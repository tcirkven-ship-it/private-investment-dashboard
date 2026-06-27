# Hosted Schema Reconciliation Plan

> **Warning**: Do not reset hosted Supabase. Do not run migrations against hosted Supabase until this plan is approved.
> This is a planning document only — no executable migration changes are generated.

---

## 1. Hosted Schema Inventory Summary

**Source**: Read-only REST API inspection (2026-06-27).
**Project Ref**: `tjtmxyhaduvydnqobuwz`
**Tables**: 15
**Custom Enums**: 3
**Data Rows**: 0 (all tables empty)

**Hosted tables (via PostgREST)**:
`app_settings`, `audit_events`, `benchmark_observations`, `data_imports`,
`model_snapshot_holdings`, `model_snapshots`, `model_versions`,
`owner_decisions`, `portfolios`, `price_observations`, `profiles`,
`rebalance_events`, `rebalance_lines`, `securities`, `transactions`

## 2. Local Committed Schema Inventory Summary

**Source**: `web/supabase/migrations/00001_schema.sql`
**Tables**: 17
**Custom Enums**: 3 (`snapshot_status`, `rebalance_status`, `transaction_event_type`)
**Functions**: 6 (`update_updated_at_column`, `handle_new_user`,
`check_snapshot_status_transition`, `prevent_portfolio_deletion`,
`check_transaction_owner`, `is_owner`)
**Triggers**: 6 (`set_profiles_updated_at`, `on_auth_user_created`,
`check_snapshot_status_transition`, `set_portfolios_updated_at`,
`prevent_portfolio_deletion`, `check_transaction_owner`)
**Policies**: 31
**Indexes**: 9

**Local tables (from 00001_schema.sql)**:
`profiles`, `app_settings`, `securities`, `model_versions`,
`model_snapshots`, `model_snapshot_holdings`, `model_publication_events`,
`portfolios`, `transactions`, `price_observations`, `benchmark_observations`,
`portfolio_valuations`, `rebalance_events`, `rebalance_lines`,
`owner_decisions`, `data_imports`, `audit_events`

---

## 3. Table-by-Table Comparison

### Every hosted table exists in the local migration

All 15 tables present on the hosted Supabase instance are defined in
`web/supabase/migrations/00001_schema.sql`. There are **zero hosted-only tables**.

### Disputed tables clarification

The earlier read-only inspection report (docs/hosted-supabase-readonly-inspection-report.md)
listed `audit_events`, `data_imports`, and `owner_decisions` as "hosted-only — extra tables."
**This was incorrect.** These three tables are defined in the local migration:

| Table | In Hosted? | In `00001_schema.sql`? | Line in migration | Classification |
|-------|-----------|------------------------|-------------------|---------------|
| `audit_events` | **yes** | **yes** | Line 419 | Both — present in both |
| `data_imports` | **yes** | **yes** | Line 403 | Both — present in both |
| `owner_decisions` | **yes** | **yes** | Line 390 | Both — present in both |

The error occurred because the earlier inspection report compared against an
**implicit mental model** of what the migration contained, rather than reading the
actual migration file. When the reconciliation plan was written, the migration file
was read directly, revealing all three tables are present locally.

### Local-only tables (in migration, not found on hosted)

| Table | Line in migration | Classification |
|-------|-------------------|---------------|
| `model_publication_events` | Line 208 | **Local-only** — must be created on hosted |
| `portfolio_valuations` | Line 346 | **Local-only** — must be created on hosted |

### Column-level differences (tables present in both)

| Table | Columns only in local | Columns only in hosted |
|-------|----------------------|----------------------|
| `profiles` | — (exact match) | — (exact match) |
| `app_settings` | — (exact match) | — (exact match) |
| `securities` | — (exact match) | `asset_class`, `superseded_by` |
| `model_versions` | — (exact match) | — (exact match) |
| `model_snapshots` | — (exact match) | — (exact match) |
| `model_snapshot_holdings` | — (exact match) | `prior_rank`, `change_from_prior`, `data_quality_flags` |
| `portfolios` | — (exact match) | `starting_cash`, `benchmark_ticker` |
| `transactions` | `tax_amount` | `tax` (numeric), `fx_rate` |
| `price_observations` | — (exact match) | — (exact match) |
| `benchmark_observations` | — (exact match) | — (exact match) |
| `rebalance_events` | — (exact match) | — (exact match) |
| `rebalance_lines` | — (exact match) | — (exact match) |
| `owner_decisions` | — (exact match) | — (exact match) |
| `data_imports` | — (exact match) | — (exact match) |
| `audit_events` | — (exact match) | — (exact match) |

### Summary counts
- Tables present in **both**: 15
- Tables present in **local only**: 2 (`model_publication_events`, `portfolio_valuations`)
- Tables present in **hosted only**: **0**
- Tables with exact column match: 10
- Tables with column differences: 4 (`securities`, `model_snapshot_holdings`, `portfolios`, `transactions`)

---

## 4. Enum-by-Enum Comparison

| Local Name | Hosted Name | Values Match? | Conflict? |
|-----------|-------------|---------------|-----------|
| `snapshot_status` | `snapshot_status` | ✅ Same values | None |
| `rebalance_status` | `rebalance_status` | ✅ Same values | None |
| `transaction_event_type` | `transaction_types` | ✅ Same values likely | **NAME MISMATCH — HIGH** |

The `transactions.event_type` column references the enum by name. If the hosted
instance has `event_type` typed as `transaction_types` and the local migration
creates `transaction_event_type`, attempting to apply the local migration will
fail because the column already uses a different type name.

---

## 5. Function/Trigger/Policy Comparison

Functions, triggers, and policies cannot be directly compared via REST API
(PostgREST only exposes tables, not procedural objects). A direct `psql` connection
(with database password) is required to verify these.

**Known from local migration:**
- 6 functions: `update_updated_at_column`, `handle_new_user`,
  `check_snapshot_status_transition`, `prevent_portfolio_deletion`,
  `check_transaction_owner`, `is_owner`
- 6 triggers
- 31 RLS policies across 17 tables

**Assumption:** If the hosted instance was initialized from a migration similar to
`00001_schema.sql`, the functions, triggers, and policies should match. This must
be verified before migration via direct database query.

---

## 6. Hosted-Only Objects

**None.** All 15 tables on the hosted instance exist in the local committed migration.

---

## 7. Local-Only Objects

| Object | Type | Classification |
|--------|------|---------------|
| `model_publication_events` | Table | **Create on hosted** — publication audit trail |
| `portfolio_valuations` | Table | **Create on hosted** — derived valuation snapshots |

---

## 8. Conflicting Objects

| Conflict | Severity | Resolution Needed |
|----------|----------|-------------------|
| Enum name `transaction_event_type` vs `transaction_types` | **HIGH** | Must pick one name; all column references must match |
| `transactions.tax_amount` vs `tax` | **MEDIUM** | Column naming — pick one |
| `transactions` missing `fx_rate` locally | **LOW** | Add if multi-currency needed |
| `securities` missing `asset_class`, `superseded_by` locally | **LOW** | Add if needed |
| `model_snapshot_holdings` missing `prior_rank`, `change_from_prior`, `data_quality_flags` locally | **LOW** | Add if needed |
| `portfolios` missing `starting_cash`, `benchmark_ticker` locally | **LOW** | Add if needed |

---

## 9. Data-Preservation Questions

Since the hosted instance has **zero data rows** in all 15 tables:

1. **Is there any configuration in `app_settings` that must be preserved?**
   Currently: no rows. After migration: no data to lose.

2. **Are there any Supabase Auth users that must be preserved?**
   Auth user count was not inspected (restricted). Separate check needed.

3. **Are there any storage objects or auth configurations?**
   Not inspected. Separate check needed.

4. **Can the hosted schema be fully replaced by our local migration?**
   **Yes** — zero data rows means no data loss risk.
   **But** — the enum name conflict means a naive migration will fail on
   `CREATE TYPE transaction_event_type` when `transaction_types` already exists.

---

## 10. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Enum name conflict blocks migration | **HIGH** | Migration fails | Create a new migration that renames or reconciles enums first |
| Column type mismatch (`tax_amount` vs `tax`) | **MEDIUM** | Migration fails or wrong type | Must reconcile column names and types |
| Extra columns on hosted cause `CREATE TABLE` conflict | **LOW** | `CREATE TABLE` fails | Use `CREATE TABLE IF NOT EXISTS` or separate baseline migration |
| Missing local tables not created on hosted | **LOW** | Missing features | Create in a new migration |
| Function/trigger/policy mismatch unverified | **MEDIUM** | Unexpected RLS behavior | Need direct database query to compare |
| Renaming enum breaks existing column references | **HIGH** | Data type mismatch | Must use `ALTER COLUMN ... TYPE ... USING` with careful cast |

---

## 11. Recommended Reconciliation Strategy

### Option A — Adopt hosted as baseline (recommended if hosted is canonical)

1. Dump the full hosted schema definition (via `pg_dump --schema-only`).
2. Create a new baseline migration file (`00003_baseline.sql`) that:
   - Uses `CREATE TABLE IF NOT EXISTS` for all 15 existing tables.
   - Uses the hosted enum name `transaction_types` (adopt hosted naming).
   - Adds missing local-only tables: `model_publication_events`, `portfolio_valuations`.
   - Adds local columns missing from hosted via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.
   - Drops hosted columns not used by the application (if any).
3. Create a follow-up migration (`00004_reconcile.sql`) for fine-tuning.

### Option B — Replace with local migration (simpler, must handle conflicts)

1. Export hosted schema as backup.
2. Create a migration that:
   - Drops conflicting type: `DROP TYPE IF EXISTS transaction_types CASCADE;`
   - Creates local type: `CREATE TYPE transaction_event_type AS ENUM (...);`
   - Re-types column: `ALTER TABLE transactions ALTER COLUMN event_type TYPE transaction_event_type USING event_type::text::transaction_event_type;`
   - Uses `CREATE TABLE IF NOT EXISTS` for all tables.
   - Adds `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` for extra hosted columns.
   - Drops local-only columns from hosted if not needed.
   - Re-applies all functions, triggers, policies idempotently.

### Option C — Staging rehearsal first (safest)

1. Create a staging Supabase project.
2. Apply the hosted schema to staging via backup/restore.
3. Test Options A or B against staging.
4. Run full CI + smoke tests.
5. Only after staging passes, proceed to hosted.

**Recommendation**: **Option C first, then Option A** — adopt hosted as baseline to minimize
destructive operations, validate against staging, then reconcile.

---

## 12. Do Not Reset Hosted Supabase

```
╔══════════════════════════════════════════════════════════════╗
║  NEVER RUN:                                                 ║
║    supabase db reset                                        ║
║    DROP SCHEMA public CASCADE                               ║
║    ALLOW_DESTRUCTIVE_DB_TESTS=true                          ║
║                                                             ║
║  AGAINST HOSTED SUPABASE.                                   ║
╚══════════════════════════════════════════════════════════════╝
```

The hosted instance has its schema initialized. Resetting would lose the existing
configuration, auth settings, and any future data. Even though the database is
currently empty, a reset is irreversible and destroys the project-level Supabase
configuration.

---

## 13. Approval Checklist Before Any Future Migration

- [ ] Hosted schema fully dumped and backed up
- [ ] Staging Supabase project created (separate from hosted)
- [ ] Reconciliation migration tested against staging
- [ ] `verify` CI job passes against staging
- [ ] `reset-reapply` CI job passes against staging
- [ ] `rollback-test` CI job passes against staging
- [ ] `schema-policy-audit` CI job passes against staging
- [ ] `Web App Quality` CI job passes
- [ ] Full smoke test passes against staging
- [ ] Auth/RLS test suite passes against staging
- [ ] User decisions documented (enum name, column preferences)
- [ ] Written approval received
- [ ] Rollback plan ready

---

## 14. Rollback/Backup Requirements

**Before any migration**:
1. Export full hosted schema: `pg_dump --schema-only --no-owner postgresql://... > backup_schema.sql`
2. Export hosted data (if any): `pg_dump --data-only --no-owner postgresql://... > backup_data.sql`
3. Document the current Supabase project configuration (auth, redirect URLs, etc.)

**After migration**:
1. Run `schema-policy-audit` script against hosted to verify schema matches expectations.
2. Run auth/RLS test suite to verify policies still work.
3. Run smoke tests against hosted.

**Rollback**:
1. If migration fails: restore from backup schema + data dumps.
2. If rollback fails: contact Supabase support for point-in-time recovery.
3. Document the failure and create a new migration to fix it.

---

## User Decisions Required

The following decisions must be made before reconciliation:

### Decision 1: Enum Name
- **Option A**: Rename local `transaction_event_type` → `transaction_types` (match hosted)
- **Option B**: Rename hosted `transaction_types` → `transaction_event_type` (match local)
- **Option C**: Keep both as aliases (not recommended — adds complexity)

### Decision 2: Column Naming — `tax_amount` vs `tax`
- **Option A**: Rename local `tax_amount` → `tax` (match hosted)
- **Option B**: Rename hosted `tax` → `tax_amount` (match local)

### Decision 3: Extra Columns on Hosted
- `securities.asset_class` — add to local migration? (Y/N)
- `securities.superseded_by` — add to local migration? (Y/N)
- `model_snapshot_holdings.prior_rank` — add to local migration? (Y/N)
- `model_snapshot_holdings.change_from_prior` — add to local migration? (Y/N)
- `model_snapshot_holdings.data_quality_flags` — add to local migration? (Y/N)
- `portfolios.starting_cash` — add to local migration? (Y/N)
- `portfolios.benchmark_ticker` — add to local migration? (Y/N)
- `transactions.fx_rate` — add to local migration? (Y/N)

### Decision 4: Missing Local Tables in Hosted
- `model_publication_events` — create on hosted? (Y/N)
- `portfolio_valuations` — create on hosted? (Y/N)

### Decision 5: Reconciliation Strategy
- **Option A**: Adopt hosted as baseline
- **Option B**: Replace with local migration
- **Option C**: Staging rehearsal first (recommended)

---

## Conclusion

```
╔══════════════════════════════════════════════════════════════╗
║  RECONCILIATION BLOCKED — CONTRADICTORY HOSTED SCHEMA       ║
║  FINDINGS RESOLVED                                          ║
║                                                             ║
║  The earlier inspection report incorrectly claimed          ║
║  audit_events, data_imports, and owner_decisions were       ║
║  hosted-only tables. All three exist in the local           ║
║  migration (00001_schema.sql). The error was caused by      ║
║  comparing against a mental model rather than reading the   ║
║  actual migration file.                                     ║
║                                                             ║
║  Corrected finding: 0 hosted-only tables, 2 local-only      ║
║  tables, 15 tables in both.                                 ║
║                                                             ║
║  Remaining conflicts: enum name mismatch, column diffs      ║
║  in 4 tables. 5 user decisions required before migration.   ║
╚══════════════════════════════════════════════════════════════╝
```
