-- Private Investment Dashboard — Complete Schema
-- Run this in Supabase SQL Editor to initialize the database.

-- 0. Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Profiles
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  display_name TEXT,
  totp_enabled BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);


-- Shared updated_at trigger function.
-- Must be defined before any trigger that references it.
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

CREATE TRIGGER set_profiles_updated_at
  BEFORE UPDATE ON profiles FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, display_name)
  VALUES (NEW.id, NEW.email, split_part(NEW.email, '@', 1));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users FOR EACH ROW
  EXECUTE FUNCTION handle_new_user();

-- 2. App settings
CREATE TABLE app_settings (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE app_settings ENABLE ROW LEVEL SECURITY;

-- 3. Securities
CREATE TABLE securities (
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

-- 4. Model versions
CREATE TABLE model_versions (
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

-- 5. Model snapshots
CREATE TYPE snapshot_status AS ENUM ('DRAFT', 'VALIDATED', 'APPROVED', 'PUBLISHED', 'SUPERSEDED');

CREATE TABLE model_snapshots (
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
  superseded_at TIMESTAMPTZ
);

ALTER TABLE model_snapshots ENABLE ROW LEVEL SECURITY;

-- 6. Model snapshot holdings
CREATE TABLE model_snapshot_holdings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_id UUID NOT NULL REFERENCES model_snapshots(id) ON DELETE CASCADE,
  security_id UUID NOT NULL REFERENCES securities(id),
  rank INT NOT NULL,
  target_weight NUMERIC(8,6) NOT NULL,
  b2_score NUMERIC(8,6),
  quality_percentile NUMERIC(8,6),
  quality_components_ok INT DEFAULT 0,
  prior_rank INT,
  change_from_prior TEXT,
  data_quality_flags TEXT[] DEFAULT '{}',
  inclusion_reason TEXT,
  UNIQUE(snapshot_id, security_id)
);

ALTER TABLE model_snapshot_holdings ENABLE ROW LEVEL SECURITY;

-- 7. Portfolios
CREATE TABLE portfolios (
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

ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

-- 8. Transactions (source of truth for holdings)
CREATE TYPE transaction_types AS ENUM (
  'BUY', 'SELL', 'DIVIDEND', 'DEPOSIT', 'WITHDRAWAL',
  'FEE', 'TAX', 'INTEREST', 'SPLIT', 'SYMBOL_CHANGE',
  'MERGER', 'SPINOFF', 'ADJUSTMENT', 'CORRECTION'
);

CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  security_id UUID REFERENCES securities(id),
  event_type transaction_types NOT NULL,
  event_date DATE NOT NULL,
  quantity NUMERIC(14,6),
  price NUMERIC(14,4),
  gross_amount NUMERIC(14,2),
  commission NUMERIC(10,2) DEFAULT 0,
  tax NUMERIC(10,2) DEFAULT 0,
  fx_rate NUMERIC(12,6) DEFAULT 1,
  notes TEXT,
  idempotency_key TEXT UNIQUE,
  corrected_by UUID REFERENCES transactions(id),
  owner_id UUID NOT NULL REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- 9. Price observations
CREATE TABLE price_observations (
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

-- 10. Benchmark observations
CREATE TABLE benchmark_observations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL,
  observation_date DATE NOT NULL,
  price NUMERIC(12,4),
  total_return_index NUMERIC(14,6),
  UNIQUE(ticker, observation_date)
);

ALTER TABLE benchmark_observations ENABLE ROW LEVEL SECURITY;

-- 11. Rebalance events
CREATE TYPE rebalance_status AS ENUM ('PENDING', 'COMPLETED', 'CANCELLED');

CREATE TABLE rebalance_events (
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

-- 12. Rebalance lines
CREATE TABLE rebalance_lines (
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

-- 13. Audit events
CREATE TABLE audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID REFERENCES auth.users(id),
  event_type TEXT NOT NULL,
  description TEXT,
  ip_address INET,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;

-- 14. Data imports
CREATE TABLE data_imports (
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

-- 15. Owner decisions
CREATE TABLE owner_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rebalance_line_id UUID REFERENCES rebalance_lines(id),
  decision_type TEXT NOT NULL,
  decision_data JSONB,
  notes TEXT,
  owner_id UUID NOT NULL REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE owner_decisions ENABLE ROW LEVEL SECURITY;

-- Indexes
CREATE INDEX idx_transactions_portfolio ON transactions(portfolio_id, event_date);
CREATE INDEX idx_transactions_owner ON transactions(owner_id);
CREATE INDEX idx_portfolios_owner ON portfolios(owner_id);
CREATE INDEX idx_model_snapshots_status ON model_snapshots(status);
CREATE INDEX idx_model_snapshot_holdings_snapshot ON model_snapshot_holdings(snapshot_id);
CREATE INDEX idx_price_observations_security ON price_observations(security_id, observation_date);
CREATE INDEX idx_benchmark_observations ON benchmark_observations(ticker, observation_date);
CREATE INDEX idx_rebalance_events_portfolio ON rebalance_events(portfolio_id);
CREATE INDEX idx_audit_events_owner ON audit_events(owner_id, created_at DESC);

-- Row Level Security Policies
-- Profiles
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (id = auth.uid());
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (id = auth.uid());

-- Portfolios
CREATE POLICY "Users can manage own portfolios" ON portfolios
  FOR ALL USING (owner_id = auth.uid());

-- Transactions
CREATE POLICY "Users can manage own transactions" ON transactions
  FOR ALL USING (owner_id = auth.uid());

-- Model snapshots (readable by authenticated, writable by service)
CREATE POLICY "Authenticated can view model snapshots" ON model_snapshots
  FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Service can manage model snapshots" ON model_snapshots
  FOR ALL USING (auth.role() = 'service_role');

-- Model snapshot holdings
CREATE POLICY "Authenticated can view holdings" ON model_snapshot_holdings
  FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Service can manage holdings" ON model_snapshot_holdings
  FOR ALL USING (auth.role() = 'service_role');

-- Securities
CREATE POLICY "Authenticated can view securities" ON securities
  FOR SELECT USING (auth.role() = 'authenticated');

-- Price observations
CREATE POLICY "Authenticated can view prices" ON price_observations
  FOR SELECT USING (auth.role() = 'authenticated');

-- Benchmark observations
CREATE POLICY "Authenticated can view benchmarks" ON benchmark_observations
  FOR SELECT USING (auth.role() = 'authenticated');

-- Rebalance events
CREATE POLICY "Users can manage own rebalance events" ON rebalance_events
  FOR ALL USING (owner_id = auth.uid());

-- Rebalance lines
CREATE POLICY "Users can view own rebalance lines" ON rebalance_lines
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM rebalance_events re WHERE re.id = rebalance_event_id AND re.owner_id = auth.uid())
  );

-- Audit events
CREATE POLICY "Users can view own audit events" ON audit_events
  FOR SELECT USING (owner_id = auth.uid());

-- App settings
CREATE POLICY "Authenticated can view app settings" ON app_settings
  FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Service can manage app settings" ON app_settings
  FOR ALL USING (auth.role() = 'service_role');

-- Data imports
CREATE POLICY "Users can view own imports" ON data_imports
  FOR SELECT USING (owner_id = auth.uid());
CREATE POLICY "Users can insert own imports" ON data_imports
  FOR INSERT WITH CHECK (owner_id = auth.uid());

-- Owner decisions
CREATE POLICY "Users can manage own decisions" ON owner_decisions
  FOR ALL USING (owner_id = auth.uid());
