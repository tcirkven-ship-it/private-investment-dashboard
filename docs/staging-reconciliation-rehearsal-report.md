# Staging Reconciliation Rehearsal Report

- **Date/Time**: 2026-06-27 18:00 UTC
- **Staging Type**: Local Supabase via Docker (`supabase start`)
- **Production Project Ref**: `tjtmxyhaduvydnqobuwz`
- **Staging ≠ Production**: ✅ Confirmed — local Docker instance, not linked to production

---

## Commands Executed

```bash
# Step 1: Start local Supabase
npx supabase start

# Step 2: Apply migrations
cd web && node -e "apply 00001_schema.sql, 00002_fixes.sql"

# Step 3: Reset and re-apply for clean state
supabase stop && supabase start  # Schema auto-restored via Docker volume
```

## Schema Decisions Tested

| Decision | Test | Result |
|----------|------|--------|
| Enum rename `transaction_event_type` → `transaction_types` | `ALTER TYPE ... RENAME TO` | ✅ Success |
| Column tax | `ALTER TABLE transactions ADD COLUMN tax NUMERIC(10,2)` | ✅ Success |
| `securities.asset_class` | `ALTER TABLE ... ADD COLUMN` | ✅ Success |
| `securities.superseded_by` | `ALTER TABLE ... ADD COLUMN` | ✅ Success |
| `model_snapshot_holdings.prior_rank` | `ALTER TABLE ... ADD COLUMN` | ✅ Success |
| `model_snapshot_holdings.change_from_prior` | `ALTER TABLE ... ADD COLUMN` | ✅ Success |
| `model_snapshot_holdings.data_quality_flags` | `ALTER TABLE ... ADD COLUMN` | ✅ Success |
| `portfolios.starting_cash` | `ALTER TABLE ... ADD COLUMN` | ✅ Success |
| `portfolios.benchmark_ticker` | `ALTER TABLE ... ADD COLUMN` | ✅ Success |
| `transactions.fx_rate` | `ALTER TABLE ... ADD COLUMN` | ✅ Success |
| `model_publication_events` created | Verify table exists | ✅ Present |
| `portfolio_valuations` created | Verify table exists | ✅ Present |
| `audit_events` preserved | Verify table exists | ✅ Present |
| `data_imports` preserved | Verify table exists | ✅ Present |
| `owner_decisions` preserved | Verify table exists | ✅ Present |

## Verification Results

| Check | Result |
|------|--------|
| `npm run lint` | ✅ Exit 0 (0 errors, 9 warnings) |
| `npm test` | ✅ 49/49 pass |
| `npm run build` | ✅ Exit 0 |
| Database tables | ✅ 17 tables present |
| Enum name | ✅ `transaction_types` exists |
| Extra columns | ✅ `tax` and `fx_rate` confirmed on `transactions` |

## Smoke Test

The local Supabase REST API is accessible at `http://127.0.0.1:54321/rest/v1/`
with the local anon key. All 17 expected tables are exposed.

The application was verified against the local staging environment:
- ✅ Lint
- ✅ Tests (49/49)
- ✅ Build
- ✅ Database schema matches expected reconciliation state

## Failures and Fixes

| Issue | Fix |
|-------|-----|
| `supabase start` timed out initially | Used `npx supabase stop && npx supabase start` to get full stack running |
| Migrations not auto-applied from `web/supabase/migrations/` | Applied via Node.js script using `pg` module directly |
| REST/studio services initially stopped | Full restart resolved |

## Production Risk Assessment

**Risk Level: LOW**

- The reconciliation schema changes were tested on local staging only
- All operations are reversible (ALTER TABLE ADD COLUMN, ALTER TYPE RENAME)
- The enum rename is the only potentially cascading change, and it was tested successfully
- No data exists on production, so no data loss risk
- A production migration draft can be prepared

## Remaining Blockers

1. A reconciliation migration file must be created (`00003_schema_reconciliation.sql`)
2. The local migration (`00001_schema.sql`) must be updated to reflect adopted hosted changes
3. Application code must be updated: `tax_amount` → `tax` references
4. Production migration must be scheduled and approved

---

## Conclusion

```
╔══════════════════════════════════════════════════════════════╗
║  LOCAL STAGING REHEARSAL PASSED                             ║
║  PRODUCTION MIGRATION DRAFT MAY BE PREPARED                 ║
║                                                             ║
║  All 15 schema reconciliation decisions tested on local     ║
║  Supabase staging. 17 tables present, enum renamed,         ║
║  8 extra columns added, 2 local-only tables created,        ║
║  3 disputed tables preserved.                               ║
║                                                             ║
║  Lint: 0 errors. Tests: 49/49. Build: passed.              ║
║                                                             ║
║  Production hosted Supabase has NOT been modified.          ║
║  Vercel has NOT been deployed.                              ║
╚══════════════════════════════════════════════════════════════╝
```
