#!/usr/bin/env tsx
/**
 * Database Migration Verification Script
 *
 * Requirements:
 *   1. A running PostgreSQL 16 database
 *   2. Connection string in PG_TEST_URL env var or default local socket
 *
 * Usage:
 *   PG_TEST_URL=postgresql://postgres:postgres@localhost:5432/dashboard_test
 *   npx tsx scripts/verify-migrations.ts
 *
 * If no database is available, this script prints the verification queries
 * and expected results for manual testing.
 */

import { execSync } from "child_process";
import * as path from "path";
import * as fs from "fs";

const MIGRATIONS_DIR = path.resolve(__dirname, "../supabase/migrations");
const RESET_SCRIPT = path.resolve(__dirname, "../supabase/reset_new_project.sql");
const DB_URL = process.env.PG_TEST_URL;

type TestResult = { name: string; passed: boolean; detail?: string };

async function run() {
  const results: TestResult[] = [];

  console.log("=".repeat(60));
  console.log("DATABASE MIGRATION VERIFICATION");
  console.log("=".repeat(60));

  if (!DB_URL) {
    console.log("\n⚠ No PG_TEST_URL set. Running in DOCUMENTATION mode — printing verification queries.\n");
    printVerificationQueries();
    return;
  }

  // We have a database — run real tests
  console.log(`\nPostgreSQL available. Testing against: ${DB_URL}\n`);

  // Step 1: Check empty database
  results.push(await testStep("Empty database check", async () => {
    const count = await query(DB_URL, "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'");
    return { passed: count === "0", detail: `Found ${count} tables` };
  }));

  // Step 2: Apply migration 00001
  results.push(await testStep("Apply 00001_schema.sql", async () => {
    const sql = fs.readFileSync(path.join(MIGRATIONS_DIR, "00001_schema.sql"), "utf-8");
    try {
      await execute(DB_URL, sql);
      return { passed: true };
    } catch (e: any) {
      return { passed: false, detail: e.message };
    }
  }));

  // Step 3: Apply migration 00002
  results.push(await testStep("Apply 00002_fixes.sql", async () => {
    const sql = fs.readFileSync(path.join(MIGRATIONS_DIR, "00002_fixes.sql"), "utf-8");
    try {
      await execute(DB_URL, sql);
      return { passed: true };
    } catch (e: any) {
      return { passed: false, detail: e.message };
    }
  }));

  // Step 4: Verify inventory
  const inventory = await getInventory(DB_URL);
  results.push({
    name: "Table count = 17",
    passed: inventory.tables.length === 17,
    detail: `Found ${inventory.tables.length} tables: ${inventory.tables.join(", ")}`
  });
  results.push({
    name: "Enum count = 3",
    passed: inventory.enums.length === 3,
    detail: `Found ${inventory.enums.length} enums: ${inventory.enums.join(", ")}`
  });
  results.push({
    name: "RLS policies = 24",
    passed: inventory.policies.length === 24,
    detail: `Found ${inventory.policies.length} policies`
  });

  // Step 5: Rollback test
  results.push(await testStep("Rollback (run reset)", async () => {
    const sql = fs.readFileSync(RESET_SCRIPT, "utf-8");
    try {
      await execute(DB_URL, sql);
      return { passed: true };
    } catch (e: any) {
      return { passed: false, detail: e.message };
    }
  }));

  // Step 6: Verify empty after reset
  results.push(await testStep("Empty after reset", async () => {
    const count = await query(DB_URL, "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'");
    return { passed: count === "0", detail: `Tables after reset: ${count}` };
  }));

  // Step 7: Reapply both migrations
  results.push(await testStep("Reapply 00001 after reset", async () => {
    const sql = fs.readFileSync(path.join(MIGRATIONS_DIR, "00001_schema.sql"), "utf-8");
    try {
      await execute(DB_URL, sql);
      return { passed: true };
    } catch (e: any) {
      return { passed: false, detail: e.message };
    }
  }));

  results.push(await testStep("Reapply 00002 after reset", async () => {
    const sql = fs.readFileSync(path.join(MIGRATIONS_DIR, "00002_fixes.sql"), "utf-8");
    try {
      await execute(DB_URL, sql);
      return { passed: true };
    } catch (e: any) {
      return { passed: false, detail: e.message };
    }
  }));

  // Step 8: Verify reapplication inventory matches
  const inventory2 = await getInventory(DB_URL);
  results.push({
    name: "Inventory matches after reapply",
    passed: JSON.stringify(inventory.tables.sort()) === JSON.stringify(inventory2.tables.sort()),
    detail: `Before: ${inventory.tables.length}, After: ${inventory2.tables.length}`
  });

  // Print results
  console.log("\n" + "=".repeat(60));
  console.log("TEST RESULTS");
  console.log("=".repeat(60));
  let passed = 0, failed = 0;
  for (const r of results) {
    const status = r.passed ? "✅ PASS" : "❌ FAIL";
    console.log(`  ${status}  ${r.name}`);
    if (r.detail) console.log(`       ${r.detail}`);
    if (r.passed) passed++; else failed++;
  }
  console.log(`\n${passed} passed, ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

async function testStep(name: string, fn: () => Promise<{ passed: boolean; detail?: string }>): Promise<TestResult> {
  try {
    return { name, ...(await fn()) };
  } catch (e: any) {
    return { name, passed: false, detail: e.message };
  }
}

async function query(url: string, sql: string): Promise<string> {
  const result = execSync(`psql "${url}" -t -A -c "${sql.replace(/"/g, '\\"')}"`, { encoding: "utf-8" });
  return result.trim();
}

async function execute(url: string, sql: string): Promise<void> {
  execSync(`psql "${url}" -f /dev/stdin`, { encoding: "utf-8", input: sql });
}

async function getInventory(url: string) {
  const tables = (await query(url, "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
    .split("\n").filter(Boolean);
  const enums = (await query(url, "SELECT t.typname FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid GROUP BY t.typname ORDER BY t.typname"))
    .split("\n").filter(Boolean);
  const policies = (await query(url, "SELECT policyname FROM pg_policies WHERE schemaname = 'public' ORDER BY policyname"))
    .split("\n").filter(Boolean);
  return { tables, enums, policies };
}

function printVerificationQueries() {
  console.log(`
Required: PostgreSQL 16 running on localhost:5432

Setup:
  1. createdb dashboard_test
  2. export PG_TEST_URL=postgresql://postgres:postgres@localhost:5432/dashboard_test

Commands to run manually:

  # Verify empty database
  psql "$PG_TEST_URL" -c "
    SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';
  "

  # Apply migration 00001
  psql "$PG_TEST_URL" -f supabase/migrations/00001_schema.sql

  # Apply migration 00002
  psql "$PG_TEST_URL" -f supabase/migrations/00002_fixes.sql

  # Verify inventory
  echo '=== TABLES ==='
  psql "$PG_TEST_URL" -c "
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' ORDER BY table_name;
  "
  echo '=== ENUMS ==='
  psql "$PG_TEST_URL" -c "
    SELECT t.typname, e.enumlabel
    FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid
    ORDER BY t.typname, e.enumlabel;
  "
  echo '=== POLICIES ==='
  psql "$PG_TEST_URL" -c "
    SELECT policyname, tablename, permissive, cmd
    FROM pg_policies WHERE schemaname = 'public'
    ORDER BY tablename, policyname;
  "
  echo '=== INDEXES ==='
  psql "$PG_TEST_URL" -c "
    SELECT indexname, tablename FROM pg_indexes
    WHERE schemaname = 'public' ORDER BY tablename;
  "
  echo '=== FUNCTIONS ==='
  psql "$PG_TEST_URL" -c "
    SELECT routine_name FROM information_schema.routines
    WHERE specific_schema = 'public' AND routine_type = 'FUNCTION'
    ORDER BY routine_name;
  "
  echo '=== TRIGGERS ==='
  psql "$PG_TEST_URL" -c "
    SELECT trigger_name, event_manipulation, event_object_table
    FROM information_schema.triggers
    WHERE trigger_schema = 'public' ORDER BY trigger_name;
  "

  # Reset
  psql "$PG_TEST_URL" -f supabase/reset_new_project.sql

  # Verify empty after reset
  psql "$PG_TEST_URL" -c "
    SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';
  "

  # Reapply
  psql "$PG_TEST_URL" -f supabase/migrations/00001_schema.sql
  psql "$PG_TEST_URL" -f supabase/migrations/00002_fixes.sql

Expected results:
  - Migration 00001: exit code 0, no errors
  - Migration 00002: exit code 0, no errors
  - Tables: 17 (app_settings, audit_events, benchmark_observations, data_imports,
    model_publication_events, model_snapshot_holdings, model_snapshots,
    model_versions, owner_decisions, portfolio_valuations, portfolios,
    price_observations, profiles, rebalance_events, rebalance_lines,
    securities, transactions)
  - Enums: 3 (rebalance_status, snapshot_status, transaction_event_type)
  - RLS policies: 24
  - Reset: exit code 0, all application tables dropped
  - Reapply: exit code 0, identical inventory
`);
}

run().catch(console.error);
