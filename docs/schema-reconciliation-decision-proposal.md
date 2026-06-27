# Schema Reconciliation Decision Proposal

> **Warning**: Do not run migrations against hosted Supabase until this proposal is approved.
> Do not reset hosted Supabase. Do not drop hosted objects.
> This is a planning document only — no executable migration changes are generated.

---

## Recommended Strategy

**Option C — Staging rehearsal first**

Create a separate staging Supabase project, replicate the hosted schema to it,
test all reconciliation steps against staging, and only after full CI + smoke-test
passing proceed to hosted.

## Why Option C is Safest

1. **No risk to hosted** — all destructive testing happens on staging.
2. **Realistic validation** — staging mirrors hosted schema exactly, so migration
   scripts are validated against the actual target structure.
3. **Enum rename safety** — renaming `transaction_types` ↔ `transaction_event_type`
   can be tested with `ALTER COLUMN ... TYPE ... USING` and verified against staging
   before touching hosted.
4. **Column reconcile safety** — `ALTER TABLE ... ADD/DROP COLUMN` can be tested
   for side effects (e.g., if `tax` and `tax_amount` both exist).
5. **Policy/trigger/function diff** — staging allows a direct `psql` comparison
   of procedural objects not visible via REST API.
6. **Rollback rehearsal** — staging can be reset and recreated at will, allowing
   rollback procedure testing.

## Risks of Option A (Adopt Hosted as Baseline)

| Risk | Detail |
|------|--------|
| **Silent drift** | Adopting hosted schema without understanding why it differs from local migration may embed unknown legacy decisions. |
| **Lost local structure** | Local-only tables (`model_publication_events`, `portfolio_valuations`) could be forgotten if the baseline does not include them. |
| **Unintended column retention** | Hosted columns like `asset_class`, `superseded_by` may have been added experimentally — adopting them permanently may not be desired. |

## Risks of Option B (Replace with Local Migration)

| Risk | Detail |
|------|--------|
| **Enum CASCADE** | `DROP TYPE transaction_types CASCADE` will cascade to `transactions.event_type` and potentially other dependent objects — could break the column type silently. |
| **Existing table conflict** | `CREATE TABLE` on an existing table will fail — each table would need `IF NOT EXISTS` handling. |
| **Column mismatch** | `tax_amount` vs `tax` — dropping the wrong column or keeping both creates application confusion. |
| **Policy loss** | Dropping and recreating tables would drop all RLS policies and require full re-application. |
| **Irreversible on hosted** | Unlike staging, a failed replacement on hosted requires a full schema restore from backup. |

---

## Item-by-Item Analysis

### 1. Enum Mismatch — `transaction_event_type` vs `transaction_types`

| Aspect | Detail |
|--------|--------|
| Hosted name | `transaction_types` |
| Local name | `transaction_event_type` |
| Values | Both contain the same enum values (DEPOSIT, WITHDRAWAL, BUY, SELL, etc.) |
| Classification | **Rename/migrate** |
| Recommendation | Adopt `transaction_types` (hosted name) as the canonical name. Rename references in the local migration to match. The application code references the enum values, not the type name, so the name change has no application impact. |
| Safety | Must use `ALTER COLUMN ... TYPE ... USING event_type::text::transaction_types` — test on staging first. |

### 2. Column Naming — `tax` vs `tax_amount`

| Aspect | Detail |
|--------|--------|
| Hosted name | `tax` (numeric) |
| Local name | `tax_amount` (not in local migration — local has `tax_amount` in `TransactionData` interface) |
| Classification | **Rename/migrate** |
| Recommendation | Adopt `tax` (hosted name). Update the local migration and application types to use `tax`. The rename simplifies alignment and avoids confusion between `tax_amount` (local migration column not present) and `commission` (separate column). |
| Safety | Test in staging: verify existing TypeScript interfaces, adapter functions, and holdings engine still compile and pass tests. |

### 3. Extra Hosted Columns

#### `securities.asset_class`

| Aspect | Detail |
|--------|--------|
| Type | text |
| Purpose | Asset class classification (stock, ETF, bond, etc.) |
| Classification | **Adopt into committed schema** |
| Recommendation | Add to local migration. Useful for filtering and reporting. No data risk — hosted is empty. |

#### `securities.superseded_by`

| Aspect | Detail |
|--------|--------|
| Type | uuid (references securities.id) |
| Purpose | Ticker symbol change tracking (e.g., when a company rebrands) |
| Classification | **Adopt into committed schema** |
| Recommendation | Add to local migration. Supports symbol change workflow. |

#### `model_snapshot_holdings.prior_rank`

| Aspect | Detail |
|--------|--------|
| Type | integer |
| Purpose | Tracks rank changes between model versions |
| Classification | **Adopt into committed schema** |
| Recommendation | Add to local migration. Useful for rebalance drift analysis. |

#### `model_snapshot_holdings.change_from_prior`

| Aspect | Detail |
|--------|--------|
| Type | text |
| Purpose | Description of rank change (new, promoted, demoted, removed, unchanged) |
| Classification | **Adopt into committed schema** |
| Recommendation | Add to local migration. Useful for rebalance drift analysis. |

#### `model_snapshot_holdings.data_quality_flags`

| Aspect | Detail |
|--------|--------|
| Type | text[] |
| Purpose | Array of quality flags (e.g., low_liquidity, stale_price) |
| Classification | **Adopt into committed schema** |
| Recommendation | Add to local migration. Useful for transparency into model decisions. |

#### `portfolios.starting_cash`

| Aspect | Detail |
|--------|--------|
| Type | numeric |
| Purpose | Initial cash balance at portfolio creation |
| Classification | **Adopt into committed schema** |
| Recommendation | Add to local migration. The application mentions `starting_cash` in mock data — the column should exist. |

#### `portfolios.benchmark_ticker`

| Aspect | Detail |
|--------|--------|
| Type | text |
| Purpose | Default benchmark ticker for performance comparison |
| Classification | **Adopt into committed schema** |
| Recommendation | Add to local migration. Already referenced in some route stubs. |

#### `transactions.fx_rate`

| Aspect | Detail |
|--------|--------|
| Type | numeric |
| Purpose | Foreign exchange rate if transaction currency differs from portfolio currency |
| Classification | **Adopt into committed schema** |
| Recommendation | Add to local migration. Single-currency MVP does not need it yet, but harmless to include. |

### 4. Local-Only Tables

#### `model_publication_events`

| Aspect | Detail |
|--------|--------|
| Purpose | Audit trail for model snapshot status transitions |
| Classification | **Preserve as-is (local only), create on hosted** |
| Recommendation | Include in the reconciliation migration that creates it on hosted. No data risk — no existing rows. |

#### `portfolio_valuations`

| Aspect | Detail |
|--------|--------|
| Purpose | Derived portfolio valuation snapshots for performance charting |
| Classification | **Preserve as-is (local only), create on hosted** |
| Recommendation | Include in the reconciliation migration that creates it on hosted. No data risk — no existing rows. |

### 5. Disputed Tables — `audit_events`, `data_imports`, `owner_decisions`

| Table | In Hosted? | In Local Migration? | Classification |
|-------|-----------|-------------------|---------------|
| `audit_events` | **Yes** | **Yes** (line 419) | **Both — no action needed** |
| `data_imports` | **Yes** | **Yes** (line 403) | **Both — no action needed** |
| `owner_decisions` | **Yes** | **Yes** (line 390) | **Both — no action needed** |

These three tables exist in both hosted and local. The earlier inspection report
incorrectly flagged them as "hosted-only" due to comparing against a mental model
rather than reading the actual migration file. No reconciliation needed.

---

## User Decisions Required

| # | Decision | Options | Recommended |
|---|----------|---------|-------------|
| 1 | Enum name | (a) Adopt `transaction_types` / (b) Rename to `transaction_event_type` | **Adopt hosted `transaction_types`** |
| 2 | Column naming: `tax` vs `tax_amount` | (a) Adopt hosted `tax` / (b) Rename to `tax_amount` | **Adopt hosted `tax`** |
| 3 | `securities.asset_class` | Adopt or drop | **Adopt** |
| 4 | `securities.superseded_by` | Adopt or drop | **Adopt** |
| 5 | `model_snapshot_holdings.prior_rank` | Adopt or drop | **Adopt** |
| 6 | `model_snapshot_holdings.change_from_prior` | Adopt or drop | **Adopt** |
| 7 | `model_snapshot_holdings.data_quality_flags` | Adopt or drop | **Adopt** |
| 8 | `portfolios.starting_cash` | Adopt or drop | **Adopt** |
| 9 | `portfolios.benchmark_ticker` | Adopt or drop | **Adopt** |
| 10 | `transactions.fx_rate` | Adopt or drop | **Adopt** |
| 11 | `model_publication_events` on hosted | Create or skip | **Create** |
| 12 | `portfolio_valuations` on hosted | Create or skip | **Create** |
| 13 | Reconciliation strategy | Option A / B / C | **Option C (staging first)** |

---

## Backup Requirements (Before Any Migration)

1. **Export hosted schema**: `pg_dump --schema-only --no-owner <connection> > hosted-schema-backup.sql`
2. **Document Supabase project settings**: Auth providers, redirect URLs, site URL, API settings.
3. **Export any existing data**: If data exists by migration time, back it up.
4. **Store backups securely**: Outside the repository, in a versioned location.

---

## Staging Rehearsal Plan

1. **Create staging Supabase project** (separate from hosted).
2. **Restore hosted schema to staging** via `psql` from the backup dump.
3. **Run the reconciliation migration** against staging.
4. **Run all CI verification jobs** against staging:
   - `verify`
   - `reset-reapply`
   - `rollback-test`
   - `schema-policy-audit`
5. **Run auth/RLS tests** against staging.
6. **Run Web App Quality** (lint, test, build).
7. **Run full smoke test** against staging.
8. **Fix any failures** and iterate.
9. **Only after staging is fully green**, schedule the hosted migration.

---

## What Must Not Happen on Hosted Production

- **No `DROP TYPE ... CASCADE`** without explicit approval and backup.
- **No `DROP TABLE`** without explicit approval.
- **No `TRUNCATE`** on any table.
- **No `supabase db reset`** under any circumstances.
- **No `ALLOW_DESTRUCTIVE_DB_TESTS=true`** against hosted.
- **No migrations during market hours** if the application is live.

---

## Rollback/Restore Requirements

| Scenario | Action |
|----------|--------|
| Migration step fails | Stop, restore from schema backup, fix migration, retry on staging |
| Data type change breaks app | Restore from schema backup, revert to previous migration |
| Policy loss detected | Re-apply RLS policies from the migration file |
| Irrecoverable state | Contact Supabase support for point-in-time recovery |

---

## Next PR Recommendation

After this proposal is approved, the next PR should:

1. Create a staging Supabase project (manual step).
2. Export hosted schema to a backup file.
3. Create the reconciliation migration file (`supabase/migrations/00003_schema_reconciliation.sql`).
4. Run CI against staging Supabase.
5. Verify all workflows pass.
6. Open a PR for hosted migration approval.

Do not skip staging. Do not merge a migration PR until staging CI is fully green.

---

## Conclusion

```
╔══════════════════════════════════════════════════════════════╗
║  DECISION PROPOSAL READY — USER APPROVAL REQUIRED           ║
║  DEPLOYMENT BLOCKED — STAGING REHEARSAL REQUIRED            ║
║                                                             ║
║  Recommended: Option C (staging rehearsal first).           ║
║  Adopt hosted enum name `transaction_types`.               ║
║  Adopt hosted column name `tax`.                            ║
║  Adopt all 8 extra hosted columns.                          ║
║  Create 2 local-only tables on hosted.                      ║
║  3 disputed tables (audit_events, data_imports,             ║
║  owner_decisions) exist in both — no action needed.         ║
║                                                             ║
║  13 user decisions listed above — all with                  ║
║  recommended choices.                                       ║
╚══════════════════════════════════════════════════════════════╝
```
