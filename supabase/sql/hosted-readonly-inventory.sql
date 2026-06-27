-- ============================================================
-- Hosted Supabase Read-Only Inventory
-- ============================================================
-- Purpose: Inspect schema metadata of a hosted Supabase project.
-- Read-only — no INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
-- Does NOT query user financial data (transactions, holdings,
-- portfolios, or user rows).
-- ============================================================

-- 1. Schemas present
SELECT schema_name
FROM information_schema.schemata
ORDER BY schema_name;

-- 2. Public tables
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- 3. Public columns (name, type, nullable, default)
SELECT
  table_name,
  column_name,
  data_type,
  udt_name,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- 4. Enums
SELECT
  t.typname AS enum_name,
  e.enumlabel AS enum_value
FROM pg_type t
JOIN pg_enum e ON t.oid = e.enumtypid
WHERE t.typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
ORDER BY t.typname, e.enumsortorder;

-- 5. Functions (name, language, volatility, definition truncated)
SELECT
  p.proname AS function_name,
  l.lanname AS language,
  CASE
    WHEN p.provolatile = 'i' THEN 'IMMUTABLE'
    WHEN p.provolatile = 's' THEN 'STABLE'
    WHEN p.provolatile = 'v' THEN 'VOLATILE'
    ELSE 'UNKNOWN'
  END AS volatility,
  pg_get_functiondef(p.oid) AS definition
FROM pg_proc p
JOIN pg_language l ON p.prolang = l.oid
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
ORDER BY p.proname;

-- 6. Triggers
SELECT
  trigger_name,
  event_manipulation,
  event_object_table,
  action_timing,
  action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY trigger_name;

-- 7. Tables with RLS enabled
SELECT
  relname AS table_name,
  relrowsecurity AS rls_enabled
FROM pg_class
WHERE relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
  AND relkind = 'r'
  AND relrowsecurity = true
ORDER BY relname;

-- 8. Policies
SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- 9. Indexes (name, columns, unique, primary)
SELECT
  tablename,
  indexname,
  indexdef,
  indisunique,
  indisprimary
FROM pg_indexes i
JOIN pg_index idx ON idx.indexrelid = (SELECT c.oid FROM pg_class c WHERE c.relname = i.indexname)
WHERE i.schemaname = 'public'
ORDER BY tablename, indexname;

-- 10. Migration history (if supabase_migrations schema exists)
SELECT
  version,
  name,
  applied_at,
  checksum
FROM supabase_migrations.schema_migrations
ORDER BY version;

-- 11. Object counts summary
SELECT 'tables' AS object_type, COUNT(*)::int AS count FROM information_schema.tables WHERE table_schema = 'public'
UNION ALL
SELECT 'columns', COUNT(*)::int FROM information_schema.columns WHERE table_schema = 'public'
UNION ALL
SELECT 'enums', COUNT(*)::int FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid WHERE t.typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
UNION ALL
SELECT 'functions', COUNT(*)::int FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid WHERE n.nspname = 'public'
UNION ALL
SELECT 'triggers', COUNT(*)::int FROM information_schema.triggers WHERE trigger_schema = 'public'
UNION ALL
SELECT 'tables_with_rls', COUNT(*)::int FROM pg_class WHERE relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public') AND relkind = 'r' AND relrowsecurity = true
UNION ALL
SELECT 'policies', COUNT(*)::int FROM pg_policies WHERE schemaname = 'public'
UNION ALL
SELECT 'indexes', COUNT(*)::int FROM pg_indexes WHERE schemaname = 'public'
ORDER BY object_type;
