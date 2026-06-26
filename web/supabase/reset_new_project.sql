-- ================================================================
-- RESET NEW PROJECT — DESTRUCTIVE
-- ================================================================
-- For brand-new Supabase development projects with NO real data.
-- WARNING: This is destructive. All application data will be lost.
--
-- Refuses if any application table contains rows.
-- Override: SET app.reset_override = true; before running.
--
-- Does NOT modify: auth, storage, extensions, realtime, supabase_functions
-- ================================================================

DO $$
DECLARE
  app_tables TEXT[] := ARRAY[
    'public.owner_decisions', 'public.rebalance_lines', 'public.rebalance_events',
    'public.portfolio_valuations', 'public.model_publication_events',
    'public.model_snapshot_holdings', 'public.model_snapshots', 'public.model_versions',
    'public.data_imports', 'public.audit_events', 'public.benchmark_observations',
    'public.price_observations', 'public.transactions', 'public.portfolios',
    'public.securities', 'public.app_settings', 'public.profiles'
  ];
  t TEXT;
  row_count INT;
  has_data BOOLEAN := false;
  override BOOLEAN;
BEGIN
  -- Check override
  BEGIN
    override := current_setting('app.reset_override', true) = 'true';
  EXCEPTION WHEN OTHERS THEN
    override := false;
  END;

  IF NOT override THEN
    -- Check if any application table has rows
    FOREACH t IN ARRAY app_tables
    LOOP
      BEGIN
        EXECUTE format('SELECT count(*) FROM %s LIMIT 1', t) INTO row_count;
        IF row_count > 0 THEN
          has_data := true;
          RAISE WARNING 'Table % has % row(s)', t, row_count;
        END IF;
      EXCEPTION WHEN undefined_table THEN
        -- Table doesn't exist yet — fine
        NULL;
      END;
    END LOOP;

    IF has_data THEN
      RAISE EXCEPTION 'Application tables contain data. Set app.reset_override = true to override.';
    END IF;
  END IF;

  -- Drop application objects
  FOREACH t IN ARRAY app_tables
  LOOP
    BEGIN
      EXECUTE format('DROP TABLE IF EXISTS %s CASCADE', t);
    EXCEPTION WHEN OTHERS THEN
      NULL;
    END;
  END LOOP;

  -- Drop custom types
  BEGIN
    DROP TYPE IF EXISTS public.snapshot_status CASCADE;
    DROP TYPE IF EXISTS public.rebalance_status CASCADE;
    DROP TYPE IF EXISTS public.transaction_event_type CASCADE;
  EXCEPTION WHEN OTHERS THEN NULL; END;

  -- Drop functions
  BEGIN
    DROP FUNCTION IF EXISTS public.update_updated_at_column() CASCADE;
    DROP FUNCTION IF EXISTS public.handle_new_user() CASCADE;
    DROP FUNCTION IF EXISTS public.prevent_published_mutation() CASCADE;
    DROP FUNCTION IF EXISTS public.prevent_portfolio_deletion() CASCADE;
    DROP FUNCTION IF EXISTS public.is_owner() CASCADE;
  EXCEPTION WHEN OTHERS THEN NULL; END;
END $$;
