#!/usr/bin/env bash
# Reset and reapply test — runs in its own GitHub Actions job with a fresh Supabase Postgres.
source "$(dirname "$0")/db-test-lib.sh"
PSQL="psql -v ON_ERROR_STOP=1 --echo-errors -t -A"

echo "=== Reset and Reapply Test ==="
echo ""

# Phase 1: Apply migration
echo "--- Phase 1: Apply migration ---"
$PSQL -f "supabase/migrations/00001_schema.sql" "$DB_URL" || { fail "Migration failed"; report_results "RESET TEST"; }

# Create test user + data to test reset safety
$PSQL "$DB_URL" -v ON_ERROR_STOP=1 -c "INSERT INTO auth.users (id, email, encrypted_password) VALUES ('00000000-0000-0000-0000-000000000002', 'reset@t.com', '\$2a\$10\$dummyhash') ON CONFLICT (id) DO NOTHING;" || fail "Could not create test user"
$PSQL "$DB_URL" -c "INSERT INTO public.model_versions (model_id, version) VALUES ('rv', '1');"
$PSQL "$DB_URL" -c "INSERT INTO public.portfolios (owner_id, name, opening_date) VALUES ('00000000-0000-0000-0000-000000000002', 'RP', '2025-01-01');"

check "Data exists before reset" "1" \
  "SELECT count(*) FROM public.model_versions;"

# Phase 2: Reset should refuse
echo "--- Phase 2: Reset safety ---"
if PG_URL="$DB_URL" $PSQL -f "supabase/reset_new_project.sql" 2>/dev/null; then
  fail "Reset should have refused with data present"
else
  pass "Reset correctly refused with data present"
fi

# Phase 3: Apply override and reset
echo "--- Phase 3: Force reset ---"
PG_URL="$DB_URL" $PSQL -c "SET app.reset_override = true;" -f "supabase/reset_new_project.sql" 2>/dev/null || { fail "Reset failed"; report_results "RESET TEST"; }

check "Zero tables after reset" "0" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
check "Zero enums after reset" "0" \
  "SELECT count(DISTINCT t.typname) FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid WHERE t.typnamespace::regnamespace = 'public';"
check "Zero functions after reset" "0" \
  "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = 'public' AND p.prokind = 'f';"
check "Zero triggers after reset" "0" \
  "SELECT count(*) FROM information_schema.triggers WHERE trigger_schema = 'public';"
check "Zero policies after reset" "0" \
  "SELECT count(*) FROM pg_policies WHERE schemaname = 'public';"

# Phase 4: Reapply
echo "--- Phase 4: Reapply ---"
$PSQL -f "supabase/migrations/00001_schema.sql" "$DB_URL" || { fail "Reapply failed"; report_results "RESET TEST"; }
check "Tables after reapply" "17" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Verify reset works on empty schema too
PG_URL="$DB_URL" $PSQL -c "SET app.reset_override = true;" -f "supabase/reset_new_project.sql" 2>/dev/null || { fail "Second reset failed"; report_results "RESET TEST"; }
check "Zero after second reset" "0" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"

report_results "RESET TEST"
