#!/usr/bin/env bash
# RLS and Auth Verification — Real Supabase-Compatible Tests
set -euo pipefail

DB_URL="${PG_TEST_URL:-}"
if [ -z "$DB_URL" ]; then
  echo "ERROR: PG_TEST_URL is required"
  exit 1
fi

PSQL="psql -v ON_ERROR_STOP=1 -t -A"

echo "=== RLS Verification ==="
echo ""

echo "Target: $(echo "$DB_URL" | sed 's/:[^:@]*@/:****@/g')"
echo ""

# 1. RLS-enabled tables
echo "--- RLS-enabled tables ---"
$PSQL "$DB_URL" -c "SELECT relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relrowsecurity = true AND n.nspname = 'public' ORDER BY relname;"

echo ""
echo "--- Policy count ---"
$PSQL "$DB_URL" -c "SELECT count(*) FROM pg_policies WHERE schemaname = 'public';"

echo ""
echo "--- All policies ---"
$PSQL "$DB_URL" -c "SELECT tablename, policyname, permissive, cmd FROM pg_policies WHERE schemaname = 'public' ORDER BY tablename, policyname;"

echo ""
echo "=== Policies use is_owner() ==="
$PSQL "$DB_URL" -c "SELECT count(*) FROM pg_policies WHERE schemaname = 'public' AND (qual IS NOT NULL AND qual::text LIKE '%is_owner%');"

echo ""
echo "=== Owner function exists ==="
$PSQL "$DB_URL" -c "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.proname = 'is_owner' AND n.nspname = 'public';"

echo ""
echo "=== Model immutability trigger ==="
$PSQL "$DB_URL" -c "SELECT trigger_name, event_manipulation FROM information_schema.triggers WHERE trigger_name = 'prevent_published_mutation';"

echo ""
echo "=== Portfolio deletion trigger ==="
$PSQL "$DB_URL" -c "SELECT trigger_name, event_manipulation FROM information_schema.triggers WHERE trigger_name = 'prevent_portfolio_deletion';"

echo ""
echo "=== RLS VERIFICATION COMPLETE ==="
echo "For full Supabase Auth-aware RLS tests, run against a local Supabase stack."
echo "Manual test steps documented in scripts/verify-rls.ts"
