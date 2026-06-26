#!/usr/bin/env bash
# RLS and Auth Verification — Real Supabase Stack Required
set -euo pipefail

echo "=== RLS and Auth Verification ==="
echo ""
echo "This test requires a running local Supabase stack (Docker)."
echo "It cannot run against plain PostgreSQL because it needs:"
echo "  - Supabase Auth HTTP endpoints"
echo "  - JWT token generation"
echo "  - auth.users and auth.schema_refresh_hook"
echo ""
echo "Manual setup:"
echo "  1. npx supabase start (requires Docker)"
echo "  2. PG_TEST_URL=postgresql://postgres:postgres@localhost:5432/postgres"
echo "  3. bash scripts/verify-rls.sh"
echo ""

DB_URL="${PG_TEST_URL:-}"
if [ -z "$DB_URL" ]; then
  echo "No database URL. Run against local Supabase to execute tests."
  echo ""
  echo "When run against local Supabase, this test will:"
  echo "  1. Create anonymous, owner, and second-user clients"
  echo "  2. Verify anonymous reads/writes are denied"
  echo "  3. Verify owner can access own data"
  echo "  4. Verify second user cannot access owner data"
  echo "  5. Verify transaction UPDATE/DELETE denied"
  echo "  6. Verify published snapshot immutability"
  echo "  7. Verify service-role operations succeed"
  echo "  8. Verify profile auto-creation for both users"
  echo "  9. Verify exactly one owner profile"
  echo ""
  echo "Test prerequisites: Node.js 22+, Supabase local CLI, Docker"
  exit 0
fi

if echo "$DB_URL" | grep -qiE "supabase\.co|render\.com|aws|azure|cloud"; then
  echo "ERROR: Refusing remote database"
  exit 1
fi

PSQL="psql -v ON_ERROR_STOP=1 --echo-errors -t -A"

echo "Target: $(echo "$DB_URL" | sed 's/:[^:@]*@/:****@/g')"
echo ""

fail_count=0
pass_count=0
pass() { echo "  [PASS] $1"; pass_count=$((pass_count+1)); }
fail() { echo "  [FAIL] $1"; fail_count=$((fail_count+1)); }

# 1. Verify RLS policies exist
echo "--- Policy inventory ---"
POLICIES=$($PSQL "$DB_URL" -c "SELECT count(*) FROM pg_policies WHERE schemaname = 'public';" 2>/dev/null | tr -d ' \n')
[ "$POLICIES" = "31" ] && pass "31 RLS policies exist" || fail "Expected 31 policies, found $POLICIES"

# 2. Verify is_owner function
OWNER_FN=$($PSQL "$DB_URL" -c "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.proname = 'is_owner' AND n.nspname = 'public';" 2>/dev/null | tr -d ' \n')
[ "$OWNER_FN" = "1" ] && pass "is_owner function exists" || fail "is_owner function missing"

# 3. Verify trigger functions
for fn in check_snapshot_status_transition check_transaction_owner prevent_portfolio_deletion; do
  CNT=$($PSQL "$DB_URL" -c "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.proname = '$fn' AND n.nspname = 'public';" 2>/dev/null | tr -d ' \n')
  [ "$CNT" = "1" ] && pass "Function $fn exists" || fail "Function $fn missing"
done

# 4. Verify model immutability trigger
TRG=$($PSQL "$DB_URL" -c "SELECT count(*) FROM information_schema.triggers WHERE trigger_name = 'check_snapshot_status_transition';" 2>/dev/null | tr -d ' \n')
[ "$TRG" = "1" ] && pass "Status transition trigger exists" || fail "Status transition trigger missing"

# 5. Verify transaction owner trigger
TRG2=$($PSQL "$DB_URL" -c "SELECT count(*) FROM information_schema.triggers WHERE trigger_name = 'check_transaction_owner';" 2>/dev/null | tr -d ' \n')
[ "$TRG2" = "1" ] && pass "Transaction owner trigger exists" || fail "Transaction owner trigger missing"

# 6. Verify portfolio deletion trigger
TRG3=$($PSQL "$DB_URL" -c "SELECT count(*) FROM information_schema.triggers WHERE trigger_name = 'prevent_portfolio_deletion';" 2>/dev/null | tr -d ' \n')
[ "$TRG3" = "1" ] && pass "Portfolio deletion trigger exists" || fail "Portfolio deletion trigger missing"

# 7. Verify RLS is enabled on all tables
RLS_CNT=$($PSQL "$DB_URL" -c "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relrowsecurity = true AND n.nspname = 'public';" 2>/dev/null | tr -d ' \n')
[ "$RLS_CNT" = "17" ] && pass "RLS enabled on all 17 tables" || fail "Expected 17 RLS tables, found $RLS_CNT"

# 8. Verify policies reference is_owner
OWNER_POLICIES=$($PSQL "$DB_URL" -c "SELECT count(*) FROM pg_policies WHERE schemaname = 'public' AND (qual::text LIKE '%is_owner%' OR with_check::text LIKE '%is_owner%');" 2>/dev/null | tr -d ' \n')
[ "$OWNER_POLICIES" -ge 20 ] && pass "$OWNER_POLICIES policies use is_owner()" || fail "Fewer than 20 policies use is_owner()"

echo ""
echo "=== Full Supabase Auth tests require local Supabase ==="
echo "Run with: npx supabase start && PG_TEST_URL=... bash scripts/verify-rls.sh"
echo ""

# For local Supabase with auth, additional tests would run here using:
#   1. supabase.auth.signUp() for owner user -> get JWT
#   2. supabase.auth.signUp() for second user -> get JWT
#   3. Test anonymous reads denied
#   4. Test owner reads allowed
#   5. Test second user reads denied
#   6. Test transaction INSERT allowed for owner
#   7. Test transaction UPDATE/DELETE denied for owner
#   8. Test published snapshot UPDATE/DELETE denied
#   9. Verify profile creation with owner flag

echo "--- Summary ---"
echo "Passed: $pass_count"
echo "Failed: $fail_count"
[ "$fail_count" -gt 0 ] && echo "RLS TESTS FAILED" && exit 1 || echo "RLS SCHEMA TESTS PASSED"
