# Hosted Supabase Migration Rehearsal Plan

This is a controlled plan for a future migration rehearsal.
**Do not execute against hosted Supabase until explicitly approved.**

## Overview

- **Goal**: Verify that committed migrations apply cleanly against a hosted Supabase project
- **Risk**: Destructive if mishandled — read-only steps first
- **Requires**: `SUPABASE_SERVICE_ROLE_KEY` with appropriate permissions

## Procedure

### Step 1: Backup / Export

- [ ] Export hosted schema via `supabase db dump --linked`
- [ ] Store backup in a secure, versioned location (not in repository)
- [ ] Export auth/users configuration if needed
- [ ] Verify backup file is valid SQL

### Step 2: Inspect Current Hosted Schema

- [ ] Connect to hosted Supabase with `psql` (read-only transaction)
- [ ] Run `\dt` to list tables
- [ ] Run `\d+ <table>` for each table
- [ ] Check RLS policies: `SELECT * FROM pg_policies;`
- [ ] Check triggers: `SELECT * FROM information_schema.triggers;`
- [ ] Check functions: `SELECT * FROM information_schema.routines WHERE specific_schema='public';`
- [ ] Check enums: `SELECT * FROM pg_type WHERE typcategory='E';`

### Step 3: Compare Hosted Schema to Committed Migrations

- [ ] Run the schema-policy-audit script against hosted DB (dry-run only)
- [ ] Report any differences:
  - Missing tables
  - Extra tables
  - Missing columns
  - Differing types
  - Missing RLS policies
  - Missing triggers
  - Missing functions
  - Missing enums
- [ ] Document all differences before applying any change

### Step 4: Dry-Run / Staging Rehearsal (if available)

- [ ] If a staging Supabase project exists: apply migrations there first
- [ ] Run all CI verification jobs against staging:
  - `verify`
  - `reset-reapply`
  - `rollback-test`
  - `schema-policy-audit`
- [ ] Run full auth/RLS test suite against staging
- [ ] Run full application smoke test against staging

### Step 5: Apply After Approval

**Only after explicit written approval.**
**Not during market hours if the application is live.**

- [ ] Ensure `ALLOW_DESTRUCTIVE_DB_TESTS` is NOT set
- [ ] Ensure `SUPABASE_CI` is NOT set
- [ ] Apply migrations one by one:
  ```bash
  supabase db push --linked
  ```
- [ ] Verify each migration step with `supabase db status`

### Step 6: Verify RLS / Policies / Functions / Triggers

- [ ] Run schema-policy-audit: `PG_TEST_URL=<hosted-db-url> npx tsx scripts/schema-policy-audit.ts`
- [ ] Run auth/RLS tests: `PG_TEST_URL=<hosted-db-url> npx tsx scripts/test-auth-rls.ts`
  - Note: test-auth-rls creates test users — assess whether to run against hosted
- [ ] Run CI verification jobs:
  ```bash
  npm run test:db-migrations
  npm run test:db-rls
  npm run test:schema-audit
  ```
- [ ] All jobs must pass before proceeding

### Step 7: Never Run Destructive Reset on Hosted Production

- `reset_new_project.sql` is for local development only
- Never run `supabase db reset` against hosted
- Never run `DROP SCHEMA public CASCADE` against hosted
- Never use `ALLOW_DESTRUCTIVE_DB_TESTS=true` against hosted

### Step 8: Rollback / Restore Plan

- [ ] If migration fails: restore from backup taken in Step 1
- [ ] Backup restoration procedure:
  1. Connect to hosted Supabase via `psql`
  2. Run the backup SQL file in a single transaction
  3. Verify schema matches expected state
  4. Run verification jobs again
- [ ] If backup restoration is not possible: contact Supabase support for point-in-time recovery
- [ ] Document the failure and update migrations before retrying

## Safety Checklist

- [ ] Hosted Supabase URL confirmed (not production until approved)
- [ ] `ALLOW_DESTRUCTIVE_DB_TESTS` is unset
- [ ] `SUPABASE_CI` is unset
- [ ] Backup taken and verified
- [ ] Read-only inspection completed
- [ ] Staging rehearsal passed (if available)
- [ ] Explicit approval received
- [ ] Rollback plan ready
