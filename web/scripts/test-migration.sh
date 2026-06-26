#!/usr/bin/env bash
# Migration smoke test — isolated database
source "$(dirname "$0")/db-test-lib.sh"
TEST_DB="dashboard_migration_test"

create_db "$TEST_DB"
DB_URL="${PG_TEST_URL/%$DB_NAME/$TEST_DB}"
PSQL="psql -v ON_ERROR_STOP=1 --echo-errors -t -A"

echo "=== Migration Smoke Test ==="
echo ""

# Phase 1: Verify empty
echo "--- Phase 1: Verify empty ---"
check "No application tables" "0" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
check "No application enums" "0" \
  "SELECT count(DISTINCT t.typname) FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid WHERE t.typnamespace::regnamespace = 'public';"

# Phase 2: Apply migration
echo "--- Phase 2: Apply 00001_schema.sql ---"
$PSQL -f "supabase/migrations/00001_schema.sql" "$DB_URL" || { fail "Migration 00001 failed"; report_results "MIGRATION SMOKE TEST"; }

# Phase 3: Exact inventory
echo "--- Phase 3: Exact inventory ---"
check "Table count" "17" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"

for tbl in profiles app_settings securities model_versions model_snapshots \
            model_snapshot_holdings model_publication_events portfolios \
            transactions price_observations benchmark_observations \
            portfolio_valuations rebalance_events rebalance_lines \
            owner_decisions data_imports audit_events; do
  check "Table: $tbl" "1" \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$tbl';"
done

# Enum values (ordered)
check "snapshot_status: DRAFT" "1" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'snapshot_status' AND e.enumlabel = 'DRAFT';"
check "snapshot_status: VALIDATED" "1" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'snapshot_status' AND e.enumlabel = 'VALIDATED';"
check "snapshot_status: APPROVED" "1" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'snapshot_status' AND e.enumlabel = 'APPROVED';"
check "snapshot_status: PUBLISHED" "1" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'snapshot_status' AND e.enumlabel = 'PUBLISHED';"
check "snapshot_status: SUPERSEDED" "1" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'snapshot_status' AND e.enumlabel = 'SUPERSEDED';"

check "rebalance_status: PENDING" "1" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'rebalance_status' AND e.enumlabel = 'PENDING';"
check "rebalance_status: COMPLETED" "1" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'rebalance_status' AND e.enumlabel = 'COMPLETED';"
check "rebalance_status: CANCELLED" "1" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'rebalance_status' AND e.enumlabel = 'CANCELLED';"

check "transaction_event_type: DEPOSIT" "1" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'transaction_event_type' AND e.enumlabel = 'DEPOSIT';"
check "transaction_event_type: CORRECTION" "1" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'transaction_event_type' AND e.enumlabel = 'CORRECTION';"
check "transaction_event_type has 14 values" "14" \
  "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'transaction_event_type';"

# Functions (exact names)
for fn in check_snapshot_status_transition check_transaction_owner handle_new_user \
          is_owner prevent_portfolio_deletion update_updated_at_column; do
  check "Function: $fn" "1" \
    "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.proname = '$fn' AND n.nspname = 'public';"
done

# Triggers (exact names)
for trg in set_profiles_updated_at set_portfolios_updated_at on_auth_user_created \
            check_snapshot_status_transition check_transaction_owner prevent_portfolio_deletion; do
  check "Trigger: $trg" "1" \
    "SELECT count(*) FROM information_schema.triggers WHERE trigger_name = '$trg';"
done

# Secondary indexes (exclude PK and unique constraint indexes)
EXPECTED_INDEXES=(
  idx_transactions_portfolio idx_transactions_owner idx_model_snapshots_status
  idx_model_snapshot_holdings_snapshot idx_price_observations_security
  idx_benchmark_observations idx_rebalance_events_portfolio
  idx_portfolio_valuations_portfolio idx_model_publication_events_snapshot
  idx_audit_events_owner
)
for idx in "${EXPECTED_INDEXES[@]}"; do
  check "Index: $idx" "1" \
    "SELECT count(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname = '$idx';"
done

# RLS
check "RLS on all 17 tables" "17" \
  "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relrowsecurity = true AND n.nspname = 'public';"
check "RLS policies" "31" \
  "SELECT count(*) FROM pg_policies WHERE schemaname = 'public';"

# Phase 4: Apply 00002 (no-op)
echo "--- Phase 4: Apply 00002 ---"
$PSQL -f "supabase/migrations/00002_fixes.sql" "$DB_URL" || fail "Migration 00002 failed"

# Phase 5: Test status transitions
echo "--- Phase 5: Status transitions ---"
$PSQL "$DB_URL" -v ON_ERROR_STOP=1 -c "INSERT INTO auth.users (id, email, encrypted_password, created_at) VALUES ('00000000-0000-0000-0000-000000000001', 'test@t.com', '\$2a\$10\$dummyhash', now()) ON CONFLICT (id) DO NOTHING;" || fail "Could not create test user in auth.users"
$PSQL "$DB_URL" -c "INSERT INTO public.model_versions (model_id, version) VALUES ('test-m', '1.0');"
MV_ID=$($PSQL "$DB_URL" -c "SELECT id FROM public.model_versions LIMIT 1;" 2>/dev/null | head -1)
$PSQL "$DB_URL" -c "INSERT INTO public.model_snapshots (model_version_id, snapshot_id, status, effective_date) VALUES ('$MV_ID', 's1', 'DRAFT', '2025-01-01');"

# Valid transitions
$PSQL "$DB_URL" -c "UPDATE public.model_snapshots SET status = 'VALIDATED' WHERE snapshot_id = 's1';" 2>/dev/null && pass "DRAFT->VALIDATED allowed" || fail "DRAFT->VALIDATED blocked"
$PSQL "$DB_URL" -c "UPDATE public.model_snapshots SET status = 'APPROVED' WHERE snapshot_id = 's1';" 2>/dev/null && pass "VALIDATED->APPROVED allowed" || fail "VALIDATED->APPROVED blocked"
$PSQL "$DB_URL" -c "UPDATE public.model_snapshots SET status = 'PUBLISHED' WHERE snapshot_id = 's1';" 2>/dev/null && pass "APPROVED->PUBLISHED allowed" || fail "APPROVED->PUBLISHED blocked"

# Invalid transitions
if echo "UPDATE public.model_snapshots SET status = 'DRAFT' WHERE snapshot_id = 's1';" | $PSQL "$DB_URL" 2>/dev/null; then
  fail "PUBLISHED->DRAFT should be rejected"
else
  pass "PUBLISHED->DRAFT correctly rejected"
fi

# Immutability
if echo "UPDATE public.model_snapshots SET status = 'SUPERSEDED' WHERE snapshot_id = 's1';" | $PSQL "$DB_URL" 2>/dev/null; then
  pass "PUBLISHED->SUPERSEDED allowed"
  if echo "UPDATE public.model_snapshots SET effective_date = '2026-01-01' WHERE snapshot_id = 's1';" | $PSQL "$DB_URL" 2>/dev/null; then
    fail "SUPERSEDED snapshot was mutable"
  else
    pass "SUPERSEDED snapshot immutable"
  fi
else
  fail "PUBLISHED->SUPERSEDED blocked"
fi

# Phase 6: Test transaction owner consistency
echo "--- Phase 6: Transaction owner ---"
$PSQL "$DB_URL" -c "INSERT INTO public.portfolios (owner_id, name, opening_date) VALUES ('00000000-0000-0000-0000-000000000001', 'TP', '2025-01-01');"
PF_ID=$($PSQL "$DB_URL" -c "SELECT id FROM public.portfolios LIMIT 1;" 2>/dev/null | head -1)

# Valid insert
$PSQL "$DB_URL" -c "INSERT INTO public.transactions (portfolio_id, event_type, event_date, gross_amount, idempotency_key, owner_id) VALUES ('$PF_ID', 'DEPOSIT', '2025-01-02', 100, 'tk1', '00000000-0000-0000-0000-000000000001');" 2>/dev/null && pass "Transaction with matching owner allowed" || fail "Transaction with matching owner blocked"

# Invalid insert (wrong owner)
if echo "INSERT INTO public.transactions (portfolio_id, event_type, event_date, gross_amount, idempotency_key, owner_id) VALUES ('$PF_ID', 'DEPOSIT', '2025-01-02', 100, 'tk2', '00000000-0000-0000-0000-000000000099');" | $PSQL "$DB_URL" 2>/dev/null; then
  fail "Transaction with wrong owner should be rejected"
else
  pass "Transaction with wrong owner correctly rejected"
fi

# Verify UPDATE/DELETE denied via trigger
$PSQL "$DB_URL" -c "UPDATE public.transactions SET gross_amount = 999 WHERE idempotency_key = 'tk1';" 2>/dev/null && fail "UPDATE allowed (should be blocked)" || pass "UPDATE correctly blocked"

# Phase 7: Portfolio deletion protection
if echo "DELETE FROM public.portfolios WHERE id = '$PF_ID';" | $PSQL "$DB_URL" 2>/dev/null; then
  fail "Portfolio deletion allowed (should be blocked)"
else
  pass "Portfolio deletion correctly blocked"
fi

# Cleanup: drop the whole database
drop_db "$TEST_DB"
report_results "MIGRATION SMOKE TEST"
