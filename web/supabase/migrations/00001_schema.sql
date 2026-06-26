-- Private Investment Dashboard — Corrected Complete Schema
-- Run this in Supabase SQL Editor to initialize a fresh database.
-- All statements are idempotent where safe. No production data exists.

-- 0. Extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Shared updated_at trigger function (create before any trigger)
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

-- 2. Profiles (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  display_name TEXT,
  totp_enabled BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

DROP TRIGGER IF EXISTS set_profiles_updated_at ON profiles;
CREATE TRIGGER set_profiles_updated_at
  BEFORE UPDATE ON profiles FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Auto-create profile on user signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, email, display_name)
  VALUES (NEW.id, NEW.email, split_part(NEW.email, '@', 1))
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users FOR EACH ROW
  EXECUTE FUNCTION handle_new_user();

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- 3. App settings
CREATE TABLE IF NOT EXISTS app_settings (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE app_settings ENABLE ROW LEVEL SECURITY;

-- 4. Securities reference
CREATE TABLE IF NOT EXISTS securities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL UNIQUE,
  company_name TEXT,
  sector TEXT,
  industry TEXT,
  asset_class TEXT DEFAULT 'stock',
  is_active BOOLEAN DEFAULT true,
  data_source TEXT DEFAULT 'yfinance',
  superseded_by UUID REFERENCES securities(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE securities ENABLE ROW LEVEL SECURITY;

-- 5. Model versions
CREATE TABLE IF NOT EXISTS model_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_id TEXT NOT NULL,
  version TEXT NOT NULL,
  description TEXT,
  config_hash TEXT,
  formula_version TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(model_id, version)
);

ALTER TABLE model_versions ENABLE ROW LEVEL SECURITY;

-- 6. Enums for model snapshots and publication
DO $$ BEGIN
  CREATE TYPE snapshot_status AS ENUM ('DRAFT', 'VALIDATED', 'APPROVED', 'PUBLISHED', 'SUPERSEDED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE rebalance_status AS ENUM ('PENDING', 'COMPLETED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 7. Model snapshots
CREATE TABLE IF NOT EXISTS model_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_version_id UUID NOT NULL REFERENCES model_versions(id),
  snapshot_id TEXT NOT NULL UNIQUE,
  status snapshot_status DEFAULT 'DRAFT',
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
  superseded_at TIMESTAMPTZ,
  CONSTRAINT valid_status_transition CHECK (
    (status = 'DRAFT') OR
    (status = 'VALIDATED') OR
    (status = 'APPROVED') OR
    (status = 'PUBLISHED') OR
    (status = 'SUPERSEDED')
  )
);

ALTER TABLE model_snapshots ENABLE ROW LEVEL SECURITY;

-- 8. Model snapshot holdings
CREATE TABLE IF NOT EXISTS model_snapshot_holdings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_id UUID NOT NULL REFERENCES model_snapshots(id) ON DELETE CASCADE,
  security_id UUID NOT NULL REFERENCES securities(id),
  rank INT NOT NULL,
  target_weight NUMERIC(8,6) NOT NULL,
  b2_score NUMERIC(8,6),
  quality_percentile NUMERIC(8,6),
  quality_components_ok INT DEFAULT 0,
  prior_rank INT,
  inclusion_reason TEXT,
  UNIQUE(snapshot_id, security_id)
);

ALTER TABLE model_snapshot_holdings ENABLE ROW LEVEL SECURITY;

-- 9. Model publication events (audit trail for status transitions)
CREATE TABLE IF NOT EXISTS model_publication_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_id UUID NOT NULL REFERENCES model_snapshots(id),
  from_status TEXT,
  to_status TEXT NOT NULL,
  changed_by UUID REFERENCES auth.users(id),
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE model_publication_events ENABLE ROW LEVEL SECURITY;

-- 10. Portfolios
CREATE TABLE IF NOT EXISTS portfolios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL REFERENCES auth.users(id),
  name TEXT NOT NULL,
  currency TEXT DEFAULT 'USD',
  opening_date DATE NOT NULL,
  starting_cash NUMERIC(14,2) DEFAULT 0,
  benchmark_ticker TEXT DEFAULT 'SPY',
  notes TEXT,
  is_archived BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

DROP TRIGGER IF EXISTS set_portfolios_updated_at ON portfolios;
CREATE TRIGGER set_portfolios_updated_at
  BEFORE UPDATE ON portfolios FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

-- 11. Transaction event types (single authoritative enum)
DO $$ BEGIN
  CREATE TYPE transaction_event_type AS ENUM (
    'DEPOSIT', 'WITHDRAWAL', 'BUY', 'SELL', 'DIVIDEND',
    'FEE', 'TAX', 'INTEREST', 'SPLIT', 'SYMBOL_CHANGE',
    'MERGER', 'SPINOFF', 'CORRECTION', 'TRANSFER'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 12. Transactions (immutable source of truth for holdings and cash)
CREATE TABLE IF NOT EXISTS transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  security_id UUID REFERENCES securities(id),
  event_type transaction_event_type NOT NULL,
  event_date DATE NOT NULL,
  quantity NUMERIC(14,6),
  price NUMERIC(14,4),
  gross_amount NUMERIC(14,2),
  commission NUMERIC(10,2) DEFAULT 0,
  tax_amount NUMERIC(10,2) DEFAULT 0,
  notes TEXT,
  idempotency_key TEXT UNIQUE,
  corrected_by UUID REFERENCES transactions(id),
  owner_id UUID NOT NULL REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Alternative: holdings and cash are DERIVED from transactions (not stored directly).

-- 13. Price observations (timestamped, sourced)
CREATE TABLE IF NOT EXISTS price_observations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  security_id UUID NOT NULL REFERENCES securities(id),
  observation_date DATE NOT NULL,
  close NUMERIC(12,4),
  adj_close NUMERIC(12,4),
  volume BIGINT,
  source TEXT DEFAULT 'yfinance',
  UNIQUE(security_id, observation_date)
);

ALTER TABLE price_observations ENABLE ROW LEVEL SECURITY;

-- 14. Benchmark observations
CREATE TABLE IF NOT EXISTS benchmark_observations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL,
  observation_date DATE NOT NULL,
  price NUMERIC(12,4),
  total_return_index NUMERIC(14,6),
  UNIQUE(ticker, observation_date)
);

ALTER TABLE benchmark_observations ENABLE ROW LEVEL SECURITY;

-- 15. Portfolio valuations (derived, reproducible)
CREATE TABLE IF NOT EXISTS portfolio_valuations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES portfolios(id),
  valuation_date DATE NOT NULL,
  total_value NUMERIC(14,2) NOT NULL,
  cash_balance NUMERIC(14,2) DEFAULT 0,
  total_deposits NUMERIC(14,2) DEFAULT 0,
  total_withdrawals NUMERIC(14,2) DEFAULT 0,
  UNIQUE(portfolio_id, valuation_date)
);

ALTER TABLE portfolio_valuations ENABLE ROW LEVEL SECURITY;

-- 16. Rebalance events
CREATE TABLE IF NOT EXISTS rebalance_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES portfolios(id),
  model_snapshot_id UUID NOT NULL REFERENCES model_snapshots(id),
  rebalance_date DATE NOT NULL,
  status rebalance_status DEFAULT 'PENDING',
  estimated_cost NUMERIC(12,2),
  completed_at TIMESTAMPTZ,
  owner_id UUID NOT NULL REFERENCES auth.users(id)
);

ALTER TABLE rebalance_events ENABLE ROW LEVEL SECURITY;

-- 17. Rebalance lines
CREATE TABLE IF NOT EXISTS rebalance_lines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rebalance_event_id UUID NOT NULL REFERENCES rebalance_events(id) ON DELETE CASCADE,
  security_id UUID NOT NULL REFERENCES securities(id),
  current_quantity NUMERIC(14,6) DEFAULT 0,
  target_quantity NUMERIC(14,6) DEFAULT 0,
  illustrative_action TEXT,
  estimated_cost NUMERIC(10,2) DEFAULT 0,
  owner_decision TEXT,
  executed_quantity NUMERIC(14,6),
  UNIQUE(rebalance_event_id, security_id)
);

ALTER TABLE rebalance_lines ENABLE ROW LEVEL SECURITY;

-- 18. Owner decisions (for quarterly review approval)
CREATE TABLE IF NOT EXISTS owner_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rebalance_line_id UUID REFERENCES rebalance_lines(id),
  decision_type TEXT NOT NULL,
  decision_data JSONB,
  notes TEXT,
  owner_id UUID NOT NULL REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE owner_decisions ENABLE ROW LEVEL SECURITY;

-- 19. Data imports (idempotency tracking)
CREATE TABLE IF NOT EXISTS data_imports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  import_type TEXT NOT NULL,
  source TEXT,
  rows_imported INT DEFAULT 0,
  rows_rejected INT DEFAULT 0,
  errors JSONB,
  checksum TEXT,
  owner_id UUID NOT NULL REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE data_imports ENABLE ROW LEVEL SECURITY;

-- 20. Audit events (append-only, immutable record)
CREATE TABLE IF NOT EXISTS audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID REFERENCES auth.users(id),
  event_type TEXT NOT NULL,
  description TEXT,
  ip_address INET,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_transactions_portfolio ON transactions(portfolio_id, event_date);
CREATE INDEX IF NOT EXISTS idx_transactions_owner ON transactions(owner_id, event_date);
CREATE INDEX IF NOT EXISTS idx_portfolios_owner ON portfolios(owner_id);
CREATE INDEX IF NOT EXISTS idx_model_snapshots_status ON model_snapshots(status);
CREATE INDEX IF NOT EXISTS idx_model_snapshot_holdings_snapshot ON model_snapshot_holdings(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_price_observations_security ON price_observations(security_id, observation_date);
CREATE INDEX IF NOT EXISTS idx_benchmark_observations ON benchmark_observations(ticker, observation_date);
CREATE INDEX IF NOT EXISTS idx_rebalance_events_portfolio ON rebalance_events(portfolio_id, owner_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_owner ON audit_events(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_valuations_portfolio ON portfolio_valuations(portfolio_id, valuation_date);
CREATE INDEX IF NOT EXISTS idx_model_publication_events_snapshot ON model_publication_events(snapshot_id);

-- Row Level Security Policies

-- Profiles
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (id = auth.uid());
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (id = auth.uid());

-- App settings
DROP POLICY IF EXISTS "Authenticated can view app settings" ON app_settings;
CREATE POLICY "Authenticated can view app settings" ON app_settings
  FOR SELECT USING (auth.role() = 'authenticated');
DROP POLICY IF EXISTS "Service can manage app settings" ON app_settings;
CREATE POLICY "Service can manage app settings" ON app_settings
  FOR ALL USING (auth.role() = 'service_role');

-- Securities
DROP POLICY IF EXISTS "Authenticated can view securities" ON securities;
CREATE POLICY "Authenticated can view securities" ON securities
  FOR SELECT USING (auth.role() = 'authenticated');

-- Model versions
DROP POLICY IF EXISTS "Service can manage model versions" ON model_versions;
CREATE POLICY "Authenticated can view model versions" ON model_versions
  FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Service can manage model versions" ON model_versions
  FOR ALL USING (auth.role() = 'service_role');

-- Model snapshots
DROP POLICY IF EXISTS "Authenticated can view model snapshots" ON model_snapshots;
CREATE POLICY "Authenticated can view model snapshots" ON model_snapshots
  FOR SELECT USING (auth.role() = 'authenticated');
DROP POLICY IF EXISTS "Service can manage model snapshots" ON model_snapshots;
CREATE POLICY "Service can manage model snapshots" ON model_snapshots
  FOR ALL USING (auth.role() = 'service_role');

-- Model snapshot holdings
DROP POLICY IF EXISTS "Authenticated can view snapshot holdings" ON model_snapshot_holdings;
CREATE POLICY "Authenticated can view snapshot holdings" ON model_snapshot_holdings
  FOR SELECT USING (auth.role() = 'authenticated');
DROP POLICY IF EXISTS "Service can manage snapshot holdings" ON model_snapshot_holdings;
CREATE POLICY "Service can manage snapshot holdings" ON model_snapshot_holdings
  FOR ALL USING (auth.role() = 'service_role');

-- Model publication events
DROP POLICY IF EXISTS "Authenticated can view publication events" ON model_publication_events;
CREATE POLICY "Authenticated can view publication events" ON model_publication_events
  FOR SELECT USING (auth.role() = 'authenticated');
DROP POLICY IF EXISTS "Service can manage publication events" ON model_publication_events;
CREATE POLICY "Service can manage publication events" ON model_publication_events
  FOR ALL USING (auth.role() = 'service_role');

-- Portfolios
DROP POLICY IF EXISTS "Users can manage own portfolios" ON portfolios;
CREATE POLICY "Users can manage own portfolios" ON portfolios
  FOR ALL USING (owner_id = auth.uid());

-- Transactions
DROP POLICY IF EXISTS "Users can manage own transactions" ON transactions;
CREATE POLICY "Users can manage own transactions" ON transactions
  FOR ALL USING (owner_id = auth.uid());

-- Price observations
DROP POLICY IF EXISTS "Authenticated can view prices" ON price_observations;
CREATE POLICY "Authenticated can view prices" ON price_observations
  FOR SELECT USING (auth.role() = 'authenticated');

-- Benchmark observations
DROP POLICY IF EXISTS "Authenticated can view benchmarks" ON benchmark_observations;
CREATE POLICY "Authenticated can view benchmarks" ON benchmark_observations
  FOR SELECT USING (auth.role() = 'authenticated');

-- Portfolio valuations
DROP POLICY IF EXISTS "Users can view own valuations" ON portfolio_valuations;
CREATE POLICY "Users can view own valuations" ON portfolio_valuations
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM portfolios p WHERE p.id = portfolio_id AND p.owner_id = auth.uid())
  );

-- Rebalance events
DROP POLICY IF EXISTS "Users can manage own rebalance events" ON rebalance_events;
CREATE POLICY "Users can manage own rebalance events" ON rebalance_events
  FOR ALL USING (owner_id = auth.uid());

-- Rebalance lines
DROP POLICY IF EXISTS "Users can view own rebalance lines" ON rebalance_lines;
CREATE POLICY "Users can view own rebalance lines" ON rebalance_lines
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM rebalance_events re WHERE re.id = rebalance_event_id AND re.owner_id = auth.uid())
  );

-- Owner decisions
DROP POLICY IF EXISTS "Users can manage own decisions" ON owner_decisions;
CREATE POLICY "Users can manage own decisions" ON owner_decisions
  FOR ALL USING (owner_id = auth.uid());

-- Data imports
DROP POLICY IF EXISTS "Users can view own imports" ON data_imports;
CREATE POLICY "Users can view own imports" ON data_imports
  FOR SELECT USING (owner_id = auth.uid());
DROP POLICY IF EXISTS "Users can insert own imports" ON data_imports;
CREATE POLICY "Users can insert own imports" ON data_imports
  FOR INSERT WITH CHECK (owner_id = auth.uid());

-- Audit events
DROP POLICY IF EXISTS "Users can view own audit events" ON audit_events;
CREATE POLICY "Users can view own audit events" ON audit_events
  FOR SELECT USING (owner_id = auth.uid());
