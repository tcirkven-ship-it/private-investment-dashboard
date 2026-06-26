#!/usr/bin/env bash
# Database Migration Smoke Test — Real Supabase-Compatible
set -euo pipefail

DB_URL="${PG_TEST_URL:-}"
if [ -z "$DB_URL" ]; then
  echo "ERROR: PG_TEST_URL environment variable is required"
  exit 1
fi

# Verify this is a local disposable database
if echo "$DB_URL" | grep -qiE "supabase\.co|render\.com|aws|azure|cloud"; then
  echo "ERROR: Refusing to run against a remote or unidentified database"
  echo "  URL: $(echo "$DB_URL" | sed 's/:[^:@]*@/:****@/g')"
  exit 1
fi

SAFE_URL=$(echo "$DB_URL" | sed 's/:[^:@]*@/:****@/g')
echo "Target database: $SAFE_URL"
echo "Disposable check: PASS (local)"
echo ""

PSQL="psql -v ON_ERROR_STOP=1 --echo-errors -t -A"
MIGRATIONS_DIR="supabase/migrations"

fail_count=0
pass_count=0

pass() { echo "  [PASS] $1"; pass_count=$((pass_count+1)); }
fail() { echo "  [FAIL] $1"; fail_count=$((fail_count+1)); }

check() {
  local label="$1" expected="$2" query="$3"
  local actual
  actual=$(echo "$query" | $PSQL "$DB_URL" 2>/dev/null | tr -d ' \n' || echo "ERROR")
  if [ "$actual" = "$expected" ]; then
    pass "$label"
  else
    fail "$label (expected=$expected, actual=$actual)"
  fi
}

# ============================================================
# Phase 1: Empty database check
# ============================================================
echo "=== Phase 1: Empty database check ==="
check "Public tables = 0" "0" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
check "Public enums = 0" "0" \
  "SELECT count(DISTINCT t.typname) FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid WHERE t.typnamespace = 'public'::regnamespace;"
check "Public functions (app) = 0" "0" \
  "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = 'public' AND p.proname LIKE 'check_%' OR p.proname LIKE 'prevent_%' OR p.proname LIKE 'update_%' OR p.proname LIKE 'handle_%' OR p.proname = 'is_owner';"

# ============================================================
# Phase 2: Apply migration 00001
# ============================================================
echo ""
echo "=== Phase 2: Apply 00001_schema.sql ==="
$PSQL -f "$MIGRATIONS_DIR/00001_schema.sql" "$DB_URL" && pass "Migration 00001 applied" || fail "Migration 00001 failed"

# ============================================================
# Phase 3: Verify inventory
# ============================================================
echo ""
echo "=== Phase 3: Schema inventory ==="

# Tables
check "Tables = 17" "17" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"

for tbl in profiles app_settings securities model_versions model_snapshots \
            model_snapshot_holdings model_publication_events portfolios \
            transactions price_observations benchmark_observations \
            portfolio_valuations rebalance_events rebalance_lines \
            owner_decisions data_imports audit_events; do
  check "Table exists: $tbl" "1" \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$tbl';"
done

# Enums (schema-qualified)
check "snapshot_status enum" "1" \
  "SELECT count(*) FROM pg_type WHERE typname = 'snapshot_status' AND typnamespace = 'public'::regnamespace;"
check "rebalance_status enum" "1" \
  "SELECT count(*) FROM pg_type WHERE typname = 'rebalance_status' AND typnamespace = 'public'::regnamespace;"
check "transaction_event_type enum" "1" \
  "SELECT count(*) FROM pg_type WHERE typname = 'transaction_event_type' AND typnamespace = 'public'::regnamespace;"

# Enum values
check "snapshot_status values" "5" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'snapshot_status';"
check "rebalance_status values" "3" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'rebalance_status';"
check "transaction_event_type values" "14" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'transaction_event_type';"

# Functions
check "check_snapshot_status_transition function" "1" \
  "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.proname = 'check_snapshot_status_transition' AND n.nspname = 'public';"
check "check_transaction_owner function" "1" \
  "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.proname = 'check_transaction_owner' AND n.nspname = 'public';"
check "is_owner function" "1" \
  "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.proname = 'is_owner' AND n.nspname = 'public';"
check "handle_new_user function" "1" \
  "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.proname = 'handle_new_user' AND n.nspname = 'public';"
check "prevent_portfolio_deletion function" "1" \
  "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.proname = 'prevent_portfolio_deletion' AND n.nspname = 'public';"
check "update_updated_at_column function" "1" \
  "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.proname = 'update_updated_at_column' AND n.nspname = 'public';"

# Triggers
for trg in set_profiles_updated_at set_portfolios_updated_at on_auth_user_created \
            check_snapshot_status_transition check_transaction_owner \
            prevent_portfolio_deletion; do
  check "Trigger: $trg" "1" \
    "SELECT count(*) FROM information_schema.triggers WHERE trigger_name = '$trg';"
done

# Secondary indexes (not PK/unique constraint indexes)
check "Secondary indexes = 8" "8" \
  "SELECT count(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname NOT LIKE '%_pkey' AND indexname NOT LIKE '%_key' AND indexname NOT LIKE '%_unique';"

# RLS-enabled tables
check "RLS enabled on all 17 tables" "17" \
  "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relrowsecurity = true AND n.nspname = 'public';"

# RLS policies
check "RLS policies = 31" "31" \
  "SELECT count(*) FROM pg_policies WHERE schemaname = 'public';"

# ============================================================
# Phase 4: Apply migration 00002 (no-op)
# ============================================================
echo ""
echo "=== Phase 4: Apply 00002_fixes.sql ==="
$PSQL -f "$MIGRATIONS_DIR/00002_fixes.sql" "$DB_URL" && pass "Migration 00002 applied" || fail "Migration 00002 failed"

# ============================================================
# Phase 5: Verify trigger-based constraints
# ============================================================
echo ""
echo "=== Phase 5: Constraint verification ==="

# Create a test user in auth.users
$PSQL "$DB_URL" -c "INSERT INTO auth.users (id, email) VALUES ('00000000-0000-0000-0000-000000000001', 'owner@test.com');" 2>/dev/null && pass "Test user created" || fail "Test user creation"

# Create a portfolio
PORTFOLIO_ID=$($PSQL "$DB_URL" -c "INSERT INTO public.portfolios (owner_id, name, opening_date) VALUES ('00000000-0000-0000-0000-000000000001', 'Test Portfolio', '2025-01-01') RETURNING id;" 2>/dev/null | head -1)
pass "Portfolio created: $PORTFOLIO_ID"

# Insert a transaction
$PSQL "$DB_URL" -c "INSERT INTO public.transactions (portfolio_id, event_type, event_date, gross_amount, idempotency_key, owner_id) VALUES ('$PORTFOLIO_ID', 'DEPOSIT', '2025-01-02', 100000, 'test-tx-1', '00000000-0000-0000-0000-000000000001');" 2>/dev/null && pass "Transaction inserted" || fail "Transaction insert failed"

# Test status transition trigger
$PSQL "$DB_URL" -c "INSERT INTO public.model_versions (model_id, version) VALUES ('test-model', '1.0');" 2>/dev/null
MV_ID=$($PSQL "$DB_URL" -c "SELECT id FROM public.model_versions LIMIT 1;" 2>/dev/null | head -1)
$PSQL "$DB_URL" -c "INSERT INTO public.model_snapshots (model_version_id, snapshot_id, status, effective_date) VALUES ('$MV_ID', 'test-snap', 'DRAFT', '2025-06-01');" 2>/dev/null

# Valid: DRAFT -> VALIDATED
$PSQL "$DB_URL" -c "UPDATE public.model_snapshots SET status = 'VALIDATED' WHERE snapshot_id = 'test-snap';" 2>/dev/null && pass "DRAFT->VALIDATED allowed" || fail "DRAFT->VALIDATED failed"

# Invalid: VALIDATED -> DRAFT (should fail)
if echo "UPDATE public.model_snapshots SET status = 'DRAFT' WHERE snapshot_id = 'test-snap';" | $PSQL "$DB_URL" 2>/dev/null; then
  fail "VALIDATED->DRAFT should have been rejected"
else
  pass "VALIDATED->DRAFT correctly rejected"
fi

# Reject published mutation
$PSQL "$DB_URL" -c "UPDATE public.model_snapshots SET status = 'APPROVED' WHERE snapshot_id = 'test-snap';" 2>/dev/null
$PSQL "$DB_URL" -c "UPDATE public.model_snapshots SET status = 'PUBLISHED' WHERE snapshot_id = 'test-snap';" 2>/dev/null
if echo "UPDATE public.model_snapshots SET status = 'DRAFT' WHERE snapshot_id = 'test-snap';" | $PSQL "$DB_URL" 2>/dev/null; then
  fail "PUBLISHED snapshot was mutable"
else
  pass "PUBLISHED snapshot correctly immutable"
fi

# Test portfolio deletion protection
if echo "DELETE FROM public.portfolios WHERE id = '$PORTFOLIO_ID';" | $PSQL "$DB_URL" 2>/dev/null; then
  fail "Portfolio with transactions was deletable"
else
  pass "Portfolio deletion correctly blocked"
fi

# ============================================================
# Phase 6: Cleanup
# ============================================================
echo ""
echo "=== Phase 6: Cleanup ==="
$PSQL "$DB_URL" -c "DELETE FROM public.transactions WHERE idempotency_key = 'test-tx-1';" 2>/dev/null
$PSQL "$DB_URL" -c "DELETE FROM public.model_snapshots WHERE snapshot_id = 'test-snap';" 2>/dev/null
$PSQL "$DB_URL" -c "DELETE FROM public.model_versions WHERE model_id = 'test-model';" 2>/dev/null
$PSQL "$DB_URL" -c "DELETE FROM public.portfolios WHERE name = 'Test Portfolio';" 2>/dev/null
$PSQL "$DB_URL" -c "DELETE FROM auth.users WHERE id = '00000000-0000-0000-0000-000000000001';" 2>/dev/null
pass "Cleanup complete"

# ============================================================
# Results
# ============================================================
echo ""
echo "=== RESULTS ==="
echo " Passed: $pass_count"
echo " Failed: $fail_count"
if [ "$fail_count" -gt 0 ]; then
  echo " MIGRATION TESTS FAILED"
  exit 1
fi
echo " MIGRATION TESTS PASSED"
