-- Migration 00003: Schema Reconciliation
-- Adopts hosted Supabase naming and extra columns.
-- Idempotent and safe for hosted production.
-- Manual review required before execution against hosted.
-- ============================================================

-- ============================================================
-- 1. Enum reconciliation
-- ============================================================
-- Hosted already has `transaction_types`. If migrating from a
-- local install that still has `transaction_event_type`, rename
-- it. On hosted this is a no-op.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_event_type' AND typnamespace = 'public'::regnamespace) THEN
    ALTER TYPE public.transaction_event_type RENAME TO transaction_types;
  END IF;
END
$$;

-- ============================================================
-- 2. Add `tax` column to transactions
-- ============================================================
-- Hosted has `tax` (numeric). Local migration lacked a tax column.
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS tax NUMERIC(10,2) DEFAULT 0;

-- ============================================================
-- 3. Extra hosted columns on securities
-- ============================================================
ALTER TABLE public.securities ADD COLUMN IF NOT EXISTS asset_class TEXT;
ALTER TABLE public.securities ADD COLUMN IF NOT EXISTS superseded_by UUID REFERENCES public.securities(id);
CREATE INDEX IF NOT EXISTS idx_securities_superseded_by ON public.securities(superseded_by);

-- ============================================================
-- 4. Extra hosted columns on model_snapshot_holdings
-- ============================================================
ALTER TABLE public.model_snapshot_holdings ADD COLUMN IF NOT EXISTS prior_rank INT;
ALTER TABLE public.model_snapshot_holdings ADD COLUMN IF NOT EXISTS change_from_prior TEXT;
ALTER TABLE public.model_snapshot_holdings ADD COLUMN IF NOT EXISTS data_quality_flags TEXT[];

-- ============================================================
-- 5. Extra hosted columns on portfolios
-- ============================================================
ALTER TABLE public.portfolios ADD COLUMN IF NOT EXISTS starting_cash NUMERIC(14,2);
ALTER TABLE public.portfolios ADD COLUMN IF NOT EXISTS benchmark_ticker TEXT;

-- ============================================================
-- 6. Extra hosted columns on transactions
-- ============================================================
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS fx_rate NUMERIC(10,6);
-- Add check constraint for tax if not already present
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'transactions_tax_check') THEN
    ALTER TABLE public.transactions ADD CONSTRAINT transactions_tax_check CHECK (tax >= 0);
  END IF;
END
$$;

-- ============================================================
-- 7. Local-only tables: model_publication_events
-- ============================================================
CREATE TABLE IF NOT EXISTS public.model_publication_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_id UUID NOT NULL REFERENCES public.model_snapshots(id),
  from_status TEXT,
  to_status TEXT NOT NULL,
  changed_by UUID REFERENCES auth.users(id),
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.model_publication_events ENABLE ROW LEVEL SECURITY;

-- Policies for model_publication_events
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Owner can view publication events') THEN
    CREATE POLICY "Owner can view publication events" ON public.model_publication_events
      FOR SELECT USING (public.is_owner());
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Service can manage publication events') THEN
    CREATE POLICY "Service can manage publication events" ON public.model_publication_events
      FOR ALL USING (auth.role() = 'service_role');
  END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_model_publication_events_snapshot ON public.model_publication_events(snapshot_id);

-- ============================================================
-- 8. Local-only tables: portfolio_valuations
-- ============================================================
CREATE TABLE IF NOT EXISTS public.portfolio_valuations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES public.portfolios(id),
  valuation_date DATE NOT NULL,
  total_value NUMERIC(14,2) NOT NULL,
  cash_balance NUMERIC(14,2) DEFAULT 0,
  total_deposits NUMERIC(14,2) DEFAULT 0,
  total_withdrawals NUMERIC(14,2) DEFAULT 0,
  UNIQUE(portfolio_id, valuation_date)
);

ALTER TABLE public.portfolio_valuations ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Owner can view valuations') THEN
    CREATE POLICY "Owner can view valuations" ON public.portfolio_valuations
      FOR SELECT USING (
        public.is_owner() AND EXISTS (
          SELECT 1 FROM public.portfolios p WHERE p.id = portfolio_id AND p.owner_id = auth.uid()
        )
      );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Service can manage valuations') THEN
    CREATE POLICY "Service can manage valuations" ON public.portfolio_valuations
      FOR ALL USING (auth.role() = 'service_role');
  END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_portfolio_valuations_portfolio ON public.portfolio_valuations(portfolio_id, valuation_date);
