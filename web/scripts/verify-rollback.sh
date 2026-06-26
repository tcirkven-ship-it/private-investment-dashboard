#!/usr/bin/env bash
# Transactional Rollback Test — Real Database
set -euo pipefail

DB_URL="${PG_TEST_URL:-}"
if [ -z "$DB_URL" ]; then
  echo "ERROR: PG_TEST_URL is required"
  exit 1
fi

if echo "$DB_URL" | grep -qiE "supabase\.co|render\.com|aws|azure|cloud"; then
  echo "ERROR: Refusing remote database"
  exit 1
fi

PSQL="psql -v ON_ERROR_STOP=1 --echo-errors -t -A"
MIGRATIONS_DIR="supabase/migrations"
echo "=== Transactional Rollback Test ==="
echo ""

# Step 1: Verify empty
echo "Step 1: Verify empty database"
EMPTY=$(echo "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" | $PSQL "$DB_URL" 2>/dev/null | tr -d ' \n')
if [ "$EMPTY" != "0" ]; then
  echo "Database is not empty. Run reset_new_project.sql first."
  exit 1
fi
echo "  Database is empty."
echo ""

# Step 2: Begin migration, inject failure
echo "Step 2: Begin transaction, inject failure"
# Read migration SQL and append a guaranteed failure before commit
MIGRATION_SQL=$(cat "$MIGRATIONS_DIR/00001_schema.sql")
# Inject a syntax error before the final COMMIT
FAILING_SQL="${MIGRATION_SQL/COMMIT;/RAISE; -- intentional failure\nCOMMIT;}"

echo "$FAILING_SQL" | $PSQL "$DB_URL" 2>&1 && {
  echo "  FAIL: Migration should have failed but did not"
  exit 1
} || {
  echo "  PASS: Migration correctly failed with error"
}

echo ""

# Step 3: Verify no application objects remain
echo "Step 3: Verify rollback removed all objects"
REMAINING=$(echo "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" | $PSQL "$DB_URL" 2>/dev/null | tr -d ' \n')
if [ "$REMAINING" != "0" ]; then
  echo "  FAIL: $REMAINING tables remain after failed migration"
  exit 1
fi
echo "  PASS: Zero tables remain after rollback"

REMAINING_FUNCS=$(echo "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = 'public';" | $PSQL "$DB_URL" 2>/dev/null | tr -d ' \n')
if [ "$REMAINING_FUNCS" != "0" ]; then
  echo "  FAIL: $REMAINING_FUNCS functions remain after rollback"
  exit 1
fi
echo "  PASS: Zero functions remain after rollback"

echo ""
echo "=== ROLLBACK TEST PASSED ==="
