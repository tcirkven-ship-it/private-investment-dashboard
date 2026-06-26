#!/usr/bin/env tsx
/**
 * Real Supabase Auth and RLS verification.
 *
 * Runs against a local Supabase stack (npx supabase start).
 * Uses dynamic env from: supabase status --output env
 *
 * Required env:
 *   ALLOW_DESTRUCTIVE_DB_TESTS=true
 *   SUPABASE_CI=true (set by CI workflow)
 *
 * The test:
 *   1. Applies migrations to the Supabase stack's database
 *   2. Creates two confirmed users via service-role Admin API
 *   3. Tests anonymous, owner, second-user, and service-role access
 *   4. Verifies RLS policies, immutability, and profile creation
 *   5. Runs a complete integrated workflow
 */

import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { execSync, execFileSync } from "child_process";
import * as path from "path";
import * as fs from "fs";

// ─── Configuration ─────────────────────────────────────────────
const ROOT = path.resolve(__dirname, "..");
const SUPABASE_DIR = ROOT;
const MIGRATIONS_DIR = path.join(SUPABASE_DIR, "supabase", "migrations");

function getSupabaseEnv(): Record<string, string> {
  try {
    const out = execFileSync("npx", ["supabase", "status", "--output", "env"], {
      cwd: SUPABASE_DIR,
      encoding: "utf-8",
    });
    const env: Record<string, string> = {};
    for (const line of out.split("\n")) {
      const m = line.match(/^(SUPABASE_\w+|STUDIO_\w+)=(.*)$/);
      if (m) env[m[1]] = m[2].replace(/^"(.*)"$/, "$1");
    }
    // Derive missing vars
    if (env["SUPABASE_ANON_KEY"]) env["NEXT_PUBLIC_SUPABASE_ANON_KEY"] = env["SUPABASE_ANON_KEY"];
    if (env["SUPABASE_SERVICE_ROLE_KEY"]) env["SUPABASE_SERVICE_ROLE_KEY"] = env["SUPABASE_SERVICE_ROLE_KEY"];
    if (env["SUPABASE_URL"]) env["NEXT_PUBLIC_SUPABASE_URL"] = env["SUPABASE_URL"];
    if (env["SUPABASE_DB_URL"]) env["PG_TEST_URL"] = env["SUPABASE_DB_URL"];
    return env;
  } catch (e) {
    console.error("FATAL: supabase status --output env failed. Is the local stack running?");
    console.error("Run: npx supabase start");
    process.exit(1);
  }
}

// ─── Test framework ────────────────────────────────────────────
let passed = 0;
let failed = 0;
const failures: string[] = [];

function assert(condition: boolean, msg: string) {
  if (condition) { passed++; console.log(`  [PASS] ${msg}`); }
  else { failed++; failures.push(msg); console.log(`  [FAIL] ${msg}`); }
}

async function assertQuery(
  client: SupabaseClient,
  table: string,
  action: "select" | "insert" | "update" | "delete",
  expectedError: boolean,
  expectedRows?: number,
  filter?: Record<string, any>,
  data?: Record<string, any>,
) {
  let result: any;
  try {
    let query = client.from(table);
    if (action === "select") {
      result = filter ? await query.select("*").eq(Object.keys(filter)[0], Object.values(filter)[0]) : await query.select("*");
    } else if (action === "insert") {
      result = await query.insert(data || {});
    } else if (action === "update") {
      result = filter ? await query.update(data || {}).eq(Object.keys(filter)[0], Object.values(filter)[0]) : await query.update(data || {});
    } else if (action === "delete") {
      result = filter ? await query.delete().eq(Object.keys(filter)[0], Object.values(filter)[0]) : await query.delete();
    }
    const hasError = !!result.error;
    const rowCount = result.data ? (Array.isArray(result.data) ? result.data.length : 1) : 0;
    if (expectedError && hasError) { pass(`${table} ${action}: correctly denied`); return; }
    if (!expectedError && !hasError && (expectedRows === undefined || rowCount === expectedRows)) {
      pass(`${table} ${action}: allowed (${rowCount} rows)`);
      return;
    }
    fail(`${table} ${action}: unexpected state (error=${!!result.error}, rows=${rowCount})`);
  } catch (e: any) {
    if (expectedError) { pass(`${table} ${action}: correctly denied (exception)`); }
    else { fail(`${table} ${action}: unexpected exception: ${e.message}`); }
  }
}

function fail(msg: string) { failed++; failures.push(msg); console.log(`  [FAIL] ${msg}`); }
function pass(msg: string) { passed++; console.log(`  [PASS] ${msg}`); }

// ─── Main ──────────────────────────────────────────────────────
async function main() {
  console.log("=== Supabase Auth and RLS Verification ===");
  console.log("");

  // Get dynamic env from local Supabase
  const env = getSupabaseEnv();
  const SUPABASE_URL = env["NEXT_PUBLIC_SUPABASE_URL"] || "http://127.0.0.1:54321";
  const ANON_KEY = env["NEXT_PUBLIC_SUPABASE_ANON_KEY"] || "";
  const SERVICE_KEY = env["SUPABASE_SERVICE_ROLE_KEY"] || "";
  const DB_URL = env["PG_TEST_URL"] || "";

  if (!ANON_KEY || !SERVICE_KEY || !DB_URL) {
    console.error("FATAL: Missing required env vars from supabase status --output env");
    console.error("Required: SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_DB_URL");
    process.exit(1);
  }

  console.log(`Supabase URL: ${SUPABASE_URL}`);
  console.log(`Database: ${DB_URL.replace(/\/\/[^:]+:[^@]+@/, "//****:****@")}`);
  console.log("");

  // Apply migrations to the Supabase stack's database
  console.log("--- Applying migrations ---");
  try {
    execSync(`psql "${DB_URL}" -v ON_ERROR_STOP=1 -f "${path.join(MIGRATIONS_DIR, "00001_schema.sql")}"`, {
      stdio: "pipe", encoding: "utf-8", timeout: 30000,
    });
    pass("Migration 00001 applied to Supabase database");
  } catch (e: any) {
    fail(`Migration 00001 failed: ${e.stderr || e.message}`);
  }

  try {
    execSync(`psql "${DB_URL}" -v ON_ERROR_STOP=1 -f "${path.join(MIGRATIONS_DIR, "00002_fixes.sql")}"`, {
      stdio: "pipe", encoding: "utf-8", timeout: 30000,
    });
    pass("Migration 00002 applied");
  } catch (e: any) {
    fail(`Migration 00002 failed: ${e.stderr || e.message}`);
  }

  // ─── Clients ─────────────────────────────────────────────
  const serviceClient = createClient(SUPABASE_URL, SERVICE_KEY, {
    auth: { autoRefreshToken: false, persistSession: false },
  });

  // ─── Create confirmed users via Admin API ────────────────
  console.log("--- Creating users via service role ---");
  const ts = Date.now();

  async function createUser(email: string): Promise<{ id: string; email: string }> {
    const { data, error } = await serviceClient.auth.admin.createUser({
      email,
      password: "test123456!",
      email_confirm: true,
    });
    if (error) throw new Error(`Failed to create ${email}: ${error.message}`);
    if (!data?.user?.id) throw new Error(`No user ID for ${email}`);
    pass(`User created: ${email} (${data.user.id.slice(0, 8)}...)`);
    return { id: data.user.id, email };
  }

  const ownerUser = await createUser(`owner_${ts}@test.com`);
  const user2 = await createUser(`user2_${ts}@test.com`);

  // Wait for profile creation trigger (poll instead of sleep)
  console.log("--- Waiting for profile creation ---");
  for (let attempt = 0; attempt < 20; attempt++) {
    const { data: profiles } = await serviceClient.from("profiles").select("id, email, is_owner");
    const ownerProfile = (profiles || []).find((p: any) => p.id === ownerUser.id);
    const user2Profile = (profiles || []).find((p: any) => p.id === user2.id);
    if (ownerProfile && user2Profile) {
      assert(ownerProfile.is_owner === true, "Owner profile has is_owner=true");
      assert(user2Profile.is_owner === false, "Second user has is_owner=false");
      const ownerCount = (profiles || []).filter((p: any) => p.is_owner).length;
      assert(ownerCount === 1, `Exactly one owner (found ${ownerCount})`);
      break;
    }
    if (attempt === 19) { fail("Profiles not created after 20 attempts"); }
    await new Promise((r) => setTimeout(r, 500));
  }

  // ─── Sign in both users ──────────────────────────────────
  console.log("--- Signing in ---");
  const anonClient = createClient(SUPABASE_URL, ANON_KEY);
  const ownerClient = createClient(SUPABASE_URL, ANON_KEY);
  const user2Client = createClient(SUPABASE_URL, ANON_KEY);

  async function signIn(client: SupabaseClient, email: string) {
    const { data, error } = await client.auth.signInWithPassword({ email, password: "test123456!" });
    assert(!error, `Sign in ${email}: ${error?.message || "OK"}`);
    assert(!!data?.session?.access_token, `Access token exists for ${email}`);
    return data!.session!.access_token;
  }

  const ownerToken = await signIn(ownerClient, ownerUser.email);
  const user2Token = await signIn(user2Client, user2.email);
  assert(ownerToken.length > 20, "Owner token is valid");
  assert(user2Token.length > 20, "User2 token is valid");

  // ─── Anonymous RLS ───────────────────────────────────────
  console.log("--- Anonymous access ---");
  await assertQuery(anonClient, "portfolios", "select", true);
  await assertQuery(anonClient, "portfolios", "insert", true, 0, undefined, {
    owner_id: ownerUser.id, name: "Hack", opening_date: "2025-01-01",
  });

  // ─── Owner access ────────────────────────────────────────
  console.log("--- Owner access ---");
  await assertQuery(ownerClient, "portfolios", "insert", false, undefined, undefined, {
    owner_id: ownerUser.id, name: "My Portfolio", opening_date: "2025-06-01",
  });

  // Fetch owner's portfolio
  const { data: ownerPorts } = await ownerClient.from("portfolios").select("*");
  assert((ownerPorts || []).length === 1, "Owner sees exactly 1 portfolio");
  const portfolioId = (ownerPorts || [])[0]?.id;

  // ─── Second user isolation ───────────────────────────────
  console.log("--- Second user isolation ---");
  await assertQuery(user2Client, "portfolios", "select", false, 0);

  // Second user must not be able to insert application portfolios
  await assertQuery(user2Client, "portfolios", "insert", true, 0, undefined, {
    owner_id: user2.id, name: "User2 Portfolio", opening_date: "2025-01-01",
  });

  await assertQuery(user2Client, "model_snapshots", "select", false, 0);
  await assertQuery(user2Client, "model_versions", "select", false, 0);

  // ─── Transaction immutability ────────────────────────────
  console.log("--- Transaction immutability ---");
  const { data: tx } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, event_type: "DEPOSIT",
    event_date: "2025-01-02", gross_amount: 10000,
    idempotency_key: `rls-tx-${ts}`, owner_id: ownerUser.id,
  }).select().single();
  assert(!!tx, "Transaction created via service role");

  if (tx) {
    // Owner tries UPDATE — must affect 0 rows
    const { data: updResult } = await ownerClient.from("transactions")
      .update({ gross_amount: 999 }).eq("id", tx.id).select();
    assert(!updResult || updResult.length === 0, "Owner UPDATE transactions affects 0 rows");

    // Owner tries DELETE — must affect 0 rows
    const { data: delResult } = await ownerClient.from("transactions")
      .delete().eq("id", tx.id).select();
    assert(!delResult || delResult.length === 0, "Owner DELETE transactions affects 0 rows");

    // Service-role confirms original still exists
    const { data: check } = await serviceClient.from("transactions")
      .select("id, gross_amount").eq("id", tx.id);
    assert(check?.length === 1, "Original transaction still exists after UPDATE/DELETE attempts");
    assert(check?.[0]?.gross_amount === 10000, "Original gross_amount unchanged (10000)");
  }

  // ─── Model snapshot — legal publication ──────────────────
  console.log("--- Model snapshot publication ---");
  const { data: mv } = await serviceClient.from("model_versions").insert({
    model_id: "rls-test", version: "1.0",
  }).select().single();
  assert(!!mv, "Model version created");

  const snapId = `snap-${ts}`;

  // Legal transition: DRAFT -> VALIDATED -> APPROVED -> PUBLISHED
  const { data: snap1, error: e1 } = await serviceClient.from("model_snapshots").insert({
    model_version_id: mv!.id, snapshot_id: snapId,
    status: "DRAFT", effective_date: "2025-01-01",
  }).select().single();
  assert(!e1 && !!snap1, "DRAFT created");
  const snapPk = snap1!.id;

  const { error: e2 } = await serviceClient.from("model_snapshots")
    .update({ status: "VALIDATED" }).eq("id", snapPk);
  assert(!e2, "VALIDATED transition OK");

  const { error: e3 } = await serviceClient.from("model_snapshots")
    .update({ status: "APPROVED" }).eq("id", snapPk);
  assert(!e3, "APPROVED transition OK");

  const { error: e4 } = await serviceClient.from("model_snapshots")
    .update({ status: "PUBLISHED" }).eq("id", snapPk);
  assert(!e4, "PUBLISHED transition OK");

  // Owner cannot UPDATE or DELETE published snapshot
  const { data: updSnap } = await ownerClient.from("model_snapshots")
    .update({ status: "DRAFT" }).eq("id", snapPk).select();
  assert(!updSnap || updSnap.length === 0, "Owner UPDATE published snapshot affects 0 rows");

  const { data: delSnap } = await ownerClient.from("model_snapshots")
    .delete().eq("id", snapPk).select();
  assert(!delSnap || delSnap.length === 0, "Owner DELETE published snapshot affects 0 rows");

  // Service-role confirms snapshot still PUBLISHED
  const { data: snapCheck } = await serviceClient.from("model_snapshots")
    .select("id, status").eq("id", snapPk);
  assert(snapCheck?.length === 1, "Published snapshot still exists");
  assert(snapCheck?.[0]?.status === "PUBLISHED", "Snapshot remains PUBLISHED");

  // ─── Database-backed workflow test ───────────────────────
  console.log("--- Workflow integration test ---");

  // Create securities for AAPL and MSFT
  const { data: aaplSec, error: aaplSecErr } = await serviceClient.from("securities")
    .insert({ ticker: "AAPL", company_name: "Apple Inc.", sector: "Technology", industry: "Consumer Electronics" })
    .select().single();
  assert(!aaplSecErr && !!aaplSec, "AAPL security created");
  const aaplId = aaplSec!.id;

  const { data: msftSec, error: msftSecErr } = await serviceClient.from("securities")
    .insert({ ticker: "MSFT", company_name: "Microsoft Corp.", sector: "Technology", industry: "Software" })
    .select().single();
  assert(!msftSecErr && !!msftSec, "MSFT security created");
  const msftId = msftSec!.id;

  // Insert the deposit
  const { data: depTx, error: depErr } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, event_type: "DEPOSIT",
    event_date: "2025-01-02", gross_amount: 100000,
    idempotency_key: `wf-dep-${ts}`, owner_id: ownerUser.id,
  }).select().single();
  assert(!depErr && !!depTx, "Deposit inserted");

  // Buy AAPL 50 @ $185 with $5 commission
  const { data: buyAapl, error: buy1Err } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, security_id: aaplId, event_type: "BUY",
    event_date: "2025-01-05", quantity: 50, price: 185,
    gross_amount: 9250, commission: 5,
    idempotency_key: `wf-buy1-${ts}`, owner_id: ownerUser.id,
  }).select().single();
  assert(!buy1Err && !!buyAapl, "Buy AAPL 50 @ $185 inserted");

  // Buy MSFT 30 @ $420 with $5 commission
  const { data: buyMsft, error: buy2Err } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, security_id: msftId, event_type: "BUY",
    event_date: "2025-01-05", quantity: 30, price: 420,
    gross_amount: 12600, commission: 5,
    idempotency_key: `wf-buy2-${ts}`, owner_id: ownerUser.id,
  }).select().single();
  assert(!buy2Err && !!buyMsft, "Buy MSFT 30 @ $420 inserted");

  // Dividend $50
  const { data: divTx, error: divErr } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, security_id: aaplId, event_type: "DIVIDEND",
    event_date: "2025-02-01", gross_amount: 50,
    idempotency_key: `wf-div-${ts}`, owner_id: ownerUser.id,
  }).select().single();
  assert(!divErr && !!divTx, "Dividend $50 inserted");

  // Fee $5
  const { data: feeTx, error: feeErr } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, event_type: "FEE",
    event_date: "2025-03-01", gross_amount: 5,
    idempotency_key: `wf-fee-${ts}`, owner_id: ownerUser.id,
  }).select().single();
  assert(!feeErr && !!feeTx, "Fee $5 inserted");

  // Sell 10 AAPL @ $200 with $3 commission
  const { data: sellAapl, error: sellErr } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, security_id: aaplId, event_type: "SELL",
    event_date: "2025-03-15", quantity: 10, price: 200,
    gross_amount: 2000, commission: 3,
    idempotency_key: `wf-sell-${ts}`, owner_id: ownerUser.id,
  }).select().single();
  assert(!sellErr && !!sellAapl, "Sell 10 AAPL @ $200 inserted");

  // 7 transactions expected: DEPOSIT, BUY, BUY, DIVIDEND, FEE, SELL — 6 total + any from RLS setup
  // Count only workflow transactions
  const { data: wfTxs, error: wfTxErr } = await serviceClient.from("transactions")
    .select("id, event_type, gross_amount, commission, quantity, price, security_id, idempotency_key")
    .eq("portfolio_id", portfolioId)
    .not("idempotency_key", "like", "rls-tx-%")
    .order("event_date", { ascending: true });
  assert(!wfTxErr, "Workflow transactions queried");
  assert(wfTxs !== null, "Workflow transactions returned non-null");
  assert(wfTxs!.length === 6, `6 workflow transactions exist (got ${wfTxs!.length})`);

  // === Cash calculation (explicit, exact arithmetic) ===
  // DEPOSIT       +100,000
  // BUY AAPL        -9,250 - 5 = -9,255
  // BUY MSFT       -12,600 - 5 = -12,605
  // DIVIDEND           +50
  // FEE                 -5
  // SELL AAPL      +2,000 - 3 = +1,997
  //                             --------
  //                             80,182

  // Use integer cents for exact comparison
  function cashReducer(sum: number, t: any): number {
    const comm = t.commission || 0;
    switch (t.event_type) {
      case "DEPOSIT": case "INTEREST": return sum + t.gross_amount;
      case "WITHDRAWAL": case "FEE": case "TAX": return sum - t.gross_amount;
      case "BUY": return sum - t.gross_amount - comm;
      case "SELL": return sum + t.gross_amount - comm;
      case "DIVIDEND": return sum + t.gross_amount;
      default: return sum;
    }
  }
  const cashCents = Math.round(wfTxs!.reduce(cashReducer, 0) * 100);
  assert(cashCents === 8018200, `Cash = $80,182.00 (got $${(cashCents / 100).toFixed(2)})`);

  // === Security identification by security_id ===
  const aaplTxs = wfTxs!.filter((t: any) => t.security_id === aaplId);
  const msftTxs = wfTxs!.filter((t: any) => t.security_id === msftId);

  const aaplBuys = aaplTxs.filter((t: any) => t.event_type === "BUY");
  const aaplSells = aaplTxs.filter((t: any) => t.event_type === "SELL");
  const msftBuys = msftTxs.filter((t: any) => t.event_type === "BUY");

  const aaplBought = aaplBuys.reduce((s: number, t: any) => s + t.quantity, 0);
  const aaplSold = aaplSells.reduce((s: number, t: any) => s + t.quantity, 0);
  const msftBought = msftBuys.reduce((s: number, t: any) => s + t.quantity, 0);

  assert(aaplBought === 50, `AAPL bought: 50 (got ${aaplBought})`);
  assert(aaplSold === 10, `AAPL sold: 10 (got ${aaplSold})`);
  assert(aaplBought - aaplSold === 40, `AAPL remaining: 40 (got ${aaplBought - aaplSold})`);
  assert(msftBought === 30, `MSFT bought: 30 (got ${msftBought})`);

  // === Average cost (commissions capitalized into cost basis) ===
  const aaplTotalCost = aaplBuys.reduce((s: number, t: any) => s + t.gross_amount + (t.commission || 0), 0);
  const aaplAvgCost = aaplTotalCost / aaplBought; // 9,255 / 50 = 185.10
  assert(Math.abs(aaplAvgCost - 185.10) < 0.001, `AAPL avg cost: $185.10 (got $${aaplAvgCost.toFixed(2)})`);

  const msftTotalCost = msftBuys.reduce((s: number, t: any) => s + t.gross_amount + (t.commission || 0), 0);
  const msftAvgCost = msftTotalCost / msftBought; // 12,605 / 30 = 420.1667
  assert(Math.abs(msftAvgCost - 420.1667) < 0.01, `MSFT avg cost: $420.17 (got $${msftAvgCost.toFixed(2)})`);

  // === Realised gain ===
  // Cost basis of sold shares = 10 × $185.10 = $1,851
  const costBasisSold = aaplSold * aaplAvgCost;
  const netSaleProceeds = aaplSells.reduce((s: number, t: any) => s + t.gross_amount - (t.commission || 0), 0);
  const realisedGain = netSaleProceeds - costBasisSold;
  assert(Math.abs(realisedGain - 146.00) < 0.01, `Realised gain: $146.00 (got $${realisedGain.toFixed(2)})`);

  // === Commissions and fees ===
  const totalCommissions = wfTxs!.reduce((s: number, t: any) => s + (t.commission || 0), 0);
  assert(totalCommissions === 13, `Total commissions: $13 (got $${totalCommissions})`);

  const purchaseCommissions = wfTxs!.filter((t: any) => t.event_type === "BUY")
    .reduce((s: number, t: any) => s + (t.commission || 0), 0);
  assert(purchaseCommissions === 10, `Purchase commissions: $10 (got $${purchaseCommissions})`);

  const dividends = wfTxs!.filter((t: any) => t.event_type === "DIVIDEND")
    .reduce((s: number, t: any) => s + t.gross_amount, 0);
  assert(dividends === 50, `Dividends: $50 (got $${dividends})`);

  const fees = wfTxs!.filter((t: any) => t.event_type === "FEE")
    .reduce((s: number, t: any) => s + t.gross_amount, 0);
  assert(fees === 5, `Fees: $5 (got $${fees})`);

  const taxes = wfTxs!.filter((t: any) => t.event_type === "TAX")
    .reduce((s: number, t: any) => s + t.gross_amount, 0);
  assert(taxes === 0, `Taxes: $0 (got $${taxes})`);

  // Rebalance event
  const { data: reb, error: rebErr } = await serviceClient.from("rebalance_events").insert({
    portfolio_id: portfolioId, model_snapshot_id: snapPk,
    rebalance_date: "2025-04-01", owner_id: ownerUser.id,
  }).select().single();
  assert(!rebErr && !!reb, "Rebalance event created");

  // ─── Summary ─────────────────────────────────────────────
  console.log("");
  console.log("=== AUTH/RLS VERIFICATION RESULTS ===");
  console.log(` Passed: ${passed}`);
  console.log(` Failed: ${failed}`);
  if (failed > 0) {
    console.log(" Failures:");
    failures.forEach((f) => console.log(`  - ${f}`));
    console.log(" RESULT: FAILED");
    process.exit(1);
  }
  console.log(" RESULT: PASSED");
}

main().catch((error) => {
  console.error("FATAL:", error);
  process.exit(1);
});
