-- ================================================================
-- RESET NEW PROJECT — DESTRUCTIVE
-- ================================================================
-- This script removes ALL application objects from a fresh Supabase
-- development project that contains NO real data.
--
-- WARNING: This will permanently delete all application tables,
-- types, functions, and their data.
--
-- It does NOT touch Supabase-managed schemas:
--   auth, storage, extensions, realtime, supabase_functions
-- It does NOT remove PostgreSQL extensions.
-- ================================================================

DO $$
DECLARE
  rec RECORD;
BEGIN
  -- Drop application policies (safe, no dependencies)
  FOR rec IN
    SELECT schemaname, tablename, policyname
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename IN (
        'profiles', 'app_settings', 'securities', 'model_versions',
        'model_snapshots', 'model_snapshot_holdings', 'model_publication_events',
        'portfolios', 'transactions', 'price_observations', 'benchmark_observations',
        'portfolio_valuations', 'rebalance_events', 'rebalance_lines',
        'owner_decisions', 'data_imports', 'audit_events'
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I', rec.policyname, rec.schemaname, rec.tablename);
  END LOOP;

  -- Drop triggers
  DROP TRIGGER IF EXISTS set_profiles_updated_at ON profiles;
  DROP TRIGGER IF EXISTS set_portfolios_updated_at ON portfolios;
  DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

  -- Drop functions
  DROP FUNCTION IF EXISTS update_updated_at_column();
  DROP FUNCTION IF EXISTS handle_new_user();

  -- Drop tables (CASCADE handles dependent objects)
  DROP TABLE IF EXISTS owner_decisions CASCADE;
  DROP TABLE IF EXISTS rebalance_lines CASCADE;
  DROP TABLE IF EXISTS rebalance_events CASCADE;
  DROP TABLE IF EXISTS portfolio_valuations CASCADE;
  DROP TABLE IF EXISTS model_publication_events CASCADE;
  DROP TABLE IF EXISTS model_snapshot_holdings CASCADE;
  DROP TABLE IF EXISTS model_snapshots CASCADE;
  DROP TABLE IF EXISTS model_versions CASCADE;
  DROP TABLE IF EXISTS data_imports CASCADE;
  DROP TABLE IF EXISTS audit_events CASCADE;
  DROP TABLE IF EXISTS benchmark_observations CASCADE;
  DROP TABLE IF EXISTS price_observations CASCADE;
  DROP TABLE IF EXISTS transactions CASCADE;
  DROP TABLE IF EXISTS portfolios CASCADE;
  DROP TABLE IF EXISTS securities CASCADE;
  DROP TABLE IF EXISTS app_settings CASCADE;
  DROP TABLE IF EXISTS profiles CASCADE;

  -- Drop custom enum types
  DROP TYPE IF EXISTS snapshot_status CASCADE;
  DROP TYPE IF EXISTS rebalance_status CASCADE;
  DROP TYPE IF EXISTS transaction_event_type CASCADE;

  RAISE NOTICE 'Application schema removed successfully.';
END $$;
