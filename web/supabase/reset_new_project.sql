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

\set ON_ERROR_STOP on

-- ================================================================
-- SAFETY CHECK — must fail before any destructive operation
-- This block has NO exception handler. Any RAISE EXCEPTION here
-- will cause psql to exit with a nonzero code.
-- ================================================================
DO $safety$
DECLARE
  tbl text;
  has_rows boolean;
  override_enabled boolean;
BEGIN
  override_enabled :=
    lower(coalesce(current_setting('app.reset_override', true), 'false'))
    IN ('true', 'on', '1', 'yes');

  RAISE NOTICE 'reset override enabled: %', override_enabled;

  IF NOT override_enabled THEN
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
        EXECUTE format(
          'SELECT EXISTS (SELECT 1 FROM public.%I LIMIT 1)',
          tbl
        )
        INTO has_rows;

        RAISE NOTICE 'table public.% has_rows=%', tbl, has_rows;

        IF has_rows THEN
          RAISE EXCEPTION
            'Refusing reset: application data exists in public.%. '
            'Set app.reset_override=true only for disposable test databases.',
            tbl;
        END IF;
      END IF;
    END LOOP;
  END IF;
END
$safety$;

-- ================================================================
-- DESTRUCTIVE DROP LOGIC
-- Runs only if the safety check passed or override was enabled.
-- ================================================================

DO $destroy$
DECLARE
  tbl text;
BEGIN
  -- Drop application tables
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
  IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_types' AND typnamespace = 'public'::regnamespace) THEN
    DROP TYPE public.transaction_types CASCADE;
  END IF;

  -- Drop functions
  FOR tbl IN SELECT proname FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = 'public' AND p.prokind = 'f' AND p.proname IN ('update_updated_at_column','handle_new_user','prevent_published_mutation','check_snapshot_status_transition','prevent_portfolio_deletion','check_transaction_owner','is_owner')
  LOOP
    EXECUTE format('DROP FUNCTION IF EXISTS public.%I() CASCADE', tbl);
  END LOOP;
END
$destroy$;
