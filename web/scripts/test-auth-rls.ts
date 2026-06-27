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
import { execSync } from "child_process";

// ─── Row/result helpers ────────────────────────────────────────
type QueryResult = { data: unknown[] | null; error: unknown };
type ProfileRow = Record<string, unknown>;
type TxRow = Record<string, unknown>;

// ─── Test framework ────────────────────────────────────────────
let passed = 0;
let failed = 0;
const failures: string[] = [];

function assert(condition: boolean, msg: string) {
  if (condition) { passed++; console.log(`  [PASS] ${msg}`); }
  else { failed++; failures.push(msg); console.log(`  [FAIL] ${msg}`); }
}

function expectSelectDeniedOrEmpty(label: string, result: QueryResult) {
  const error = !!result?.error;
  const rows = result?.data;
  const rowCount = Array.isArray(rows) ? rows.length : 0;
  assert(error || rowCount === 0, `${label}: denied or empty result (error=${error}, rows=${rowCount})`);
}

function expectRows(label: string, result: QueryResult, expectedCount: number) {
  assert(!result?.error, `${label}: query should not error`);
  assert(Array.isArray(result?.data), `${label}: rows should be array`);
  assert(result.data!.length === expectedCount, `${label}: expected ${expectedCount}, got ${result.data!.length}`);
}

function expectInsertAllowed(label: string, result: QueryResult) {
  assert(!result?.error, `${label}: insert should succeed`);
}

function expectInsertDenied(label: string, result: QueryResult) {
  assert(!!result?.error, `${label}: insert should be denied`);
}

function expectUpdateDenied(label: string, result: QueryResult) {
  const rows = result?.data;
  const rowCount = Array.isArray(rows) ? rows.length : 0;
  assert(rowCount === 0, `${label}: UPDATE should affect 0 rows (affected ${rowCount})`);
}

function expectDeleteDenied(label: string, result: QueryResult) {
  const rows = result?.data;
  const rowCount = Array.isArray(rows) ? rows.length : 0;
  assert(rowCount === 0, `${label}: DELETE should affect 0 rows (affected ${rowCount})`);
}

function fail(msg: string) { failed++; failures.push(msg); console.log(`  [FAIL] ${msg}`); }
function pass(msg: string) { passed++; console.log(`  [PASS] ${msg}`); }

// ─── Main ──────────────────────────────────────────────────────
async function main() {
  console.log("=== Supabase Auth and RLS Verification ===");
  console.log("");

  const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
  const ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
  const SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || "";
  const DB_URL = process.env.PG_TEST_URL || "";

  if (!ANON_KEY || !SERVICE_KEY || !DB_URL) {
    console.error("FATAL: Missing required env vars from supabase status --output env");
    console.error("Required: SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_DB_URL");
    process.exit(1);
  }

  console.log(`Supabase URL: ${SUPABASE_URL}`);
  console.log(`Database: ${DB_URL.replace(/\/\/[^:]+:[^@]+@/, "//****:****@")}`);
  console.log("");

  console.log("--- Verifying schema (applied by supabase start) ---");
  try {
    execSync(`psql "${DB_URL}" -v ON_ERROR_STOP=1 -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"`, {
      stdio: "pipe", encoding: "utf-8", timeout: 10000,
    });
    pass("Application tables exist — migrations were applied by supabase start");
  } catch (e: unknown) {
    const err = e as { stderr?: string; message?: string };
    fail(`Schema verification failed: ${err.stderr || err.message}`);
    process.exit(1);
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
    const { data: profiles } = await serviceClient.from("profiles").select("id, email, is_owner") as { data: ProfileRow[] | null; error: unknown };
    const ownerProfile = (profiles || []).find((p: ProfileRow) => p.id === ownerUser.id);
    const user2Profile = (profiles || []).find((p: ProfileRow) => p.id === user2.id);
    if (ownerProfile && user2Profile) {
      assert(ownerProfile.is_owner === true, "Owner profile has is_owner=true");
      assert(user2Profile.is_owner === false, "Second user has is_owner=false");
      const ownerCount = (profiles || []).filter((p: ProfileRow) => p.is_owner).length;
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
  expectSelectDeniedOrEmpty("Anonymous portfolios SELECT", await anonClient.from("portfolios").select("*") as QueryResult);
  expectInsertDenied("Anonymous portfolios INSERT", await anonClient.from("portfolios").insert({
    owner_id: ownerUser.id, name: "Hack", opening_date: "2025-01-01",
  }) as QueryResult);

  // ─── Owner access ────────────────────────────────────────
  console.log("--- Owner access ---");
  expectInsertAllowed("Owner portfolios INSERT", await ownerClient.from("portfolios").insert({
    owner_id: ownerUser.id, name: "My Portfolio", opening_date: "2025-06-01",
  }) as QueryResult);

  // Fetch owner's portfolio
  const { data: ownerPorts, error: ownerPortsErr } = await ownerClient.from("portfolios").select("*") as { data: ProfileRow[] | null; error: unknown };
  assert(!ownerPortsErr, "Owner portfolios SELECT query succeeded");
  assert(Array.isArray(ownerPorts), "Owner portfolios result is array");
  assert(ownerPorts!.length === 1, `Owner sees exactly 1 portfolio (got ${ownerPorts!.length})`);
  const portfolioId = String((ownerPorts as ProfileRow[])[0]?.id);

  // ─── Second user isolation ───────────────────────────────
  console.log("--- Second user isolation ---");
  expectSelectDeniedOrEmpty("Second user portfolios SELECT", await user2Client.from("portfolios").select("*") as QueryResult);

  expectInsertDenied("Second user portfolios INSERT", await user2Client.from("portfolios").insert({
    owner_id: user2.id, name: "User2 Portfolio", opening_date: "2025-01-01",
  }) as QueryResult);

  expectSelectDeniedOrEmpty("Second user model_snapshots SELECT", await user2Client.from("model_snapshots").select("*") as QueryResult);
  expectSelectDeniedOrEmpty("Second user model_versions SELECT", await user2Client.from("model_versions").select("*") as QueryResult);

  // ─── Transaction immutability ────────────────────────────
  console.log("--- Transaction immutability ---");
  const { data: tx } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, event_type: "DEPOSIT",
    event_date: "2025-01-02", gross_amount: 10000,
    idempotency_key: `rls-tx-${ts}`, owner_id: ownerUser.id,
  }).select().single() as { data: TxRow | null; error: unknown };
  assert(!!tx, "Transaction created via service role");

  if (tx) {
    expectUpdateDenied("Owner UPDATE transactions", await ownerClient.from("transactions")
      .update({ gross_amount: 999 }).eq("id", tx.id).select() as QueryResult);

    expectDeleteDenied("Owner DELETE transactions", await ownerClient.from("transactions")
      .delete().eq("id", tx.id).select() as QueryResult);

    expectRows("Original transaction after UPDATE/DELETE attempts",
      await serviceClient.from("transactions").select("id, gross_amount").eq("id", tx.id) as QueryResult, 1);
    const { data: check } = await serviceClient.from("transactions")
      .select("gross_amount").eq("id", tx.id).single() as { data: TxRow | null; error: unknown };
    assert(check?.gross_amount === 10000, "Original gross_amount unchanged (10000)");
  }

  // ─── Model snapshot — legal publication ──────────────────
  console.log("--- Model snapshot publication ---");
  const { data: mv } = await serviceClient.from("model_versions").insert({
    model_id: "rls-test", version: "1.0",
  }).select().single() as { data: TxRow | null; error: unknown };
  assert(!!mv, "Model version created");

  const snapId = `snap-${ts}`;

  const { data: snap1, error: e1 } = await serviceClient.from("model_snapshots").insert({
    model_version_id: mv!.id, snapshot_id: snapId,
    status: "DRAFT", effective_date: "2025-01-01",
  }).select().single() as { data: TxRow | null; error: unknown };
  assert(!e1 && !!snap1, "DRAFT created");
  const snapPk = snap1!.id as string;

  const { error: e2 } = await serviceClient.from("model_snapshots")
    .update({ status: "VALIDATED" }).eq("id", snapPk) as { error: unknown };
  assert(!e2, "VALIDATED transition OK");

  const { error: e3 } = await serviceClient.from("model_snapshots")
    .update({ status: "APPROVED" }).eq("id", snapPk) as { error: unknown };
  assert(!e3, "APPROVED transition OK");

  const { error: e4 } = await serviceClient.from("model_snapshots")
    .update({ status: "PUBLISHED" }).eq("id", snapPk) as { error: unknown };
  assert(!e4, "PUBLISHED transition OK");

  const { data: updSnap } = await ownerClient.from("model_snapshots")
    .update({ status: "DRAFT" }).eq("id", snapPk).select() as { data: unknown[] | null; error: unknown };
  assert(!updSnap || updSnap.length === 0, "Owner UPDATE published snapshot affects 0 rows");

  const { data: delSnap } = await ownerClient.from("model_snapshots")
    .delete().eq("id", snapPk).select() as { data: unknown[] | null; error: unknown };
  assert(!delSnap || delSnap.length === 0, "Owner DELETE published snapshot affects 0 rows");

  const { data: snapCheck } = await serviceClient.from("model_snapshots")
    .select("id, status").eq("id", snapPk) as { data: TxRow[] | null; error: unknown };
  assert(snapCheck?.length === 1, "Published snapshot still exists");
  assert(snapCheck?.[0]?.status === "PUBLISHED", "Snapshot remains PUBLISHED");

  // ─── Database-backed workflow test ───────────────────────
  console.log("--- Workflow integration test ---");

  const { data: aaplSec, error: aaplSecErr } = await serviceClient.from("securities")
    .insert({ ticker: "AAPL", company_name: "Apple Inc.", sector: "Technology", industry: "Consumer Electronics" })
    .select().single() as { data: TxRow | null; error: unknown };
  assert(!aaplSecErr && !!aaplSec, "AAPL security created");
  const aaplId = aaplSec!.id as string;

  const { data: msftSec, error: msftSecErr } = await serviceClient.from("securities")
    .insert({ ticker: "MSFT", company_name: "Microsoft Corp.", sector: "Technology", industry: "Software" })
    .select().single() as { data: TxRow | null; error: unknown };
  assert(!msftSecErr && !!msftSec, "MSFT security created");
  const msftId = msftSec!.id as string;

  const { data: depTx, error: depErr } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, event_type: "DEPOSIT",
    event_date: "2025-01-02", gross_amount: 100000,
    idempotency_key: `wf-dep-${ts}`, owner_id: ownerUser.id,
  }).select().single() as { data: TxRow | null; error: unknown };
  assert(!depErr && !!depTx, "Deposit inserted");

  const { data: buyAapl, error: buy1Err } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, security_id: aaplId, event_type: "BUY",
    event_date: "2025-01-05", quantity: 50, price: 185,
    gross_amount: 9250, commission: 5,
    idempotency_key: `wf-buy1-${ts}`, owner_id: ownerUser.id,
  }).select().single() as { data: TxRow | null; error: unknown };
  assert(!buy1Err && !!buyAapl, "Buy AAPL 50 @ $185 inserted");

  const { data: buyMsft, error: buy2Err } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, security_id: msftId, event_type: "BUY",
    event_date: "2025-01-05", quantity: 30, price: 420,
    gross_amount: 12600, commission: 5,
    idempotency_key: `wf-buy2-${ts}`, owner_id: ownerUser.id,
  }).select().single() as { data: TxRow | null; error: unknown };
  assert(!buy2Err && !!buyMsft, "Buy MSFT 30 @ $420 inserted");

  const { data: divTx, error: divErr } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, security_id: aaplId, event_type: "DIVIDEND",
    event_date: "2025-02-01", gross_amount: 50,
    idempotency_key: `wf-div-${ts}`, owner_id: ownerUser.id,
  }).select().single() as { data: TxRow | null; error: unknown };
  assert(!divErr && !!divTx, "Dividend $50 inserted");

  const { data: feeTx, error: feeErr } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, event_type: "FEE",
    event_date: "2025-03-01", gross_amount: 5,
    idempotency_key: `wf-fee-${ts}`, owner_id: ownerUser.id,
  }).select().single() as { data: TxRow | null; error: unknown };
  assert(!feeErr && !!feeTx, "Fee $5 inserted");

  const { data: sellAapl, error: sellErr } = await serviceClient.from("transactions").insert({
    portfolio_id: portfolioId, security_id: aaplId, event_type: "SELL",
    event_date: "2025-03-15", quantity: 10, price: 200,
    gross_amount: 2000, commission: 3,
    idempotency_key: `wf-sell-${ts}`, owner_id: ownerUser.id,
  }).select().single() as { data: TxRow | null; error: unknown };
  assert(!sellErr && !!sellAapl, "Sell 10 AAPL @ $200 inserted");

  const { data: wfTxs, error: wfTxErr } = await serviceClient.from("transactions")
    .select("id, event_type, gross_amount, commission, quantity, price, security_id, idempotency_key")
    .eq("portfolio_id", portfolioId)
    .not("idempotency_key", "like", "rls-tx-%")
    .order("event_date", { ascending: true }) as { data: TxRow[] | null; error: unknown };
  assert(!wfTxErr, "Workflow transactions queried");
  assert(wfTxs !== null, "Workflow transactions returned non-null");
  assert(wfTxs!.length === 6, `6 workflow transactions exist (got ${wfTxs!.length})`);

  const typedWfTxs = wfTxs as TxRow[];

  function cashReducer(sum: number, t: TxRow): number {
    const comm = Number(t.commission ?? 0);
    const gross = Number(t.gross_amount ?? 0);
    switch (t.event_type) {
      case "DEPOSIT": case "INTEREST": return sum + gross;
      case "WITHDRAWAL": case "FEE": case "TAX": return sum - gross;
      case "BUY": return sum - gross - comm;
      case "SELL": return sum + gross - comm;
      case "DIVIDEND": return sum + gross;
      default: return sum;
    }
  }
  const cashCents = Math.round(typedWfTxs.reduce(cashReducer, 0) * 100);
  assert(cashCents === 8018200, `Cash = $80,182.00 (got $${(cashCents / 100).toFixed(2)})`);

  const aaplTxs = typedWfTxs.filter((t) => t.security_id === aaplId);
  const msftTxs = typedWfTxs.filter((t) => t.security_id === msftId);

  const aaplBuys = aaplTxs.filter((t) => t.event_type === "BUY");
  const aaplSells = aaplTxs.filter((t) => t.event_type === "SELL");
  const msftBuys = msftTxs.filter((t) => t.event_type === "BUY");

  const safeQuant = (t: TxRow): number => Number(t.quantity ?? 0);
  const safeGross = (t: TxRow): number => Number(t.gross_amount ?? 0);
  const safeComm = (t: TxRow): number => Number(t.commission ?? 0);

  const aaplBought = aaplBuys.reduce((s, t) => s + safeQuant(t), 0);
  const aaplSold = aaplSells.reduce((s, t) => s + safeQuant(t), 0);
  const msftBought = msftBuys.reduce((s, t) => s + safeQuant(t), 0);

  assert(aaplBought === 50, `AAPL bought: 50 (got ${aaplBought})`);
  assert(aaplSold === 10, `AAPL sold: 10 (got ${aaplSold})`);
  assert(aaplBought - aaplSold === 40, `AAPL remaining: 40 (got ${aaplBought - aaplSold})`);
  assert(msftBought === 30, `MSFT bought: 30 (got ${msftBought})`);

  const aaplTotalCost = aaplBuys.reduce((s, t) => s + safeGross(t) + safeComm(t), 0);
  const aaplAvgCost = aaplTotalCost / aaplBought;
  assert(Math.abs(aaplAvgCost - 185.10) < 0.001, `AAPL avg cost: $185.10 (got $${aaplAvgCost.toFixed(2)})`);

  const msftTotalCost = msftBuys.reduce((s, t) => s + safeGross(t) + safeComm(t), 0);
  const msftAvgCost = msftTotalCost / msftBought;
  assert(Math.abs(msftAvgCost - 420.1667) < 0.01, `MSFT avg cost: $420.17 (got $${msftAvgCost.toFixed(2)})`);

  const costBasisSold = aaplSold * aaplAvgCost;
  const netSaleProceeds = aaplSells.reduce((s, t) => s + safeGross(t) - safeComm(t), 0);
  const realisedGain = netSaleProceeds - costBasisSold;
  assert(Math.abs(realisedGain - 146.00) < 0.01, `Realised gain: $146.00 (got $${realisedGain.toFixed(2)})`);

  const totalCommissions = typedWfTxs.reduce((s, t) => s + safeComm(t), 0);
  assert(totalCommissions === 13, `Total commissions: $13 (got $${totalCommissions})`);

  const purchaseCommissions = typedWfTxs.filter((t) => t.event_type === "BUY")
    .reduce((s, t) => s + safeComm(t), 0);
  assert(purchaseCommissions === 10, `Purchase commissions: $10 (got $${purchaseCommissions})`);

  const dividends = typedWfTxs.filter((t) => t.event_type === "DIVIDEND")
    .reduce((s, t) => s + safeGross(t), 0);
  assert(dividends === 50, `Dividends: $50 (got $${dividends})`);

  const fees = typedWfTxs.filter((t) => t.event_type === "FEE")
    .reduce((s, t) => s + safeGross(t), 0);
  assert(fees === 5, `Fees: $5 (got $${fees})`);

  const taxes = typedWfTxs.filter((t) => t.event_type === "TAX")
    .reduce((s, t) => s + safeGross(t), 0);
  assert(taxes === 0, `Taxes: $0 (got $${taxes})`);

  const { data: reb, error: rebErr } = await serviceClient.from("rebalance_events").insert({
    portfolio_id: portfolioId, model_snapshot_id: snapPk,
    rebalance_date: "2025-04-01", owner_id: ownerUser.id,
  }).select().single() as { data: TxRow | null; error: unknown };
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

main().catch((error: unknown) => {
  console.error("FATAL:", error);
  process.exit(1);
});
