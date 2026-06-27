-- Private Investment Dashboard — Corrected Release Schema
-- Single atomic migration for fresh installations.
-- Requires: Supabase project with auth.users schema.
-- Run inside a transaction block in Supabase SQL Editor.

BEGIN;

-- ============================================================
-- 1. Extensions
-- ============================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- 2. Shared trigger function
-- ============================================================
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

-- ============================================================
-- 3. Profiles (extends Supabase auth.users)
-- ============================================================
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  display_name TEXT,
  totp_enabled BOOLEAN DEFAULT false,
  is_owner BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER set_profiles_updated_at
  BEFORE UPDATE ON public.profiles FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  owner_exists BOOLEAN;
BEGIN
  SELECT EXISTS (SELECT 1 FROM public.profiles WHERE is_owner = true) INTO owner_exists;
  INSERT INTO public.profiles (id, email, display_name, is_owner)
  VALUES (
    NEW.id,
    NEW.email,
    split_part(NEW.email, '@', 1),
    NOT owner_exists  -- first user becomes owner
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- 4. App settings (owner-only)
-- ============================================================
CREATE TABLE public.app_settings (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 5. Securities reference
-- ============================================================
CREATE TABLE public.securities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL UNIQUE,
  company_name TEXT,
  sector TEXT,
  industry TEXT,
  asset_class TEXT,
  is_active BOOLEAN DEFAULT true,
  data_source TEXT DEFAULT 'yfinance',
  superseded_by UUID REFERENCES public.securities(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 6. Model versions
-- ============================================================
CREATE TABLE public.model_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_id TEXT NOT NULL,
  version TEXT NOT NULL,
  description TEXT,
  config_hash TEXT,
  formula_version TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(model_id, version)
);

-- ============================================================
-- 7. Enums
-- ============================================================
CREATE TYPE public.snapshot_status AS ENUM (
  'DRAFT', 'VALIDATED', 'APPROVED', 'PUBLISHED', 'SUPERSEDED'
);

CREATE TYPE public.rebalance_status AS ENUM (
  'PENDING', 'COMPLETED', 'CANCELLED'
);

CREATE TYPE public.transaction_types AS ENUM (
  'DEPOSIT', 'WITHDRAWAL', 'BUY', 'SELL', 'DIVIDEND',
  'FEE', 'TAX', 'INTEREST', 'SPLIT', 'SYMBOL_CHANGE',
  'MERGER', 'SPINOFF', 'CORRECTION', 'TRANSFER'
);

-- ============================================================
-- 8. Model snapshots (immutable after PUBLISHED)
-- ============================================================
CREATE TABLE public.model_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_version_id UUID NOT NULL REFERENCES public.model_versions(id),
  snapshot_id TEXT NOT NULL UNIQUE,
  status public.snapshot_status NOT NULL DEFAULT 'DRAFT',
  effective_date DATE NOT NULL,
  decision_timestamp TIMESTAMPTZ,
  execution_convention TEXT DEFAULT 'next_valid_session_close',
  universe_screened INT,
  eligible_count INT,
  valid_score_count INT,
  integrity_hash TEXT,
  source_commit TEXT,
  warnings JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  published_at TIMESTAMPTZ,
  superseded_at TIMESTAMPTZ
);

-- Enforce valid status transitions for model snapshots
CREATE OR REPLACE FUNCTION public.check_snapshot_status_transition()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  -- Published/superseded are immutable
  IF OLD.status IN ('PUBLISHED', 'SUPERSEDED') THEN
    RAISE EXCEPTION 'Published or superseded snapshots are immutable';
  END IF;

  -- Valid transitions: DRAFT->VALIDATED->APPROVED->PUBLISHED, any->SUPERSEDED
  IF NEW.status = 'VALIDATED' AND OLD.status != 'DRAFT' THEN
    RAISE EXCEPTION 'Only DRAFT can become VALIDATED';
  END IF;
  IF NEW.status = 'APPROVED' AND OLD.status != 'VALIDATED' THEN
    RAISE EXCEPTION 'Only VALIDATED can become APPROVED';
  END IF;
  IF NEW.status = 'PUBLISHED' AND OLD.status != 'APPROVED' THEN
    RAISE EXCEPTION 'Only APPROVED can become PUBLISHED';
  END IF;
  IF NEW.status = 'SUPERSEDED' AND OLD.status NOT IN ('PUBLISHED', 'APPROVED') THEN
    RAISE EXCEPTION 'Only PUBLISHED or APPROVED can become SUPERSEDED';
  END IF;

  -- Set timestamps
  IF NEW.status = 'PUBLISHED' AND OLD.status != 'PUBLISHED' THEN
    NEW.published_at = now();
  END IF;

  RETURN NEW;
END;
$$;

CREATE TRIGGER check_snapshot_status_transition
  BEFORE UPDATE ON public.model_snapshots FOR EACH ROW
  EXECUTE FUNCTION public.check_snapshot_status_transition();

-- ============================================================
-- 9. Model snapshot holdings
-- ============================================================
CREATE TABLE public.model_snapshot_holdings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_id UUID NOT NULL REFERENCES public.model_snapshots(id) ON DELETE CASCADE,
  security_id UUID NOT NULL REFERENCES public.securities(id),
  rank INT NOT NULL CHECK (rank >= 1 AND rank <= 30),
  target_weight NUMERIC(8,6) NOT NULL CHECK (target_weight > 0 AND target_weight <= 1),
  b2_score NUMERIC(8,6) CHECK (b2_score >= 0 AND b2_score <= 1),
  quality_percentile NUMERIC(8,6) CHECK (quality_percentile >= 0 AND quality_percentile <= 1),
  quality_components_ok INT DEFAULT 0 CHECK (quality_components_ok >= 0 AND quality_components_ok <= 4),
  prior_rank INT,
  change_from_prior TEXT,
  data_quality_flags TEXT[],
  inclusion_reason TEXT,
  UNIQUE(snapshot_id, rank),
  UNIQUE(snapshot_id, security_id)
);

-- ============================================================
-- 10. Model publication events
-- ============================================================
CREATE TABLE public.model_publication_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_id UUID NOT NULL REFERENCES public.model_snapshots(id),
  from_status TEXT,
  to_status TEXT NOT NULL,
  changed_by UUID REFERENCES auth.users(id),
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 11. Portfolios (archive instead of delete)
-- ============================================================
CREATE TABLE public.portfolios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL REFERENCES auth.users(id),
  name TEXT NOT NULL,
  currency TEXT DEFAULT 'USD',
  opening_date DATE NOT NULL,
  starting_cash NUMERIC(14,2),
  benchmark_ticker TEXT,
  notes TEXT,
  is_archived BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER set_portfolios_updated_at
  BEFORE UPDATE ON public.portfolios FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- Prevent deletion of portfolios with transaction history
CREATE OR REPLACE FUNCTION public.prevent_portfolio_deletion()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.transactions WHERE portfolio_id = OLD.id LIMIT 1) THEN
    RAISE EXCEPTION 'Cannot delete portfolio with transaction history. Archive it instead.';
  END IF;
  RETURN OLD;
END;
$$;

CREATE TRIGGER prevent_portfolio_deletion
  BEFORE DELETE ON public.portfolios FOR EACH ROW
  EXECUTE FUNCTION public.prevent_portfolio_deletion();

-- ============================================================
-- 12. Transactions (append-only source of truth)
-- ============================================================
CREATE TABLE public.transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES public.portfolios(id) ON DELETE RESTRICT,
  security_id UUID REFERENCES public.securities(id),
  event_type public.transaction_types NOT NULL,
  event_date DATE NOT NULL,
  quantity NUMERIC(14,6) CHECK (quantity IS NULL OR quantity >= 0),
  price NUMERIC(14,4) CHECK (price IS NULL OR price >= 0),
  gross_amount NUMERIC(14,2) NOT NULL,
  commission NUMERIC(10,2) DEFAULT 0 CHECK (commission >= 0),
  tax NUMERIC(10,2) DEFAULT 0 CHECK (tax >= 0),
  fx_rate NUMERIC(10,6),
  notes TEXT,
  idempotency_key TEXT NOT NULL UNIQUE,
  corrected_by UUID REFERENCES public.transactions(id),
  owner_id UUID NOT NULL REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT chk_buy_sell_requires_security CHECK (
    event_type NOT IN ('BUY', 'SELL', 'DIVIDEND', 'SPLIT', 'SYMBOL_CHANGE', 'MERGER', 'SPINOFF')
    OR security_id IS NOT NULL
  ),
  CONSTRAINT chk_buy_sell_quantity CHECK (
    event_type NOT IN ('BUY', 'SELL', 'SPLIT') OR (quantity IS NOT NULL AND quantity > 0)
  ),
  CONSTRAINT chk_buy_sell_price CHECK (
    event_type NOT IN ('BUY', 'SELL') OR (price IS NOT NULL AND price > 0)
  ),
  CONSTRAINT chk_deposit_withdrawal_amount CHECK (
    event_type NOT IN ('DEPOSIT', 'WITHDRAWAL') OR gross_amount > 0
  )
);

-- Enforce transaction owner matches portfolio owner
CREATE OR REPLACE FUNCTION public.check_transaction_owner()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  port_owner UUID;
BEGIN
  SELECT owner_id INTO port_owner FROM public.portfolios WHERE id = NEW.portfolio_id;
  IF port_owner IS NULL THEN
    RAISE EXCEPTION 'Portfolio not found';
  END IF;
  IF NEW.owner_id != port_owner THEN
    RAISE EXCEPTION 'Transaction owner must match portfolio owner';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER check_transaction_owner
  BEFORE INSERT ON public.transactions FOR EACH ROW
  EXECUTE FUNCTION public.check_transaction_owner();

CREATE INDEX idx_transactions_portfolio ON public.transactions(portfolio_id, event_date);
CREATE INDEX idx_transactions_owner ON public.transactions(owner_id, event_date);

-- ============================================================
-- 13. Price observations
-- ============================================================
CREATE TABLE public.price_observations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  security_id UUID NOT NULL REFERENCES public.securities(id),
  observation_date DATE NOT NULL,
  close NUMERIC(12,4),
  adj_close NUMERIC(12,4),
  volume BIGINT,
  source TEXT DEFAULT 'yfinance',
  UNIQUE(security_id, observation_date)
);

-- ============================================================
-- 14. Benchmark observations
-- ============================================================
CREATE TABLE public.benchmark_observations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL,
  observation_date DATE NOT NULL,
  price NUMERIC(12,4),
  total_return_index NUMERIC(14,6),
  UNIQUE(ticker, observation_date)
);

-- ============================================================
-- 15. Portfolio valuations (derived, not source of truth)
-- ============================================================
CREATE TABLE public.portfolio_valuations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES public.portfolios(id),
  valuation_date DATE NOT NULL,
  total_value NUMERIC(14,2) NOT NULL,
  cash_balance NUMERIC(14,2) DEFAULT 0,
  total_deposits NUMERIC(14,2) DEFAULT 0,
  total_withdrawals NUMERIC(14,2) DEFAULT 0,
  UNIQUE(portfolio_id, valuation_date)
);

-- ============================================================
-- 16. Rebalance events
-- ============================================================
CREATE TABLE public.rebalance_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES public.portfolios(id),
  model_snapshot_id UUID NOT NULL REFERENCES public.model_snapshots(id),
  rebalance_date DATE NOT NULL,
  status public.rebalance_status NOT NULL DEFAULT 'PENDING',
  estimated_cost NUMERIC(12,2),
  completed_at TIMESTAMPTZ,
  owner_id UUID NOT NULL REFERENCES auth.users(id)
);

-- ============================================================
-- 17. Rebalance lines
-- ============================================================
CREATE TABLE public.rebalance_lines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rebalance_event_id UUID NOT NULL REFERENCES public.rebalance_events(id) ON DELETE CASCADE,
  security_id UUID NOT NULL REFERENCES public.securities(id),
  current_quantity NUMERIC(14,6) DEFAULT 0,
  target_quantity NUMERIC(14,6) DEFAULT 0,
  illustrative_action TEXT,
  estimated_cost NUMERIC(10,2) DEFAULT 0,
  owner_decision TEXT,
  executed_quantity NUMERIC(14,6),
  UNIQUE(rebalance_event_id, security_id)
);

-- ============================================================
-- 18. Owner decisions
-- ============================================================
CREATE TABLE public.owner_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rebalance_line_id UUID REFERENCES public.rebalance_lines(id),
  decision_type TEXT NOT NULL,
  decision_data JSONB,
  notes TEXT,
  owner_id UUID NOT NULL REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 19. Data imports (idempotency tracking)
-- ============================================================
CREATE TABLE public.data_imports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  import_type TEXT NOT NULL,
  source TEXT,
  rows_imported INT DEFAULT 0,
  rows_rejected INT DEFAULT 0,
  errors JSONB,
  checksum TEXT NOT NULL,
  owner_id UUID NOT NULL REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(checksum)
);

-- ============================================================
-- 20. Audit events (append-only)
-- ============================================================
CREATE TABLE public.audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID REFERENCES auth.users(id),
  event_type TEXT NOT NULL,
  description TEXT,
  ip_address INET,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_model_snapshots_status ON public.model_snapshots(status);
CREATE INDEX idx_model_snapshot_holdings_snapshot ON public.model_snapshot_holdings(snapshot_id);
CREATE INDEX idx_price_observations_security ON public.price_observations(security_id, observation_date);
CREATE INDEX idx_benchmark_observations ON public.benchmark_observations(ticker, observation_date);
CREATE INDEX idx_rebalance_events_portfolio ON public.rebalance_events(portfolio_id, owner_id);
CREATE INDEX idx_portfolio_valuations_portfolio ON public.portfolio_valuations(portfolio_id, valuation_date);
CREATE INDEX idx_model_publication_events_snapshot ON public.model_publication_events(snapshot_id);
CREATE INDEX idx_securities_superseded_by ON public.securities(superseded_by);
CREATE INDEX idx_audit_events_owner ON public.audit_events(owner_id, created_at DESC);

-- ============================================================
-- Row Level Security
-- ============================================================

-- Helper: check if the current user is the application owner
CREATE OR REPLACE FUNCTION public.is_owner()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND is_owner = true);
$$;

-- Profiles: owner can read/update own; service can manage all
CREATE POLICY "Users can view own profile" ON public.profiles
  FOR SELECT USING (id = auth.uid());
CREATE POLICY "Users can update own profile" ON public.profiles
  FOR UPDATE USING (id = auth.uid());
CREATE POLICY "Service can manage profiles" ON public.profiles
  FOR ALL USING (auth.role() = 'service_role');

-- App settings: owner only
CREATE POLICY "Owner can manage app settings" ON public.app_settings
  FOR ALL USING (public.is_owner());
CREATE POLICY "Service can manage app settings" ON public.app_settings
  FOR ALL USING (auth.role() = 'service_role');

-- Securities: owner only (private reference data)
CREATE POLICY "Owner can view securities" ON public.securities
  FOR SELECT USING (public.is_owner());
CREATE POLICY "Service can manage securities" ON public.securities
  FOR ALL USING (auth.role() = 'service_role');

-- Model versions: owner only
CREATE POLICY "Owner can view model versions" ON public.model_versions
  FOR SELECT USING (public.is_owner());
CREATE POLICY "Service can manage model versions" ON public.model_versions
  FOR ALL USING (auth.role() = 'service_role');

-- Model snapshots: owner read; service manage
CREATE POLICY "Owner can view model snapshots" ON public.model_snapshots
  FOR SELECT USING (public.is_owner());
CREATE POLICY "Service can manage model snapshots" ON public.model_snapshots
  FOR ALL USING (auth.role() = 'service_role');

-- Model snapshot holdings: owner read
CREATE POLICY "Owner can view snapshot holdings" ON public.model_snapshot_holdings
  FOR SELECT USING (public.is_owner());
CREATE POLICY "Service can manage snapshot holdings" ON public.model_snapshot_holdings
  FOR ALL USING (auth.role() = 'service_role');

-- Model publication events: owner read
CREATE POLICY "Owner can view publication events" ON public.model_publication_events
  FOR SELECT USING (public.is_owner());
CREATE POLICY "Service can manage publication events" ON public.model_publication_events
  FOR ALL USING (auth.role() = 'service_role');

-- Portfolios: owner manage
CREATE POLICY "Owner can manage portfolios" ON public.portfolios
  FOR ALL USING (owner_id = auth.uid() AND public.is_owner());

-- Transactions: owner INSERT + SELECT only (append-only)
CREATE POLICY "Owner can insert transactions" ON public.transactions
  FOR INSERT WITH CHECK (owner_id = auth.uid() AND public.is_owner());
CREATE POLICY "Owner can view transactions" ON public.transactions
  FOR SELECT USING (owner_id = auth.uid() AND public.is_owner());
-- UPDATE and DELETE are intentionally NOT granted to authenticated users.
-- Corrections use CORRECTION event type with corrected_by reference.

-- Price observations: owner only
CREATE POLICY "Owner can view prices" ON public.price_observations
  FOR SELECT USING (public.is_owner());
CREATE POLICY "Service can manage prices" ON public.price_observations
  FOR ALL USING (auth.role() = 'service_role');

-- Benchmark observations: owner only
CREATE POLICY "Owner can view benchmarks" ON public.benchmark_observations
  FOR SELECT USING (public.is_owner());
CREATE POLICY "Service can manage benchmarks" ON public.benchmark_observations
  FOR ALL USING (auth.role() = 'service_role');

-- Portfolio valuations: owner read
CREATE POLICY "Owner can view valuations" ON public.portfolio_valuations
  FOR SELECT USING (
    public.is_owner() AND EXISTS (
      SELECT 1 FROM public.portfolios p WHERE p.id = portfolio_id AND p.owner_id = auth.uid()
    )
  );
CREATE POLICY "Service can manage valuations" ON public.portfolio_valuations
  FOR ALL USING (auth.role() = 'service_role');

-- Rebalance events: owner manage
CREATE POLICY "Owner can manage rebalance events" ON public.rebalance_events
  FOR ALL USING (owner_id = auth.uid() AND public.is_owner());

-- Rebalance lines: owner read (via rebalance_events join)
CREATE POLICY "Owner can view rebalance lines" ON public.rebalance_lines
  FOR SELECT USING (
    public.is_owner() AND EXISTS (
      SELECT 1 FROM public.rebalance_events re WHERE re.id = rebalance_event_id AND re.owner_id = auth.uid()
    )
  );
CREATE POLICY "Service can manage rebalance lines" ON public.rebalance_lines
  FOR ALL USING (auth.role() = 'service_role');

-- Owner decisions: owner manage
CREATE POLICY "Owner can manage decisions" ON public.owner_decisions
  FOR ALL USING (owner_id = auth.uid() AND public.is_owner());

-- Data imports: owner view+insert
CREATE POLICY "Owner can view imports" ON public.data_imports
  FOR SELECT USING (owner_id = auth.uid() AND public.is_owner());
CREATE POLICY "Owner can insert imports" ON public.data_imports
  FOR INSERT WITH CHECK (owner_id = auth.uid() AND public.is_owner());

-- Audit events: owner read only
CREATE POLICY "Owner can view audit events" ON public.audit_events
  FOR SELECT USING (owner_id = auth.uid() AND public.is_owner());

-- ============================================================
-- RLS enable on all tables (required for policies to take effect)
-- ============================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.securities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_snapshot_holdings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_publication_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.price_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.benchmark_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolio_valuations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rebalance_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rebalance_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.owner_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_imports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_events ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Grants
-- ============================================================
-- Authenticated users get SELECT on tables they're allowed to read via RLS.
-- Service role gets full access via RLS policies.
-- Anon role gets nothing.

COMMIT;
