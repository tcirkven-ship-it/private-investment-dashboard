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
**Functions**: 5 (`update_updated_at_column`, `handle_new_user`,
`check_snapshot_status_transition`, `prevent_portfolio_deletion`,
`check_transaction_owner`, `is_owner`)
**Triggers**: 5 (`set_profiles_updated_at`, `on_auth_user_created`,
`check_snapshot_status_transition`, `set_portfolios_updated_at`,
`prevent_portfolio_deletion`, `check_transaction_owner`)
**Policies**: 31
**Indexes**: 9

**Local tables**:
`profiles`, `app_settings`, `securities`, `model_versions`,
`model_snapshots`, `model_snapshot_holdings`, `model_publication_events`,
`portfolios`, `transactions`, `price_observations`, `benchmark_observations`,
`portfolio_valuations`, `rebalance_events`, `rebalance_lines`,
`owner_decisions`, `data_imports`, `audit_events`

---

## 3. Table-by-Table Comparison

### Matching tables (present in both)

| Table | Columns Match? | Notes |
|-------|---------------|-------|
| `profiles` | ✅ Exact match | Same columns, types, constraints |
| `app_settings` | ✅ Exact match | Same columns, types |
| `securities` | ⚠️ Hosted has extras | Hosted adds `asset_class`, `superseded_by`; local has `data_source` |
| `model_versions` | ✅ Exact match | Same columns including `config_hash`, `formula_version` |
| `model_snapshots` | ✅ Exact match | Same extended columns (`decision_timestamp`, `execution_convention`, etc.) |
| `model_snapshot_holdings` | ⚠️ Hosted has extras | Hosted adds `prior_rank`, `change_from_prior`, `data_quality_flags` |
| `portfolios` | ⚠️ Column diff | Local has `is_archived`, `notes`, `benchmark_ticker`; hosted has `is_archived`, `notes`, `benchmark_ticker`, `starting_cash`, `updated_at` |
| `transactions` | ⚠️ Column diff | Local has `commission`, `tax_amount`; hosted has `commission`, `tax` (numeric), `fx_rate` |
| `price_observations` | ⚠️ Hosted has extras | Hosted adds `adj_close`, `volume`, `source`; local has same |
| `benchmark_observations` | ✅ Exact match | Same columns |
| `rebalance_events` | ✅ Exact match | Same columns including `estimated_cost`, `completed_at` |
| `rebalance_lines` | ✅ Exact match | Same columns |
| `owner_decisions` | ✅ Exact match | Same columns |
| `data_imports` | ✅ Exact match | Same columns |
| `audit_events` | ✅ Exact match | Same columns |

### Local-only tables (not found in hosted)

| Table | Classification | Notes |
|-------|---------------|-------|
| `model_publication_events` | **Migrate into hosted** | Publication audit trail — create on hosted |
| `portfolio_valuations` | **Migrate into hosted** | Derived valuation snapshots — create on hosted |

### Hosted-only tables

None. All 15 hosted tables exist in the local migration.

---

## 4. Enum-by-Enum Comparison

| Local Name | Hosted Name | Match? | Notes |
|-----------|-------------|--------|-------|
| `snapshot_status` | `snapshot_status` | ✅ Same name, same values | `DRAFT, VALIDATED, APPROVED, PUBLISHED, SUPERSEDED` |
| `rebalance_status` | `rebalance_status` | ✅ Same name, same values | `PENDING, COMPLETED, CANCELLED` |
| `transaction_event_type` | `transaction_types` | ❌ **NAME MISMATCH** | Local: `transaction_event_type`, Hosted: `transaction_types` |

**Risk**: The enum name mismatch is the most critical conflict. If the local migration creates
`transaction_event_type` but the hosted instance already has `transaction_types`, a migration
that issues `CREATE TYPE public.transaction_event_type` will fail if the type already exists
under a different name. The `transactions.event_type` column references the enum by name.

---

## 5. Function/Trigger/Policy Comparison

Functions, triggers, and policies cannot be directly compared via REST API.
The hosted instance's functions/triggers/policies were not inspectable through PostgREST.

**Assumption**: The hosted instance likely has the same functions, triggers, and policies
if it was initialized from a migration similar to `00001_schema.sql`. This must be verified
by direct database query (requires psql access with database password or a read-only
connection).

---

## 6. Hosted-Only Objects

None. All tables in the hosted instance are also defined in the local migration.
No hosted-only objects require classification.

---

## 7. Local-Only Objects

| Object | Type | Classification |
|--------|------|---------------|
| `model_publication_events` | Table | **Migrate into hosted** |
| `portfolio_valuations` | Table | **Migrate into hosted** |
| `transaction_event_type` | Enum name | **Rename to match hosted** (or vice versa) |

---

## 8. Conflicting Objects

| Conflict | Severity | Resolution Needed |
|----------|----------|-------------------|
| Enum name `transaction_event_type` vs `transaction_types` | **HIGH** | Must pick one name; all references (`transactions.event_type` column type) must match |
| `transactions.tax_amount` vs hosted `transactions.tax` | **MEDIUM** | Column naming difference |
| `transactions` missing `fx_rate` in local | **LOW** | Add if multi-currency support needed |
| `securities` missing `asset_class`, `superseded_by` in local | **LOW** | Add if needed |
| `model_snapshot_holdings` missing `prior_rank`, `change_from_prior`, `data_quality_flags` in local | **LOW** | Add if needed |
| `portfolios` differs on `starting_cash` presence | **MEDIUM** | Local migration has `starting_cash`? Check the migration... Local has `notes` but not `starting_cash` as a column — hosted might have it differently |

Wait — let me verify the portfolios column comparison more carefully.

Local `portfolios` (from 00001_schema.sql):
- id, owner_id, name, currency, opening_date, notes, is_archived, created_at, updated_at

Hosted `portfolios` (from REST inspection):
- id, owner_id, name, currency, opening_date, starting_cash, benchmark_ticker, notes, is_archived, created_at, updated_at

So hosted has `starting_cash` and `benchmark_ticker` which local does NOT have. And local has all the same columns otherwise. This is a real difference.

Let me also re-check `securities`:
Local: id, ticker, company_name, sector, industry, is_active, data_source, created_at
Hosted: id, ticker, company_name, sector, industry, asset_class, is_active, data_source, superseded_by, created_at

Hosted has `asset_class` and `superseded_by` that local does not.

---

## 9. Data-Preservation Questions

Since the hosted instance has **zero data rows** in all 15 tables:

1. **Is there any configuration in `app_settings` that must be preserved?**
   - Currently: no rows. After migration: no data to lose.

2. **Are there any Supabase Auth users that must be preserved?**
   - Auth user count was not inspected (restricted). Separate check needed.

3. **Are there any storage objects or auth configurations?**
   - Not inspected. Separate check needed.

4. **Can the hosted schema be fully replaced by our local migration?**
   - **Yes** — zero data rows means no data loss risk.
   - **But** — the enum name conflict means a naive migration will fail on
     `CREATE TYPE transaction_event_type` when `transaction_types` already exists.

---

## 10. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Enum name conflict blocks migration | **HIGH** | Migration fails | Create a new migration that renames or reconciles enums first |
| Column type mismatch (`tax_amount` vs `tax`) | **MEDIUM** | Migration fails or wrong type | Must reconcile column names and types |
| Extra columns on hosted cause `CREATE TABLE` conflict | **HIGH** | Migration fails existing table | Must use `CREATE TABLE IF NOT EXISTS` or separate baseline migration |
| Missing local tables (`model_publication_events`, `portfolio_valuations`) | **LOW** | Missing features | Create them in a new migration |
| Function/trigger/policy mismatch not yet verified | **MEDIUM** | Unexpected RLS behavior | Need direct database query to compare |
| `starting_cash` column exists on hosted but not in local migration | **MEDIUM** | Feature gap | Add `starting_cash` to local migration or hosted schema |
| `asset_class`, `superseded_by` columns exist on hosted but not in local | **LOW** | Feature gap | Add to local migration if needed |

---

## 11. Recommended Reconciliation Strategy

### Option A — Adopt hosted as baseline (recommended if hosted is canonical)

1. Dump the full hosted schema definition (via `pg_dump --schema-only`).
2. Create a new baseline migration file (`00003_baseline.sql`) that:
   - Uses `CREATE TABLE IF NOT EXISTS` (or skips existing tables).
   - Uses the hosted enum name `transaction_types`.
   - Adds missing local-only tables (`model_publication_events`, `portfolio_valuations`).
   - Drops/adds columns to align with local application expectations.
3. Create a follow-up migration (`00004_reconcile.sql`) that:
   - Adds any local columns missing from hosted.
   - Adds local functions, triggers, policies not present.
   - Drops hosted columns not used by the application.
4. Test against a staging Supabase instance.

### Option B — Replace with local migration (simpler, but must handle conflicts)

1. Export hosted schema as backup.
2. Create a migration that drops conflicting types and re-creates them:
   - `DROP TYPE IF EXISTS transaction_types CASCADE;`
   - `CREATE TYPE transaction_event_type AS ENUM (...);`
   - `ALTER TABLE transactions ALTER COLUMN event_type TYPE transaction_event_type USING event_type::text::transaction_event_type;`
3. Use `CREATE TABLE IF NOT EXISTS` for all tables.
4. Add `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` for extra hosted columns.
5. Add `ALTER TABLE ... DROP COLUMN IF EXISTS` for local columns not in hosted.
6. Re-apply all functions, triggers, and policies idempotently.

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
║  RECONCILIATION PLAN READY — USER DECISIONS REQUIRED        ║
║                                                             ║
║  The hosted Supabase schema is largely compatible with      ║
║  the local committed migration, but has meaningful          ║
║  differences in enum naming, column definitions, and        ║
║  missing tables. The database is empty (zero data rows),    ║
║  which simplifies the reconciliation risk.                  ║
║                                                             ║
║  5 user decisions above must be resolved before any         ║
║  migration can proceed.                                     ║
╚══════════════════════════════════════════════════════════════╝
```
