# Production Migration Preflight Checklist and Execution Plan

> **Warning**: This document is a planning checklist only.
> Do not execute the production migration until all approvals are obtained.
> Do not reset production hosted Supabase.
> Do not run destructive commands against production.

---

## 1. Current Approved State

| Status | Value |
|--------|-------|
| Local staging rehearsal | ✅ Passed |
| Schema reconciliation decisions | ✅ Adopted (see decision proposal) |
| Migration draft created | ✅ `00003_schema_reconciliation.sql` |
| Local migration updated | ✅ `00001_schema.sql` (enum name, columns) |
| App code aligned | ✅ `tax_amount` → `tax` updated |
| CI workflows | ✅ All green (6 workflows) |
| PR #10 | ✅ Merged |

## 2. Exact Migration Files to Apply

Applied in order:

| File | Purpose |
|------|---------|
| `web/supabase/migrations/00001_schema.sql` | Full schema (idempotent for fresh installs; skipped on hosted since tables exist) |
| `web/supabase/migrations/00002_fixes.sql` | No-op (SELECT 1) |
| `web/supabase/migrations/00003_schema_reconciliation.sql` | **Primary reconciliation file** — ensures enum, adds columns, creates missing tables |

**On hosted, only `00003_schema_reconciliation.sql` needs to be executed.**
`00001_schema.sql` and `00002_fixes.sql` are skipped because hosted already has tables.

## 3. Production Project Ref

- **Project ref**: `tjtmxyhaduvydnqobuwz`
- **Verification**: Must match the Supabase project to be migrated

## 4. Backup Requirements

Before any execution, the following **must** be backed up:

- [ ] **Schema-only dump**:
  ```bash
  pg_dump --schema-only --no-owner --no-acl \
    --dbname=<hosted-database-url> \
    > /tmp/hosted-pre-migration-schema-$(date +%Y%m%d-%H%M%S).sql
  ```
- [ ] **Data dump** (if any data exists):
  ```bash
  pg_dump --data-only --no-owner --no-acl \
    --dbname=<hosted-database-url> \
    > /tmp/hosted-pre-migration-data-$(date +%Y%m%d-%H%M%S).sql
  ```
- [ ] **Auth configuration**: Export from Supabase Dashboard → Authentication → Settings
- [ ] **Project settings**: Document Site URL, Redirect URLs, API settings
- [ ] **Backup storage**: Store securely outside the repository

## 5. Read-Only Preflight Inspection Commands

Run these against production **before** migration to confirm the baseline has not changed since the initial inspection.

### 5.1 — Table inventory
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' ORDER BY table_name;
```
Expected: 15 tables (app_settings, audit_events, benchmark_observations, data_imports, model_snapshot_holdings, model_snapshots, model_versions, owner_decisions, portfolios, price_observations, profiles, rebalance_events, rebalance_lines, securities, transactions)

### 5.2 — Enum inventory
```sql
SELECT t.typname, e.enumlabel
FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid
WHERE t.typnamespace = 'public'::regnamespace
ORDER BY t.typname, e.enumsortorder;
```
Expected: `snapshot_status`, `rebalance_status`, `transaction_types`

### 5.3 — Column comparison for key tables
```sql
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name IN (
  'securities', 'model_snapshot_holdings', 'portfolios', 'transactions'
)
ORDER BY table_name, ordinal_position;
```

### 5.4 — Policy inventory
```sql
SELECT tablename, policyname, cmd FROM pg_policies
WHERE schemaname = 'public' ORDER BY tablename, policyname;
```
Expected: 31 policies

### 5.5 — Function inventory
```sql
SELECT proname, lanname FROM pg_proc p
JOIN pg_language l ON p.prolang = l.oid
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public' AND p.prokind = 'f'
ORDER BY proname;
```
Expected: 6 functions

### 5.6 — Trigger inventory
```sql
SELECT trigger_name, event_object_table
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY trigger_name;
```

### 5.7 — RLS-enabled tables
```sql
SELECT relname FROM pg_class
WHERE relnamespace = 'public'::regnamespace
  AND relkind = 'r' AND relrowsecurity = true
ORDER BY relname;
```

### 5.8 — Data row counts (metadata only, no financial data)
```sql
SELECT 'profiles' AS tbl, count(*) FROM profiles
UNION ALL SELECT 'portfolios', count(*) FROM portfolios
UNION ALL SELECT 'transactions', count(*) FROM transactions
UNION ALL SELECT 'securities', count(*) FROM securities;
```

## 6. Confirmation Production Schema Matches Baseline

- [ ] Table list matches the 15-table hosted inventory from the read-only inspection
- [ ] Enum names match: `snapshot_status`, `rebalance_status`, `transaction_types`
- [ ] No unexpected objects found
- [ ] No schema drift detected since the read-only inspection report

If the schema has changed since the initial inspection, **stop** and re-inspect before proceeding.

## 7. Human Approval Checklist

- [ ] Migration file reviewed by a second person (if available)
- [ ] Local staging rehearsal passed
- [ ] All 6 CI workflows green
- [ ] Production schema backup completed
- [ ] Rollback plan reviewed
- [ ] Migration scheduled during low-activity window
- [ ] Explicit written approval obtained
- [ ] Team notified of migration window
- [ ] Vercel preview deployment ready for post-migration smoke test

## 8. Migration Execution Command Placeholders

**Do not execute until all approvals are obtained.**

### 8.1 — Connect to production database
```bash
# Use the Supabase project's database connection string
# Credentials stored securely, never hardcoded
```

### 8.2 — Run preflight inspections (Section 5)
```bash
# Verify current state matches expected baseline
psql <hosted-db-url> -f preflight-checks.sql
```

### 8.3 — Apply reconciliation migration
```bash
# Execute the reconciliation SQL against production
psql <hosted-db-url> -v ON_ERROR_STOP=1 \
  -f web/supabase/migrations/00003_schema_reconciliation.sql
```

### 8.4 — Verify migration
```bash
# Run schema-policy-audit against production
PG_TEST_URL=<hosted-db-url> npx tsx web/scripts/schema-policy-audit.ts

# Run auth/RLS tests (if test users are acceptable)
PG_TEST_URL=<hosted-db-url> npx tsx web/scripts/test-auth-rls.ts
```

## 9. Post-Migration Verification Checklist

- [ ] 17 tables present (15 original + `model_publication_events` + `portfolio_valuations`)
- [ ] 3 enums present (`snapshot_status`, `rebalance_status`, `transaction_types`)
- [ ] 31 RLS policies present
- [ ] 6 functions present
- [ ] 6 triggers present
- [ ] 17 tables with RLS enabled
- [ ] Extra columns confirmed: `tax`, `fx_rate`, `asset_class`, `superseded_by`, `prior_rank`, `change_from_prior`, `data_quality_flags`, `starting_cash`, `benchmark_ticker`
- [ ] No data lost (row counts match pre-migration numbers)
- [ ] Vercel preview deployment smoke test passes
- [ ] Login/auth flow works
- [ ] Model page loads
- [ ] Portfolio pages render
- [ ] Transactions display correctly

## 10. Rollback/Restore Plan

| Scenario | Action |
|----------|--------|
| Migration step fails | Stop immediately. Restore from schema+data backup. |
| Wrong column added | `ALTER TABLE ... DROP COLUMN IF EXISTS` — additive changes only, no data loss |
| Enum rename issue | `ALTER TYPE transaction_types RENAME TO transaction_event_type` |
| Application breaks | Revert code via Git; deploy previous version; fix migration; re-test on staging |
| Data corruption suspected | Restore from pre-migration data backup |
| Irrecoverable state | Contact Supabase support for point-in-time recovery |

All changes in `00003_schema_reconciliation.sql` are additive (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`). Rollback is always possible by simply dropping added columns or tables if needed.

## 11. Stop Conditions

Stop immediately if any of the following occur:

- [ ] Preflight inspections reveal schema changes since baseline
- [ ] Backup fails or is incomplete
- [ ] Migration SQL produces unexpected errors
- [ ] Post-migration verification fails
- [ ] Auth/RLS tests fail
- [ ] Application smoke tests fail against preview deployment
- [ ] Rollback plan cannot be executed
- [ ] Any destructive SQL accidentally targets production

## 12. Never Run `supabase db reset` Against Production

```
╔══════════════════════════════════════════════════════════════════╗
║  NEVER RUN:                                                     ║
║    supabase db reset                                            ║
║                                                                 ║
║  AGAINST PRODUCTION HOSTED SUPABASE.                            ║
║                                                                 ║
║  `supabase db reset` destroys all data, drops all tables,       ║
║  and re-applies migrations from scratch. This is                ║
║  irreversible on production.                                    ║
╚══════════════════════════════════════════════════════════════════╝
```

## 13. Never Run Destructive Reset or Broad Schema Deletion

```
╔══════════════════════════════════════════════════════════════════╗
║  NEVER EXECUTE ON PRODUCTION:                                   ║
║    DROP SCHEMA public CASCADE                                   ║
║    DROP TABLE ... CASCADE                                       ║
║    DROP TYPE ... CASCADE                                        ║
║    ALLOW_DESTRUCTIVE_DB_TESTS=true                              ║
║    supabase db reset                                            ║
║                                                                 ║
║  All migration operations must be additive only.                ║
║  No destructive reset. No broad schema deletion.                ║
╚══════════════════════════════════════════════════════════════════╝
```

## 14. Exact Status Labels Allowed After Execution

After successful production migration execution and verification:

- `PRODUCTION MIGRATION APPLIED`
- `PRODUCTION DEPLOYMENT STILL PENDING`

After Vercel deployment:

- `PRODUCTION DEPLOYMENT COMPLETE`

Never use:

- `SAFE TO DEPLOY` (deployment requires separate approval)
- `DEPLOYMENT READY` (deployment requires separate approval)
- `COMPLETE` (vague and ambiguous)
- `DATABASE RELEASE VERIFIED` (reserved for CI schema verification)

---

## Conclusion

```
╔══════════════════════════════════════════════════════════════════╗
║  PRODUCTION MIGRATION PREFLIGHT READY — MANUAL APPROVAL REQUIRED║
║  PRODUCTION MIGRATION NOT EXECUTED                               ║
║                                                                  ║
║  All planning documents are in place.                            ║
║  Local staging rehearsal passed.                                ║
║  Reconciliation migration created and tested.                    ║
║  Preflight checklist and rollback plan ready.                    ║
║                                                                  ║
║  Production hosted Supabase has NOT been modified.               ║
║  Vercel has NOT been deployed.                                   ║
╚══════════════════════════════════════════════════════════════════╝
```
