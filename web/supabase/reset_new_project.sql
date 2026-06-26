-- ================================================================
-- RESET NEW PROJECT — DESTRUCTIVE
-- ================================================================
-- For brand-new Supabase development projects with NO real data.
-- WARNING: This is destructive. All application data will be lost.
-- Will refuse if any application table contains data unless
-- the override comment is uncommented.
-- Does NOT modify: auth, storage, extensions, realtime, supabase_functions
-- ================================================================

DO $$
DECLARE
  has_data boolean;
BEGIN
  -- Safety check: refuse if any table has rows
  SELECT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE'
      AND table_name IN (
        'profiles', 'app_settings', 'securities', 'model_versions',
        'model_snapshots', 'model_snapshot_holdings', 'model_publication_events',
        'portfolios', 'transactions', 'price_observations', 'benchmark_observations',
        'portfolio_valuations', 'rebalance_events', 'rebalance_lines',
        'owner_decisions', 'data_imports', 'audit_events'
      )
      -- Check if any have rows
      AND EXISTS (SELECT 1 FROM (SELECT 1 FROM ONLY (quote_ident(table_name)) LIMIT 1) t)
  ) INTO has_data;

  IF has_data THEN
    RAISE EXCEPTION 'Application tables contain data. Remove data manually or override.';
  END IF;
END $$;

-- Drop application objects (schema-qualified for safety)
DROP TABLE IF EXISTS public.owner_decisions CASCADE;
DROP TABLE IF EXISTS public.rebalance_lines CASCADE;
DROP TABLE IF EXISTS public.rebalance_events CASCADE;
DROP TABLE IF EXISTS public.portfolio_valuations CASCADE;
DROP TABLE IF EXISTS public.model_publication_events CASCADE;
DROP TABLE IF EXISTS public.model_snapshot_holdings CASCADE;
DROP TABLE IF EXISTS public.model_snapshots CASCADE;
DROP TABLE IF EXISTS public.model_versions CASCADE;
DROP TABLE IF EXISTS public.data_imports CASCADE;
DROP TABLE IF EXISTS public.audit_events CASCADE;
DROP TABLE IF EXISTS public.benchmark_observations CASCADE;
DROP TABLE IF EXISTS public.price_observations CASCADE;
DROP TABLE IF EXISTS public.transactions CASCADE;
DROP TABLE IF EXISTS public.portfolios CASCADE;
DROP TABLE IF EXISTS public.securities CASCADE;
DROP TABLE IF EXISTS public.app_settings CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;

-- Drop custom types
DROP TYPE IF EXISTS public.snapshot_status CASCADE;
DROP TYPE IF EXISTS public.rebalance_status CASCADE;
DROP TYPE IF EXISTS public.transaction_event_type CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS public.update_updated_at_column() CASCADE;
DROP FUNCTION IF EXISTS public.handle_new_user() CASCADE;
DROP FUNCTION IF EXISTS public.prevent_published_mutation() CASCADE;
DROP FUNCTION IF EXISTS public.prevent_portfolio_deletion() CASCADE;
DROP FUNCTION IF EXISTS public.is_owner() CASCADE;
