-- Fix schema: add missing tables and correct types

-- Fix transaction_types enum to handle uppercase consistently
DO $$ BEGIN
  CREATE TYPE transaction_type AS ENUM (
    'BUY', 'SELL', 'DIVIDEND', 'DEPOSIT', 'WITHDRAWAL',
    'FEE', 'TAX', 'INTEREST', 'SPLIT', 'SYMBOL_CHANGE',
    'MERGER', 'SPINOFF', 'ADJUSTMENT', 'CORRECTION', 'TRANSFER'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Add model_publication_events for workflow audit trail
CREATE TABLE IF NOT EXISTS model_publication_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_id UUID NOT NULL REFERENCES model_snapshots(id),
  from_status TEXT,
  to_status TEXT NOT NULL,
  changed_by UUID REFERENCES auth.users(id),
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Add portfolio_valuations for daily NAV history
CREATE TABLE IF NOT EXISTS portfolio_valuations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES portfolios(id),
  valuation_date DATE NOT NULL,
  total_value NUMERIC(14,2) NOT NULL,
  cash_balance NUMERIC(14,2) DEFAULT 0,
  deposits NUMERIC(14,2) DEFAULT 0,
  withdrawals NUMERIC(14,2) DEFAULT 0,
  is_corrected BOOLEAN DEFAULT false,
  correction_reason TEXT,
  UNIQUE(portfolio_id, valuation_date)
);

-- Add holding_snapshots for point-in-time positions
CREATE TABLE IF NOT EXISTS holding_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES portfolios(id),
  valuation_date DATE NOT NULL,
  security_id UUID REFERENCES securities(id),
  quantity NUMERIC(14,6) NOT NULL,
  cost_basis NUMERIC(14,2) NOT NULL,
  market_value NUMERIC(14,2) NOT NULL,
  UNIQUE(portfolio_id, valuation_date, security_id)
);

-- RLS
ALTER TABLE model_publication_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_valuations ENABLE ROW LEVEL SECURITY;
ALTER TABLE holding_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated can view publication events" ON model_publication_events
  FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Service can manage publication events" ON model_publication_events
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Users can view own valuations" ON portfolio_valuations
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM portfolios p WHERE p.id = portfolio_id AND p.owner_id = auth.uid())
  );
CREATE POLICY "Service can manage valuations" ON portfolio_valuations
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Users can view own holding snapshots" ON holding_snapshots
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM portfolios p WHERE p.id = portfolio_id AND p.owner_id = auth.uid())
  );
CREATE POLICY "Service can manage holding snapshots" ON holding_snapshots
  FOR ALL USING (auth.role() = 'service_role');

-- Indexes
CREATE INDEX IF NOT EXISTS idx_holding_snapshots_portfolio_date ON holding_snapshots(portfolio_id, valuation_date);
CREATE INDEX IF NOT EXISTS idx_portfolio_valuations_portfolio_date ON portfolio_valuations(portfolio_id, valuation_date);
CREATE INDEX IF NOT EXISTS idx_model_publication_events_snapshot ON model_publication_events(snapshot_id);
