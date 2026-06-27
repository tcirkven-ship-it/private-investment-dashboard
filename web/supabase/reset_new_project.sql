-- ================================================================
-- RESET NEW PROJECT — DESTRUCTIVE
-- ================================================================
-- For brand-new Supabase development projects with NO real data.
-- WARNING: This is destructive. All application data will be lost.
--
-- Refuses if any application table contains rows and no override is set.
-- Override: SET app.reset_override = true; before running.
--
-- Does NOT modify: auth, storage, extensions, realtime, supabase_functions
-- ================================================================

DO $$
DECLARE
  tbl text;
  row_count bigint;
  has_data boolean := false;
  override_enabled boolean;
BEGIN
  -- Check override setting
  BEGIN
    override_enabled := COALESCE(
      current_setting('app.reset_override', true)::boolean,
      false
    );
  EXCEPTION WHEN OTHERS THEN
    override_enabled := false;
  END;

  IF NOT override_enabled THEN
    -- Check every application table for data
    FOR tbl IN
      SELECT unnest(ARRAY[
        'profiles',
        'app_settings',
        'securities',
        'model_versions',
        'model_snapshots',
        'model_snapshot_holdings',
        'model_publication_events',
        'portfolios',
        'transactions',
        'price_observations',
        'benchmark_observations',
        'portfolio_valuations',
        'rebalance_events',
        'rebalance_lines',
        'owner_decisions',
        'data_imports',
        'audit_events'
      ])
    LOOP
      IF to_regclass(format('public.%I', tbl)) IS NOT NULL THEN
        EXECUTE format('SELECT count(*) FROM public.%I', tbl) INTO row_count;

        IF row_count > 0 THEN
          has_data := true;
          RAISE NOTICE 'Application table public.% contains % row(s)', tbl, row_count;
        END IF;
      END IF;
    END LOOP;

    IF has_data THEN
      RAISE EXCEPTION 'Refusing reset: application data exists. Set app.reset_override=true only for disposable test databases.';
    END IF;
  END IF;

  -- Drop application tables (in dependency-safe order)
  FOREACH tbl IN ARRAY ARRAY[
    'owner_decisions', 'rebalance_lines', 'rebalance_events',
    'portfolio_valuations', 'model_publication_events',
    'model_snapshot_holdings', 'model_snapshots', 'model_versions',
    'data_imports', 'audit_events', 'benchmark_observations',
    'price_observations', 'transactions', 'portfolios',
    'securities', 'app_settings', 'profiles'
  ]
  LOOP
    IF to_regclass(format('public.%I', tbl)) IS NOT NULL THEN
      EXECUTE format('DROP TABLE IF EXISTS public.%I CASCADE', tbl);
    END IF;
  END LOOP;

  -- Drop custom types
  IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'snapshot_status' AND typnamespace = 'public'::regnamespace) THEN
    DROP TYPE public.snapshot_status CASCADE;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rebalance_status' AND typnamespace = 'public'::regnamespace) THEN
    DROP TYPE public.rebalance_status CASCADE;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_event_type' AND typnamespace = 'public'::regnamespace) THEN
    DROP TYPE public.transaction_event_type CASCADE;
  END IF;

  -- Drop functions
  FOR tbl IN SELECT proname FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = 'public' AND p.prokind = 'f' AND p.proname IN ('update_updated_at_column','handle_new_user','prevent_published_mutation','check_snapshot_status_transition','prevent_portfolio_deletion','check_transaction_owner','is_owner')
  LOOP
    EXECUTE format('DROP FUNCTION IF EXISTS public.%I() CASCADE', tbl);
  END LOOP;
END $$;
