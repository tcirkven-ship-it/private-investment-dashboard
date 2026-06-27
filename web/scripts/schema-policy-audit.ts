#!/usr/bin/env tsx
/**
 * Schema and Policy Definition Audit
 * Normalizes harmless representation differences before comparison.
 * Exits nonzero on any meaningful mismatch.
 */

import { execSync } from "child_process";

const DB_URL = process.env.PG_TEST_URL || "";
if (!DB_URL) { console.error("FATAL: PG_TEST_URL required"); process.exit(1); }

let passed = 0;
let failed = 0;
const failures: string[] = [];

function sql(query: string): string {
  return execSync(
    `psql "${DB_URL}" -v ON_ERROR_STOP=1 -t -A -c "${query.replace(/"/g, '\\"')}"`,
    { encoding: "utf-8", timeout: 10000 }
  ).trim();
}

function assert(label: string, actual: string, expected: string) {
  if (actual === expected) { passed++; }
  else { failed++; failures.push(`${label}: expected=[${expected}] actual=[${actual}]`); }
}

// Normalize helpers
function normDefault(d: string | null): string {
  if (!d || d === "") return "";
  // Handle common patterns: 'textvalue'::text -> 'textvalue', gen_random_uuid() -> gen_random_uuid()
  let v = d.replace(/::\w+(\[\])?/g, ""); // remove ::text, ::snapshot_status, etc
  v = v.replace(/^'(.*)'$/, "$1"); // unwrap quotes for simple strings
  return v;
}

function normDataType(col: string, dt: string, udt: string): string {
  // Use udt_name for enums
  if (["snapshot_status", "rebalance_status", "transaction_types"].includes(udt)) return udt;
  // Canonicalize timestamptz
  if (dt === "timestamp with time zone") return "timestamptz";
  if (dt === "timestamp without time zone") return "timestamp";
  return dt;
}

function normBool(b: string): string {
  if (b === "t") return "true";
  if (b === "f") return "false";
  return b;
}

interface ColumnDef {
  column_name: string;
  data_type: string;
  udt_name: string;
  is_nullable: string;
  column_default: string | null;
  [key: string]: unknown;
}

function colKey(c: ColumnDef): string {
  const dt = normDataType(c.column_name, c.data_type, c.udt_name);
  const nn = c.is_nullable === "NO" ? "NN" : "";
  const def = normDefault(c.column_default);
  return `${c.column_name}:${dt}:${nn}:${def}`;
}

// Build expected column definitions
const EXPECTED_TABLES: Record<string, string> = {
  profiles: "id:uuid:NN:|email:text:NN:|display_name:text::|totp_enabled:boolean::false|is_owner:boolean::false|created_at:timestamptz::now()|updated_at:timestamptz::now()",
  app_settings: "key:text:NN:|value:jsonb:NN:|updated_at:timestamptz::now()",
  securities: "id:uuid:NN:gen_random_uuid()|ticker:text:NN:|company_name:text::|sector:text::|industry:text::|asset_class:text::|is_active:boolean::true|data_source:text::yfinance|superseded_by:uuid::|created_at:timestamptz::now()",
  model_versions: "id:uuid:NN:gen_random_uuid()|model_id:text:NN:|version:text:NN:|description:text::|config_hash:text::|formula_version:text::|created_at:timestamptz::now()",
  model_snapshots: "id:uuid:NN:gen_random_uuid()|model_version_id:uuid:NN:|snapshot_id:text:NN:|status:snapshot_status:NN:DRAFT|effective_date:date:NN:|decision_timestamp:timestamptz::|execution_convention:text::next_valid_session_close|universe_screened:integer::|eligible_count:integer::|valid_score_count:integer::|integrity_hash:text::|source_commit:text::|warnings:jsonb::|created_at:timestamptz::now()|published_at:timestamptz::|superseded_at:timestamptz::",
  model_snapshot_holdings: "id:uuid:NN:gen_random_uuid()|snapshot_id:uuid:NN:|security_id:uuid:NN:|rank:integer:NN:|target_weight:numeric:NN:|b2_score:numeric::|quality_percentile:numeric::|quality_components_ok:integer::0|prior_rank:integer::|change_from_prior:text::|data_quality_flags:ARRAY::|inclusion_reason:text::",
  model_publication_events: "id:uuid:NN:gen_random_uuid()|snapshot_id:uuid:NN:|from_status:text::|to_status:text:NN:|changed_by:uuid::|reason:text::|created_at:timestamptz::now()",
  portfolios: "id:uuid:NN:gen_random_uuid()|owner_id:uuid:NN:|name:text:NN:|currency:text::USD|opening_date:date:NN:|starting_cash:numeric::|benchmark_ticker:text::|notes:text::|is_archived:boolean::false|created_at:timestamptz::now()|updated_at:timestamptz::now()",
  transactions: "id:uuid:NN:gen_random_uuid()|portfolio_id:uuid:NN:|security_id:uuid::|event_type:transaction_types:NN:|event_date:date:NN:|quantity:numeric::|price:numeric::|gross_amount:numeric:NN:|commission:numeric::0|tax:numeric::0|fx_rate:numeric::|notes:text::|idempotency_key:text:NN:|corrected_by:uuid::|owner_id:uuid:NN:|created_at:timestamptz::now()",
  price_observations: "id:uuid:NN:gen_random_uuid()|security_id:uuid:NN:|observation_date:date:NN:|close:numeric::|adj_close:numeric::|volume:bigint::|source:text::yfinance",
  benchmark_observations: "id:uuid:NN:gen_random_uuid()|ticker:text:NN:|observation_date:date:NN:|price:numeric::|total_return_index:numeric::",
  portfolio_valuations: "id:uuid:NN:gen_random_uuid()|portfolio_id:uuid:NN:|valuation_date:date:NN:|total_value:numeric:NN:|cash_balance:numeric::0|total_deposits:numeric::0|total_withdrawals:numeric::0",
  rebalance_events: "id:uuid:NN:gen_random_uuid()|portfolio_id:uuid:NN:|model_snapshot_id:uuid:NN:|rebalance_date:date:NN:|status:rebalance_status:NN:PENDING|estimated_cost:numeric::|completed_at:timestamptz::|owner_id:uuid:NN:",
  rebalance_lines: "id:uuid:NN:gen_random_uuid()|rebalance_event_id:uuid:NN:|security_id:uuid:NN:|current_quantity:numeric::0|target_quantity:numeric::0|illustrative_action:text::|estimated_cost:numeric::0|owner_decision:text::|executed_quantity:numeric::",
  owner_decisions: "id:uuid:NN:gen_random_uuid()|rebalance_line_id:uuid::|decision_type:text:NN:|decision_data:jsonb::|notes:text::|owner_id:uuid:NN:|created_at:timestamptz::now()",
  data_imports: "id:uuid:NN:gen_random_uuid()|import_type:text:NN:|source:text::|rows_imported:integer::0|rows_rejected:integer::0|errors:jsonb::|checksum:text:NN:|owner_id:uuid:NN:|created_at:timestamptz::now()",
  audit_events: "id:uuid:NN:gen_random_uuid()|owner_id:uuid::|event_type:text:NN:|description:text::|ip_address:inet::|metadata:jsonb::|created_at:timestamptz::now()",
};

console.log("=== Schema and Policy Definition Audit ===");
console.log("");

// ─── Tables and columns ─────────────────────────────────────────
console.log("--- Tables and columns ---");
for (const [table, expected] of Object.entries(EXPECTED_TABLES)) {
  const rows = sql(`SELECT column_name, data_type, udt_name, is_nullable, column_default, ordinal_position FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '${table}' ORDER BY ordinal_position;`);
  const actual = rows.split("\n").filter(Boolean).map((line) => {
    const [name, dt, udt, nullable, def] = line.split("|");
    const type = normDataType(name, dt, udt);
    const nn = nullable === "NO" ? "NN" : "";
    const d = normDefault(def || "");
    return `${name}:${type}:${nn}:${d}`;
  }).join("|");
  assert(`table ${table}`, actual, expected);
}

// ─── Enums ──────────────────────────────────────────────────────
console.log("--- Enums ---");
const ENUMS: [string, string][] = [
  ["snapshot_status", "DRAFT,VALIDATED,APPROVED,PUBLISHED,SUPERSEDED"],
  ["rebalance_status", "PENDING,COMPLETED,CANCELLED"],
  ["transaction_types", "DEPOSIT,WITHDRAWAL,BUY,SELL,DIVIDEND,FEE,TAX,INTEREST,SPLIT,SYMBOL_CHANGE,MERGER,SPINOFF,CORRECTION,TRANSFER"],
];
for (const [name, vals] of ENUMS) {
  const actual = sql(`SELECT string_agg(enumlabel::text, ',' ORDER BY enumsortorder) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = '${name}' AND t.typnamespace = 'public'::regnamespace;`);
  assert(`enum ${name}`, actual, vals);
}

// ─── Functions ──────────────────────────────────────────────────
console.log("--- Functions ---");
const FUNCTIONS: [string, string, string][] = [
  ["handle_new_user", "SECURITY DEFINER", "public"],
  ["is_owner", "SECURITY DEFINER", "public"],
  ["check_transaction_owner", "SECURITY DEFINER", "public"],
  ["check_snapshot_status_transition", "SECURITY DEFINER", "public"],
  ["prevent_portfolio_deletion", "SECURITY DEFINER", "public"],
  ["update_updated_at_column", "SECURITY INVOKER", "public"],
];
for (const [name, security, _sp] of FUNCTIONS) {
  const sec = normBool(sql(`SELECT prosecdef::text FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.proname = '${name}' AND n.nspname = 'public';`));
  assert(`function ${name} security definer`, sec, security === "SECURITY DEFINER" ? "true" : "false");
}

// ─── Triggers ──────────────────────────────────────────────────
console.log("--- Triggers ---");
const TRIGGERS: [string, string, string, string][] = [
  ["set_profiles_updated_at", "public", "profiles", "update_updated_at_column"],
  ["set_portfolios_updated_at", "public", "portfolios", "update_updated_at_column"],
  ["on_auth_user_created", "auth", "users", "handle_new_user"],
  ["check_snapshot_status_transition", "public", "model_snapshots", "check_snapshot_status_transition"],
  ["check_transaction_owner", "public", "transactions", "check_transaction_owner"],
  ["prevent_portfolio_deletion", "public", "portfolios", "prevent_portfolio_deletion"],
];
for (const [tgName, schema, table, fnName] of TRIGGERS) {
  const actual = sql(`SELECT count(*) FROM pg_trigger tg JOIN pg_class cls ON cls.oid = tg.tgrelid JOIN pg_namespace ns ON ns.oid = cls.relnamespace JOIN pg_proc p ON p.oid = tg.tgfoid WHERE NOT tg.tgisinternal AND ns.nspname = '${schema}' AND cls.relname = '${table}' AND tg.tgname = '${tgName}' AND p.proname = '${fnName}';`);
  assert(`trigger ${tgName} on ${schema}.${table}`, actual, "1");
}

// ─── RLS ──────────────────────────────────────────────────────
console.log("--- RLS ---");
const rlsCount = sql(`SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relrowsecurity = true AND n.nspname = 'public';`);
assert("RLS enabled on 17 tables", rlsCount, "17");

const policyTables = sql(`SELECT count(*) FROM (SELECT DISTINCT tablename FROM pg_policies WHERE schemaname = 'public') t;`);
assert("Tables with at least 1 policy", policyTables, "17");

const pCount = sql(`SELECT count(*) FROM pg_policies WHERE schemaname = 'public';`);
assert("Total policies = 31", pCount, "31");

// ─── Indexes ──────────────────────────────────────────────────
console.log("--- Indexes ---");
const INDEXES = [
  "idx_transactions_portfolio", "idx_transactions_owner",
  "idx_model_snapshots_status", "idx_model_snapshot_holdings_snapshot",
  "idx_price_observations_security", "idx_benchmark_observations",
  "idx_rebalance_events_portfolio", "idx_portfolio_valuations_portfolio",
  "idx_model_publication_events_snapshot", "idx_audit_events_owner",
];
for (const idx of INDEXES) {
  const actual = sql(`SELECT count(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname = '${idx}';`);
  assert(`index ${idx}`, actual, "1");
}

// ─── Summary ──────────────────────────────────────────────────
console.log("");
console.log("=== Schema and Policy Audit Results ===");
console.log(` Passed: ${passed}`);
console.log(` Failed: ${failed}`);
if (failures.length > 0) {
  console.log(" Failures:");
  failures.forEach((f) => console.log(`  ${f}`));
  console.log(" RESULT: FAILED");
  process.exit(1);
}
console.log(" RESULT: PASSED");
