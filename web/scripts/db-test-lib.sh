#!/usr/bin/env bash
# Shared library for database verification tests
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

# Extract database name from URL
DB_NAME=$(echo "$DB_URL" | sed 's|.*/\([^?]*\)|\1|' | sed 's/?.*//')

if [ -z "${EXPECTED_TEST_DATABASE:-}" ]; then
  echo "ERROR: EXPECTED_TEST_DATABASE must be set"
  exit 1
fi

if [ "$DB_NAME" != "$EXPECTED_TEST_DATABASE" ]; then
  echo "ERROR: Database name mismatch. Expected '$EXPECTED_TEST_DATABASE', got '$DB_NAME'"
  exit 1
fi

# Verify local
if echo "$DB_URL" | grep -qiE "supabase\.co|render\.com|aws\.|azure\.|cloud\."; then
  echo "ERROR: Refusing remote/unidentified database"
  exit 1
fi

# Base URL without database name
BASE_URL=$(echo "$DB_URL" | sed "s|/$DB_NAME|/postgres|")

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

create_db() {
  local dbname="$1"
  echo "Creating database: $dbname"
  PG_URL="$BASE_URL" $PSQL -c "CREATE DATABASE $dbname;" 2>/dev/null || true
}

drop_db() {
  local dbname="$1"
  echo "Dropping database: $dbname"
  # Terminate connections first
  PG_URL="$BASE_URL" $PSQL -c "
    SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$dbname';
  " 2>/dev/null || true
  PG_URL="$BASE_URL" $PSQL -c "DROP DATABASE IF EXISTS $dbname;" 2>/dev/null || true
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
