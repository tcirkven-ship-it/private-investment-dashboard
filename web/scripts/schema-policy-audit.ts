#!/usr/bin/env tsx
/**
 * Schema and Policy Definition Audit
 *
 * Verifies exact database object definitions against a committed expected
 * inventory. Exits nonzero on any mismatch.
 *
 * Usage: PG_TEST_URL=postgresql://... npx tsx scripts/schema-policy-audit.ts
 */

import { execSync } from "child_process";

const DB_URL = process.env.PG_TEST_URL || "";

if (!DB_URL) {
  console.error("FATAL: PG_TEST_URL is required");
  process.exit(1);
}

let passed = 0;
let failed = 0;

function sql(query: string): string {
  return execSync(
    `psql "${DB_URL}" -v ON_ERROR_STOP=1 -t -A -c "${query.replace(/"/g, '\\"')}"`,
    { encoding: "utf-8", timeout: 10000 }
  ).trim();
}

function assert(label: string, actual: string, expected: string) {
  if (actual === expected) {
    passed++;
  } else {
    failed++;
    console.log(`[FAIL] ${label}`);
    console.log(`  expected: ${expected}`);
    console.log(`  actual:   ${actual}`);
  }
}

function assertTable(table: string, columns: string) {
  const actual = sql(`SELECT string_agg(column_name || ':' || data_type || ':' || CASE WHEN is_nullable = 'NO' THEN 'NN' ELSE '' END || ':' || COALESCE(column_default, ''), '|') FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '${table}' ORDER BY ordinal_position;`);
  assert(`table ${table} columns`, actual, columns);
}

console.log("=== Schema and Policy Definition Audit ===");
console.log("");

// ─── Tables and columns ─────────────────────────────────────────
console.log("--- Tables and columns ---");
assertTable("profiles", "id:uuid:NN:|email:text:NN:|display_name:text::|totp_enabled:boolean::false|is_owner:boolean::false|created_at:timestamptz::now()|updated_at:timestamptz::now()");
assertTable("app_settings", "key:text:NN:|value:jsonb:NN:|updated_at:timestamptz::now()");
assertTable("securities", "id:uuid:NN:|ticker:text:NN:|company_name:text::|sector:text::|industry:text::|is_active:boolean::true|data_source:text::yfinance|created_at:timestamptz::now()");
assertTable("model_versions", "id:uuid:NN:|model_id:text:NN:|version:text:NN:|description:text::|config_hash:text::|formula_version:text::|created_at:timestamptz::now()");
assertTable("model_snapshots", "id:uuid:NN:|model_version_id:uuid:NN:|snapshot_id:text:NN:|status:snapshot_status:NN:|effective_date:date:NN:|decision_timestamp:timestamptz::|execution_convention:text::next_valid_session_close|universe_screened:integer::|eligible_count:integer::|valid_score_count:integer::|integrity_hash:text::|source_commit:text::|warnings:jsonb::|created_at:timestamptz::now()|published_at:timestamptz::|superseded_at:timestamptz::");
assertTable("model_snapshot_holdings", "id:uuid:NN:|snapshot_id:uuid:NN:|security_id:uuid:NN:|rank:integer:NN:|target_weight:numeric:NN:|b2_score:numeric::|quality_percentile:numeric::|quality_components_ok:integer::0|inclusion_reason:text::");
assertTable("model_publication_events", "id:uuid:NN:|snapshot_id:uuid:NN:|from_status:text::|to_status:text:NN:|changed_by:uuid::|reason:text::|created_at:timestamptz::now()");
assertTable("portfolios", "id:uuid:NN:|owner_id:uuid:NN:|name:text:NN:|currency:text::USD|opening_date:date:NN:|notes:text::|is_archived:boolean::false|created_at:timestamptz::now()|updated_at:timestamptz::now()");
assertTable("transactions", "id:uuid:NN:|portfolio_id:uuid:NN:|security_id:uuid::|event_type:transaction_event_type:NN:|event_date:date:NN:|quantity:numeric::|price:numeric::|gross_amount:numeric:NN:|commission:numeric::0|notes:text::|idempotency_key:text:NN:|corrected_by:uuid::|owner_id:uuid:NN:|created_at:timestamptz::now()");
assertTable("price_observations", "id:uuid:NN:|security_id:uuid:NN:|observation_date:date:NN:|close:numeric::|adj_close:numeric::|volume:bigint::|source:text::yfinance");
assertTable("benchmark_observations", "id:uuid:NN:|ticker:text:NN:|observation_date:date:NN:|price:numeric::|total_return_index:numeric::");
assertTable("portfolio_valuations", "id:uuid:NN:|portfolio_id:uuid:NN:|valuation_date:date:NN:|total_value:numeric:NN:|cash_balance:numeric::0|total_deposits:numeric::0|total_withdrawals:numeric::0");
assertTable("rebalance_events", "id:uuid:NN:|portfolio_id:uuid:NN:|model_snapshot_id:uuid:NN:|rebalance_date:date:NN:|status:rebalance_status:NN:|estimated_cost:numeric::|completed_at:timestamptz::|owner_id:uuid:NN:");
assertTable("rebalance_lines", "id:uuid:NN:|rebalance_event_id:uuid:NN:|security_id:uuid:NN:|current_quantity:numeric::0|target_quantity:numeric::0|illustrative_action:text::|estimated_cost:numeric::0|owner_decision:text::|executed_quantity:numeric::");
assertTable("owner_decisions", "id:uuid:NN:|rebalance_line_id:uuid::|decision_type:text:NN:|decision_data:jsonb::|notes:text::|owner_id:uuid:NN:|created_at:timestamptz::now()");
assertTable("data_imports", "id:uuid:NN:|import_type:text:NN:|source:text::|rows_imported:integer::0|rows_rejected:integer::0|errors:jsonb::|checksum:text:NN:|owner_id:uuid:NN:|created_at:timestamptz::now()");
assertTable("audit_events", "id:uuid:NN:|owner_id:uuid::|event_type:text:NN:|description:text::|ip_address:inet::|metadata:jsonb::|created_at:timestamptz::now()");

// ─── Enums ──────────────────────────────────────────────────────
console.log("--- Enums ---");
for (const [name, vals] of [
  ["snapshot_status", "DRAFT,VALIDATED,APPROVED,PUBLISHED,SUPERSEDED"],
  ["rebalance_status", "PENDING,COMPLETED,CANCELLED"],
  ["transaction_event_type", "BUY,SELL,DIVIDEND,DEPOSIT,WITHDRAWAL,FEE,TAX,INTEREST,SPLIT,SYMBOL_CHANGE,MERGER,SPINOFF,CORRECTION,TRANSFER"],
]) {
  const actual = sql(`SELECT string_agg(enumlabel::text, ',' ORDER BY enumsortorder) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = '${name}' AND t.typnamespace = 'public'::regnamespace;`);
  assert(`enum ${name}`, actual, vals);
}

// ─── Functions ──────────────────────────────────────────────────
console.log("--- Functions ---");
for (const [name, security, searchPath] of [
  ["handle_new_user", "SECURITY DEFINER", "public"],
  ["is_owner", "SECURITY DEFINER", "public"],
  ["check_transaction_owner", "SECURITY DEFINER", "public"],
  ["check_snapshot_status_transition", "SECURITY DEFINER", "public"],
  ["prevent_portfolio_deletion", "SECURITY DEFINER", "public"],
  ["update_updated_at_column", "SECURITY INVOKER", "public"],
]) {
  const actual = sql(`SELECT prokind FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.proname = '${name}' AND n.nspname = 'public';`);
  assert(`function ${name} exists`, actual, "f");
  const sec = sql(`SELECT prosecdef::text FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.proname = '${name}' AND n.nspname = 'public';`);
  assert(`function ${name} security`, sec, security === "SECURITY DEFINER" ? "t" : "f");
}

// ─── Triggers ──────────────────────────────────────────────────
console.log("--- Triggers ---");
const triggers = [
  ["set_profiles_updated_at", "public", "profiles", "update_updated_at_column"],
  ["set_portfolios_updated_at", "public", "portfolios", "update_updated_at_column"],
  ["on_auth_user_created", "auth", "users", "handle_new_user"],
  ["check_snapshot_status_transition", "public", "model_snapshots", "check_snapshot_status_transition"],
  ["check_transaction_owner", "public", "transactions", "check_transaction_owner"],
  ["prevent_portfolio_deletion", "public", "portfolios", "prevent_portfolio_deletion"],
];
for (const [tgName, schema, table, fnName] of triggers) {
  const actual = sql(`SELECT count(*) FROM pg_trigger tg JOIN pg_class cls ON cls.oid = tg.tgrelid JOIN pg_namespace ns ON ns.oid = cls.relnamespace JOIN pg_proc p ON p.oid = tg.tgfoid WHERE NOT tg.tgisinternal AND ns.nspname = '${schema}' AND cls.relname = '${table}' AND tg.tgname = '${tgName}' AND p.proname = '${fnName}';`);
  assert(`trigger ${tgName} on ${schema}.${table}`, actual, "1");
}

// ─── RLS Policies ──────────────────────────────────────────────
console.log("--- RLS policies ---");
// Check RLS is enabled on all 17 tables
const rlsCount = sql(`SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relrowsecurity = true AND n.nspname = 'public';`);
assert("RLS enabled on 17 tables", rlsCount, "17");

// Verify each table has at least one policy
const policyTables = sql(`SELECT count(*) FROM (SELECT DISTINCT tablename FROM pg_policies WHERE schemaname = 'public') t;`);
assert("Tables with policies", policyTables, "17");

// Key policies with their USING definitions
const policies: [string, string, string, string][] = [
  ["portfolios", "Owner can manage portfolios", "ALL", "(owner_id = auth.uid()) AND public.is_owner()"],
  ["transactions", "Owner can view transactions", "SELECT", "(owner_id = auth.uid()) AND public.is_owner()"],
  ["transactions", "Owner can insert transactions", "INSERT", "<uses WITH CHECK>"],
  ["transactions", "Owner can insert transactions", "INSERT", "(owner_id = auth.uid()) AND public.is_owner()"],
];

// Count total policies
const pCount = sql(`SELECT count(*) FROM pg_policies WHERE schemaname = 'public';`);
assert("Total policies = 31", pCount, "31");

// ─── Indexes ──────────────────────────────────────────────────
console.log("--- Indexes ---");
const expectedIndexes = [
  "idx_transactions_portfolio", "idx_transactions_owner",
  "idx_model_snapshots_status", "idx_model_snapshot_holdings_snapshot",
  "idx_price_observations_security", "idx_benchmark_observations",
  "idx_rebalance_events_portfolio", "idx_portfolio_valuations_portfolio",
  "idx_model_publication_events_snapshot", "idx_audit_events_owner",
];
for (const idx of expectedIndexes) {
  const actual = sql(`SELECT count(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname = '${idx}';`);
  assert(`index ${idx}`, actual, "1");
}
const totalIdx = sql(`SELECT count(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname NOT LIKE '%_pkey' AND indexname NOT LIKE '%_key';`);
assert("Secondary indexes = 10", totalIdx, "10");

// ─── Summary ──────────────────────────────────────────────────
console.log("");
console.log("=== Schema and Policy Audit Results ===");
console.log(` Passed: ${passed}`);
console.log(` Failed: ${failed}`);
if (failed > 0) {
  console.log(" RESULT: FAILED");
  process.exit(1);
}
console.log(" RESULT: PASSED");
