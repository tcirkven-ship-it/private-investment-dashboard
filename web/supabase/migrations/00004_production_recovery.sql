-- Migration 00004: Production Recovery
-- Completes schema objects that were missing on production
-- after the partial 00003 and initial production schema.
-- Additive only. Idempotent. Safe after any prior state.
-- ============================================================

-- ============================================================
-- 1. Add is_owner column to profiles
-- ============================================================
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS is_owner BOOLEAN DEFAULT false;

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
-- 3. Profiles updated_at trigger
-- ============================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_profiles_updated_at') THEN
    CREATE TRIGGER set_profiles_updated_at
      BEFORE UPDATE ON public.profiles FOR EACH ROW
      EXECUTE FUNCTION public.update_updated_at_column();
  END IF;
END
$$;

-- ============================================================
-- 4. handle_new_user function + trigger
-- ============================================================
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
    NOT owner_exists
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'on_auth_user_created') THEN
    CREATE TRIGGER on_auth_user_created
      AFTER INSERT ON auth.users FOR EACH ROW
      EXECUTE FUNCTION public.handle_new_user();
  END IF;
END
$$;

-- ============================================================
-- 5. is_owner() helper function
-- ============================================================
CREATE OR REPLACE FUNCTION public.is_owner()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND is_owner = true);
$$;

-- ============================================================
-- 6. check_snapshot_status_transition function + trigger
-- ============================================================
CREATE OR REPLACE FUNCTION public.check_snapshot_status_transition()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF OLD.status IN ('PUBLISHED', 'SUPERSEDED') THEN
    RAISE EXCEPTION 'Published or superseded snapshots are immutable';
  END IF;
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
  IF NEW.status = 'PUBLISHED' AND OLD.status != 'PUBLISHED' THEN
    NEW.published_at = now();
  END IF;
  RETURN NEW;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'check_snapshot_status_transition') THEN
    CREATE TRIGGER check_snapshot_status_transition
      BEFORE UPDATE ON public.model_snapshots FOR EACH ROW
      EXECUTE FUNCTION public.check_snapshot_status_transition();
  END IF;
END
$$;

-- ============================================================
-- 7. prevent_portfolio_deletion function + trigger
-- ============================================================
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

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'prevent_portfolio_deletion') THEN
    CREATE TRIGGER prevent_portfolio_deletion
      BEFORE DELETE ON public.portfolios FOR EACH ROW
      EXECUTE FUNCTION public.prevent_portfolio_deletion();
  END IF;
END
$$;

-- ============================================================
-- 8. Portfolios updated_at trigger
-- ============================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_portfolios_updated_at') THEN
    CREATE TRIGGER set_portfolios_updated_at
      BEFORE UPDATE ON public.portfolios FOR EACH ROW
      EXECUTE FUNCTION public.update_updated_at_column();
  END IF;
END
$$;

-- ============================================================
-- 9. check_transaction_owner function + trigger
-- ============================================================
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

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'check_transaction_owner') THEN
    CREATE TRIGGER check_transaction_owner
      BEFORE INSERT ON public.transactions FOR EACH ROW
      EXECUTE FUNCTION public.check_transaction_owner();
  END IF;
END
$$;

-- ============================================================
-- 10. Tax check constraint
-- ============================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'transactions_tax_check') THEN
    ALTER TABLE public.transactions ADD CONSTRAINT transactions_tax_check CHECK (tax >= 0);
  END IF;
END
$$;

-- ============================================================
-- 11. model_publication_events table
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
-- 12. portfolio_valuations table
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

-- ============================================================
-- 13. Remaining indexes
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_securities_superseded_by ON public.securities(superseded_by);
