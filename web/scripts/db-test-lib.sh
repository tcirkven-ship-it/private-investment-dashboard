#!/usr/bin/env bash
# Shared library for database verification tests
# Each test runs in its own GitHub Actions job with a fresh Supabase Postgres service.
# No separate database creation needed — use the Supabase-compatible 'postgres' database.
set -euo pipefail

# Safety guards
if [ "${ALLOW_DESTRUCTIVE_DB_TESTS:-}" != "true" ]; then
  echo "ERROR: Set ALLOW_DESTRUCTIVE_DB_TESTS=true to run destructive tests"
  exit 1
fi

DB_URL="${PG_TEST_URL:-}"
if [ -z "$DB_URL" ]; then
  echo "ERROR: PG_TEST_URL is required"
  exit 1
fi

DB_NAME=$(echo "$DB_URL" | sed 's|.*/\([^?]*\)|\1|' | sed 's/?.*//')

if [ -z "${EXPECTED_TEST_DATABASE:-}" ]; then
  echo "ERROR: EXPECTED_TEST_DATABASE must be set"
  exit 1
fi

if [ "$DB_NAME" != "$EXPECTED_TEST_DATABASE" ]; then
  echo "ERROR: Database name mismatch. Expected '$EXPECTED_TEST_DATABASE', got '$DB_NAME'"
  exit 1
fi

if echo "$DB_URL" | grep -qiE "supabase\.co|render\.com|aws\.|azure\.|cloud\."; then
  echo "ERROR: Refusing remote/unidentified database"
  exit 1
fi

# Verify Supabase compatibility
HAS_AUTH=$(psql "$DB_URL" -v ON_ERROR_STOP=1 -t -A -c "SELECT count(*) FROM information_schema.schemata WHERE schema_name = 'auth';" 2>/dev/null || echo "0")
if [ "$HAS_AUTH" != "1" ]; then
  echo "ERROR: Database does not have 'auth' schema. This test requires a Supabase-compatible PostgreSQL."
  echo "  The supabase/postgres:16.6.0 Docker image includes auth schema automatically."
  echo "  Ensure each test job gets its own fresh Supabase Postgres service container."
  exit 1
fi

PSQL="psql -v ON_ERROR_STOP=1 --echo-errors -t -A"

fail_count=0
pass_count=0

pass() { echo "  [PASS] $1"; pass_count=$((pass_count+1)); }
fail() { echo "  [FAIL] $1"; fail_count=$((fail_count+1)); }

check() {
  local label="$1" expected="$2" query="$3"
  local actual
  actual=$(echo "$query" | $PSQL "$DB_URL" 2>/dev/null | tr -d ' \n' || echo "QUERY_ERROR")
  if [ "$actual" = "$expected" ]; then
    pass "$label"
  else
    fail "$label (expected=$expected, actual=$actual)"
  fi
}

report_results() {
  local test_name="$1"
  echo ""
  echo "=== $test_name ==="
  echo " Passed: $pass_count"
  echo " Failed: $fail_count"
  if [ "$fail_count" -gt 0 ]; then
    echo " RESULT: FAILED"
    exit 1
  fi
  echo " RESULT: PASSED"
}
