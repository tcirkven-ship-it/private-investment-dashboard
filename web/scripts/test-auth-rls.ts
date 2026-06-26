#!/usr/bin/env tsx
/**
 * Real Supabase Auth and RLS verification test.
 *
 * Requires: running local Supabase stack (npx supabase start)
 * Sets: ALLOW_DESTRUCTIVE_DB_TESTS=true
 *       PG_TEST_URL=postgresql://postgres:postgres@localhost:5432/postgres
 *       NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
 *       NEXT_PUBLIC_SUPABASE_ANON_KEY=<local anon key>
 *       SUPABASE_SERVICE_ROLE_KEY=<local service role key>
 */

import { createClient } from "@supabase/supabase-js";
import { execSync } from "child_process";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "http://localhost:54321";
const ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
const SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || "";
const PG_URL = process.env.PG_TEST_URL || "";
const TEST_DB = "dashboard_auth_test";

let passed = 0;
let failed = 0;
const errors: string[] = [];

function assert(condition: boolean, message: string) {
  if (condition) {
    passed++;
    console.log(`  [PASS] ${message}`);
  } else {
    failed++;
    errors.push(message);
    console.log(`  [FAIL] ${message}`);
  }
}

async function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

async function main() {
  console.log("=== Supabase Auth and RLS Verification ===");
  console.log("");

  if (!ANON_KEY || !SERVICE_KEY) {
    console.log("  SKIP: Supabase keys not configured");
    console.log("  Run against local Supabase: npx supabase start");
    console.log("  Copy keys from: http://localhost:54323/project/default/settings/api");
    process.exit(0);
  }

  // Create test database
  try {
    execSync(
      `psql "${PG_URL}" -c "CREATE DATABASE ${TEST_DB};"`,
      { stdio: "ignore" }
    );
  } catch {}
  const dbUrl = PG_URL.replace(/\/[^/]+$/, `/${TEST_DB}`);

  // Apply migration
  console.log("--- Applying migration ---");
  execSync(
    `ALLOW_DESTRUCTIVE_DB_TESTS=true EXPECTED_TEST_DATABASE=${TEST_DB} PG_TEST_URL="${dbUrl}" bash scripts/test-migration.sh`,
    { stdio: "inherit", cwd: __dirname + "/.." }
  );

  // Clients
  const anonClient = createClient(SUPABASE_URL, ANON_KEY);
  const serviceClient = createClient(SUPABASE_URL, SERVICE_KEY, {
    auth: { autoRefreshToken: false, persistSession: false },
  });

  // Create owner user
  console.log("--- Creating users ---");
  const email1 = `owner_${Date.now()}@test.com`;
  const { data: ownerData, error: ownerErr } = await anonClient.auth.signUp({
    email: email1,
    password: "test123456!",
  });
  assert(!ownerErr, `Owner user created: ${ownerErr?.message || ""}`);
  const ownerId = ownerData?.user?.id || "";

  // Create second user
  const email2 = `user2_${Date.now()}@test.com`;
  const { data: user2Data, error: user2Err } = await anonClient.auth.signUp({
    email: email2,
    password: "test123456!",
  });
  assert(!user2Err, `Second user created: ${user2Err?.message || ""}`);
  const user2Id = user2Data?.user?.id || "";

  await sleep(2000); // Wait for Auth->profile trigger

  // Verify profiles
  console.log("--- Profile verification ---");
  const { data: profiles } = await serviceClient
    .from("profiles")
    .select("id, email, is_owner");

  const ownerProfile = (profiles || []).find((p: any) => p.id === ownerId);
  assert(!!ownerProfile, "Owner profile exists");
  assert(ownerProfile?.is_owner === true, "First user is owner");

  const user2Profile = (profiles || []).find((p: any) => p.id === user2Id);
  assert(!!user2Profile, "Second user profile exists");
  assert(user2Profile?.is_owner === false, "Second user is not owner");

  const ownerCount = (profiles || []).filter((p: any) => p.is_owner).length;
  assert(ownerCount === 1, `Exactly one owner (found ${ownerCount})`);

  // Auth clients
  const ownerClient = createClient(SUPABASE_URL, ANON_KEY);
  await ownerClient.auth.signInWithPassword({ email: email1, password: "test123456!" });

  const user2Client = createClient(SUPABASE_URL, ANON_KEY);
  await user2Client.auth.signInWithPassword({ email: email2, password: "test123456!" });

  // Create test portfolio and transaction via service role
  const { data: portfolio } = await serviceClient
    .from("portfolios")
    .insert({ owner_id: ownerId, name: "Test", opening_date: "2025-01-01", currency: "USD" })
    .select()
    .single();
  assert(!!portfolio, "Portfolio created via service role");

  // === RLS Tests ===
  console.log("--- RLS: Anonymous access ---");
  const { data: anonPortfolios, error: anonErr } = await anonClient
    .from("portfolios")
    .select("*");
  assert(!anonErr || (anonPortfolios || []).length === 0, "Anonymous cannot read portfolios");

  const { error: anonInsertErr } = await anonClient
    .from("portfolios")
    .insert({ owner_id: ownerId, name: "Hack", opening_date: "2025-01-01" });
  assert(!!anonInsertErr, "Anonymous cannot insert portfolios");

  // === Owner access ===
  console.log("--- RLS: Owner access ---");
  const { data: ownerPorts } = await ownerClient
    .from("portfolios")
    .select("*");
  assert((ownerPorts || []).length >= 1, "Owner can read own portfolios");

  const { error: ownerInsertErr } = await ownerClient
    .from("portfolios")
    .insert({ owner_id: ownerId, name: "Owner Portfolio 2", opening_date: "2025-06-01" });
  assert(!ownerInsertErr, "Owner can insert portfolio");

  // === Second user denial ===
  console.log("--- RLS: Second user isolation ---");
  const { data: user2Ports } = await user2Client
    .from("portfolios")
    .select("*");
  assert((user2Ports || []).length === 0, "Second user cannot read owner portfolios");

  const { error: user2InsertErr } = await user2Client
    .from("portfolios")
    .insert({ owner_id: user2Id, name: "User2 Portfolio", opening_date: "2025-01-01" });
  assert(!user2InsertErr, "Second user can insert own portfolio");

  const { data: user2Models } = await user2Client
    .from("model_snapshots")
    .select("*");
  assert((user2Models || []).length === 0, "Second user cannot read model snapshots");

  // === Transaction UPDATE/DELETE denied ===
  console.log("--- RLS: Transaction immutability ---");
  const { data: tx } = await serviceClient
    .from("transactions")
    .insert({
      portfolio_id: portfolio!.id, event_type: "DEPOSIT",
      event_date: "2025-01-02", gross_amount: 1000,
      idempotency_key: "rls-tx-1", owner_id: ownerId,
    })
    .select()
    .single();
  assert(!!tx, "Transaction created via service role");

  if (tx) {
    const { error: updateErr } = await ownerClient
      .from("transactions")
      .update({ gross_amount: 999 })
      .eq("id", tx.id);
    assert(!!updateErr, "Owner cannot UPDATE transactions");

    const { error: deleteErr } = await ownerClient
      .from("transactions")
      .delete()
      .eq("id", tx.id);
    assert(!!deleteErr, "Owner cannot DELETE transactions");
  }

  // === Published snapshot immutability ===
  console.log("--- RLS: Published snapshot immutability ---");
  const { data: mv } = await serviceClient
    .from("model_versions")
    .insert({ model_id: "rls-test", version: "1.0" })
    .select()
    .single();
  const { data: snap } = await serviceClient
    .from("model_snapshots")
    .insert({
      model_version_id: mv!.id, snapshot_id: "rls-snap",
      status: "PUBLISHED", effective_date: "2025-01-01",
      published_at: new Date().toISOString(),
    })
    .select()
    .single();
  assert(!!snap, "Published snapshot created");

  const { error: snapUpdateErr } = await ownerClient
    .from("model_snapshots")
    .update({ status: "DRAFT" })
    .eq("id", snap!.id);
  assert(!!snapUpdateErr, "Owner cannot UPDATE published snapshot");

  const { error: snapDeleteErr } = await ownerClient
    .from("model_snapshots")
    .delete()
    .eq("id", snap!.id);
  assert(!!snapDeleteErr, "Owner cannot DELETE published snapshot");

  // === Summary ===
  console.log("");
  console.log("=== AUTH/RLS TEST RESULTS ===");
  console.log(` Passed: ${passed}`);
  console.log(` Failed: ${failed}`);
  if (failed > 0) {
    console.log(" Failures:");
    errors.forEach((e) => console.log(`  - ${e}`));
    console.log(" RESULT: FAILED");
    process.exit(1);
  }
  console.log(" RESULT: PASSED");
}

main().catch(console.error);
