# Production Migration Draft Report

- **Date**: 2026-06-27
- **Draft Branch**: `production-migration-draft`
- **Status**: DRAFT — NOT APPLIED

---

## What the Migration Draft Changes

### Schema changes (00003_schema_reconciliation.sql)

The reconciliation migration applied against hosted Supabase:

1. **Enum**: Ensures `transaction_types` exists (no-op if already present; renames `transaction_event_type` if found).
2. **`transactions.tax`**: Adds column if not exists (hosted already has it).
3. **`securities.asset_class`**: Adds column if not exists.
4. **`securities.superseded_by`**: Adds column + index if not exists.
5. **`model_snapshot_holdings.prior_rank`**: Adds column if not exists.
6. **`model_snapshot_holdings.change_from_prior`**: Adds column if not exists.
7. **`model_snapshot_holdings.data_quality_flags`**: Adds column if not exists.
8. **`portfolios.starting_cash`**: Adds column if not exists.
9. **`portfolios.benchmark_ticker`**: Adds column if not exists.
10. **`transactions.fx_rate`**: Adds column + check constraint if not exists.
11. **`model_publication_events`**: Creates table + RLS + policies + index if not exists.
12. **`portfolio_valuations`**: Creates table + RLS + policies + index if not exists.

### Local migration (00001_schema.sql) updates

Updated for future fresh installations to match hosted naming and columns:
- Enum renamed: `transaction_event_type` → `transaction_types`
- Added columns: `tax`, `fx_rate`, `asset_class`, `superseded_by`, `prior_rank`, `change_from_prior`, `data_quality_flags`, `starting_cash`, `benchmark_ticker`
- Added index: `idx_securities_superseded_by`

### Application code updates

All TypeScript references to `tax_amount` renamed to `tax`:
- `adapters.ts` — TransactionData interface + adapter function (backward-compatible: reads `tax` or `tax_amount`)
- `holdings.ts` — Transaction interface + holdings engine
- `route-loaders.ts` — TransactionData interface + select query + mapping
- `supabase-queries.ts` — Transaction interface + select query
- `types.ts` — TransactionRow type
- `route-loaders.test.ts` — test data
- `holdings.test.ts` — test data

### CI/script updates

- `schema-policy-audit.ts` — updated expected column definitions and enum name
- `reset_new_project.sql` — updated drop type name

## Why It Is Safe

- **All SQL is idempotent**: `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`
- **No destructive operations**: No `DROP TABLE`, `DROP COLUMN`, `TRUNCATE`, or schema wipe
- **No data assumptions**: All changes are additive — they do not depend on the hosted instance being empty
- **Enum is preserved**: The hosted enum `transaction_types` is not dropped; only renamed if it still uses the old local name `transaction_event_type`
- **Application backward-compatible**: The `getTransaction` adapter reads `tax` first, falls back to `tax_amount` for backward compatibility during transition
- **Staging-verified**: All changes were tested against local Supabase staging (17 tables, 49 tests, lint/build all passing)

## What It Does Not Do

- ❌ No production migration is applied
- ❌ No schema reset
- ❌ No data deletion
- ❌ No hosted Supabase modification
- ❌ No Vercel deployment
- ❌ No `DROP TYPE ... CASCADE` on hosted
- ❌ No assumptions that hosted is empty

## Production Preflight Checklist

Before executing the migration against hosted:

- [ ] Hosted schema backed up (pg_dump --schema-only)
- [ ] Hosted project settings documented (auth, redirect URLs)
- [ ] Staging rehearsal passed (✅ completed)
- [ ] Migration tested against staging (✅ completed)
- [ ] Code changes reviewed and merged
- [ ] All CI workflows green
- [ ] Migration file reviewed for safety
- [ ] Explicit written approval obtained
- [ ] Rollback plan ready
- [ ] Migration scheduled during low-activity window

## Backup Requirements

Before any execution:
1. `pg_dump --schema-only --no-owner <hosted-db-url> > hosted-pre-migration-backup.sql`
2. `pg_dump --data-only --no-owner <hosted-db-url> > hosted-data-backup.sql` (if data exists)
3. Document Supabase project auth/redirect/API settings
4. Store backups securely outside the repository

## Rollback/Restore Plan

| Scenario | Action |
|----------|--------|
| Migration step fails | Stop, assess, roll back using `psql` restore from backup |
| Wrong column added | `ALTER TABLE ... DROP COLUMN IF EXISTS` (non-destructive to data) |
| Enum rename causes issue | `ALTER TYPE transaction_types RENAME TO transaction_event_type` |
| Application breaks after migration | Revert code, fix migration, re-test on staging |
| Irrecoverable | Contact Supabase support for point-in-time recovery |

## Manual Approval Required

```
╔══════════════════════════════════════════════════════════════════╗
║  THIS MIGRATION MUST NOT BE EXECUTED AGAINST PRODUCTION         ║
║  UNTIL EXPLICIT WRITTEN APPROVAL IS OBTAINED.                   ║
║                                                                  ║
║  Approval checklist:                                             ║
║  [ ] Migration file reviewed                                     ║
║  [ ] Staging rehearsal passed                                   ║
║  [ ] All CI workflows green                                     ║
║  [ ] Hosted schema backed up                                    ║
║  [ ] Rollback plan ready                                        ║
║  [ ] Written approval received                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

## Production Not Modified

- Production hosted Supabase was **NOT modified** during this draft
- Vercel was **NOT deployed**
- All operations were local (code edits, migration file creation)

---

## Conclusion

```
╔══════════════════════════════════════════════════════════════════╗
║  PRODUCTION MIGRATION DRAFT READY — MANUAL REVIEW REQUIRED      ║
║                                                                  ║
║  Migration file: 00003_schema_reconciliation.sql                 ║
║  Local migration updated: 00001_schema.sql                       ║
║  Code references renamed: tax_amount -> tax                      ║
║  CI scripts updated: schema-policy-audit, reset_new_project      ║
║                                                                  ║
║  Lint: 0 errors | Tests: 49/49 | Build: passed                  ║
║  Production hosted Supabase: NOT modified                        ║
║  Vercel: NOT deployed                                            ║
╚══════════════════════════════════════════════════════════════════╝
```
