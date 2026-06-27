#!/usr/bin/env bash
# Transactional rollback test — runs in its own GitHub Actions job with a fresh Supabase Postgres.
source "$(dirname "$0")/db-test-lib.sh"
PSQL="psql -v ON_ERROR_STOP=1 --echo-errors -t -A"

echo "=== Rollback Test ==="
echo ""

# Verify empty
check "No application tables" "0" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Read migration, inject failure before COMMIT
MIGRATION=$(cat "supabase/migrations/00001_schema.sql")
# Replace COMMIT with a guaranteed error
FAILING_SQL="${MIGRATION/COMMIT;/RAISE 'intentional_failure';END;}"
FAILING_SQL="${FAILING_SQL%COMMIT;}"
FAILING_SQL="${FAILING_SQL}RAISE 'intentional_failure';"
FAILING_SQL="${FAILING_SQL}COMMIT;"

echo "--- Injecting failure ---"
echo "$FAILING_SQL" | $PSQL "$DB_URL" 2>/dev/null && {
  fail "Migration should have failed"
  report_results "ROLLBACK TEST"
} || {
  pass "Migration correctly failed"
}

# Verify zero objects remain
echo "--- Verifying rollback ---"
check "Zero tables remain" "0" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"

check "Zero application enums" "0" \
  "SELECT count(DISTINCT t.typname) FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid WHERE t.typnamespace::regnamespace = 'public';"

check "Zero application functions" "0" \
  "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = 'public' AND p.prokind = 'f';"

check "Zero RLS policies" "0" \
  "SELECT count(*) FROM pg_policies WHERE schemaname = 'public';"

check "Zero application sequences" "0" \
  "SELECT count(*) FROM information_schema.sequences WHERE sequence_schema = 'public';"

report_results "ROLLBACK TEST"
