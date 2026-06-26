#!/usr/bin/env bash
# Database Migration Verification — Real Supabase-Compatible Smoke Test
set -euo pipefail

DB_URL="${PG_TEST_URL:-}"
if [ -z "$DB_URL" ]; then
  echo "ERROR: PG_TEST_URL environment variable is required"
  echo "Usage: PG_TEST_URL=postgresql://postgres:postgres@localhost:5432/dashboard_test bash scripts/verify-migrations.sh"
  exit 1
fi

# Redact password from output
SAFE_URL=$(echo "$DB_URL" | sed 's/:[^:@]*@/:****@/g')
echo "Target database: $SAFE_URL"
echo ""

PSQL="psql -v ON_ERROR_STOP=1 --echo-errors -t -A"

# Helper: run sql and check exit code
run_sql() {
  local label="$1"
  local sql="$2"
  echo "  [RUN] $label"
  if echo "$sql" | $PSQL "$DB_URL" 2>/dev/null; then
    echo "  [PASS] $label"
  else
    echo "  [FAIL] $label"
    return 1
  fi
}

# Helper: run sql file
run_file() {
  local label="$1"
  local file="$2"
  echo "  [RUN] $label ($file)"
  if $PSQL -f "$file" "$DB_URL" 2>&1; then
    echo "  [PASS] $label"
  else
    echo "  [FAIL] $label"
    return 1
  fi
}

# Helper: assert query result equals expected value
assert_eq() {
  local label="$1"
  local query="$2"
  local expected="$3"
  local actual
  actual=$(echo "$query" | $PSQL "$DB_URL" 2>/dev/null | tr -d ' \n')
  if [ "$actual" = "$expected" ]; then
    echo "  [PASS] $label (expected=$expected)"
  else
    echo "  [FAIL] $label (expected=$expected, actual=$actual)"
    return 1
  fi
}

MIGRATIONS_DIR="supabase/migrations"

echo "=== Phase 1: Empty database check ==="
assert_eq "Public tables count = 0" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" \
  "0"

echo ""
echo "=== Phase 2: Apply migration 00001 ==="
run_file "Apply 00001_schema.sql" "$MIGRATIONS_DIR/00001_schema.sql"

echo ""
echo "=== Phase 3: Verify inventory ==="
assert_eq "Table count = 17" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" \
  "17"

assert_eq "Enum count = 3" \
  "SELECT count(DISTINCT t.typname) FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid;" \
  "3"

assert_eq "RLS-enabled tables = 17" \
  "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relrowsecurity = true AND n.nspname = 'public';" \
  "17"

assert_eq "Policies count = 31" \
  "SELECT count(*) FROM pg_policies WHERE schemaname = 'public';" \
  "31"

assert_eq "Indexes count = 10" \
  "SELECT count(*) FROM pg_indexes WHERE schemaname = 'public';" \
  "10"

echo ""
echo "=== Phase 4: Apply migration 00002 (no-op) ==="
run_file "Apply 00002_fixes.sql" "$MIGRATIONS_DIR/00002_fixes.sql"

echo ""
echo "=== Phase 5: Verify model immutability trigger ==="
run_sql "Create DRAFT snapshot" "
  INSERT INTO public.model_versions (model_id, version) VALUES ('test', '1.0');
  INSERT INTO public.model_snapshots (model_version_id, snapshot_id, status, effective_date)
  VALUES ((SELECT id FROM public.model_versions LIMIT 1), 'test-snap-1', 'DRAFT', '2026-01-01');
"

# Verify trigger prevents updating published
run_sql "Update DRAFT to PUBLISHED" "
  UPDATE public.model_snapshots
  SET status = 'PUBLISHED', published_at = now()
  WHERE snapshot_id = 'test-snap-1';
"

# Try to update published (should fail)
echo "  [RUN] Update published snapshot (should fail)"
if echo "UPDATE public.model_snapshots SET status = 'DRAFT' WHERE snapshot_id = 'test-snap-1';" | $PSQL "$DB_URL" 2>&1; then
  echo "  [FAIL] Published snapshot was mutable"
  exit 1
else
  echo "  [PASS] Published snapshot correctly immutable"
fi

echo ""
echo "=== Phase 6: Verify ledger constraints ==="
run_sql "CONSTRAINT: portfolio deletion blocked" "
  INSERT INTO public.portfolios (owner_id, name, opening_date)
  VALUES ('00000000-0000-0000-0000-000000000000', 'Test', '2026-01-01');
  INSERT INTO public.transactions (portfolio_id, event_type, event_date, gross_amount, idempotency_key, owner_id)
  VALUES ((SELECT id FROM public.portfolios LIMIT 1), 'DEPOSIT', '2026-01-02', 1000, 'test-tx-1', '00000000-0000-0000-0000-000000000000');
"

echo "  [RUN] Delete portfolio with transactions (should fail)"
if echo "DELETE FROM public.portfolios WHERE name = 'Test';" | $PSQL "$DB_URL" 2>&1; then
  echo "  [FAIL] Portfolio with transactions was deletable"
  exit 1
else
  echo "  [PASS] Portfolio deletion correctly blocked"
fi

echo ""
echo "=== Phase 7: Apply reset ==="
# Reset requires all tables to be empty first
run_sql "Delete test data" "
  DELETE FROM public.transactions WHERE idempotency_key = 'test-tx-1';
  DELETE FROM public.model_snapshots WHERE snapshot_id = 'test-snap-1';
  DELETE FROM public.model_versions WHERE model_id = 'test';
  DELETE FROM public.portfolios WHERE name = 'Test';
"

run_file "Reset project" "supabase/reset_new_project.sql"
assert_eq "Tables after reset = 0" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" \
  "0"

echo ""
echo "=== Phase 8: Reapply migrations ==="
run_file "Reapply 00001" "$MIGRATIONS_DIR/00001_schema.sql"
run_file "Reapply 00002" "$MIGRATIONS_DIR/00002_fixes.sql"
assert_eq "Tables after reapply = 17" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" \
  "17"

echo ""
echo "=== ALL MIGRATION TESTS PASSED ==="
