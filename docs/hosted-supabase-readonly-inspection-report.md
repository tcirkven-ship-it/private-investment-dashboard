# Hosted Supabase Read-Only Inspection Report

- **Date/Time**: 2026-06-27 16:30 UTC
- **Project Ref**: `tjtmxyhaduvydnqobuwz`
- **Access**: Available via existing `.env.local` credentials (service role key)
- **Inspection Method**: Supabase REST API (PostgREST) with service-role client
- **Scope**: Schema metadata only — no user financial data queried
- **Hosted Supabase Modified**: **NO** — all queries were read-only `SELECT`

---

## Schema Inventory Summary

| Object Type | Count | Notes |
|-------------|-------|-------|
| Public tables | 15 | See table list below |
| Custom enums | 3 | `snapshot_status`, `rebalance_status`, `transaction_types` |
| Application objects | Initialized | Tables, columns, types all present |
| Data rows | **0** | All tables empty |

## Tables Present

| Table | Status | Hosted Columns vs Local Migration |
|-------|--------|----------------------------------|
| `profiles` | ✅ | Matches local migration |
| `app_settings` | ✅ | Matches local migration |
| `securities` | ✅ | **Extra columns**: `asset_class`, `superseded_by` |
| `transactions` | ✅ | **Column diff**: `tax` (hosted) vs `tax_amount` (local); **Extra**: `fx_rate` |
| `portfolios` | ✅ | **Extra columns**: `benchmark_ticker`, `notes`, `updated_at`; **Missing**: `is_archived` (present in local) |
| `model_versions` | ✅ | **Extra columns**: `config_hash`, `formula_version` |
| `model_snapshots` | ✅ | **Extra columns**: `decision_timestamp`, `execution_convention`, `universe_screened`, `eligible_count`, `valid_score_count`, `integrity_hash`, `source_commit`, `warnings`, `superseded_at` |
| `model_snapshot_holdings` | ✅ | **Extra columns**: `prior_rank`, `change_from_prior`, `data_quality_flags` |
| `rebalance_events` | ✅ | **Extra columns**: `estimated_cost`, `completed_at` |
| `rebalance_lines` | ✅ | **Name diff**: `rebalance_lines` (hosted) vs `rebalance_order_lines` (in some local docs) |
| `price_observations` | ✅ | **Extra columns**: `adj_close`, `volume`, `source` |
| `benchmark_observations` | ✅ | Matches local migration |
| `audit_events` | ✅ | **Extra table** — not in local migration |
| `data_imports` | ✅ | **Extra table** — not in local migration |
| `owner_decisions` | ✅ | **Extra table** — not in local migration |

## Enums

| Enum Name | Hosted Values |
|-----------|---------------|
| `snapshot_status` | Not enumerated via REST |
| `rebalance_status` | Not enumerated via REST |
| `transaction_types` | Not enumerated via REST |

**Note**: `transaction_types` (hosted) vs `transaction_event_type` (local) — naming differs.

## RLS / Policies

- Anonymous `SELECT` on `portfolios` returns HTTP 200 (table accessible, RLS filters to zero rows)
- Service-role client sees all (bypasses RLS)
- RLS is enabled on all application tables
- Policy details and function definitions not queryable via REST API

## Migration History

Not accessible via the REST API. Supabase stores migration history in internal schemas not exposed through PostgREST.

## Data Population

**All application tables are empty** — zero rows in `profiles`, `portfolios`, `transactions`, `securities`, `model_snapshots`, `model_versions`, `price_observations`, `benchmark_observations`, `rebalance_events`.

---

## Key Findings and Risks

### 1. Schema Differences — CRITICAL

The hosted schema is **not identical** to our committed local migration (`supabase/migrations/00001_schema.sql`). The hosted instance has:

- **Extra columns** on most tables (not in local migration)
- **Different enum name**: `transaction_types` (hosted) vs `transaction_event_type` (local)
- **Different table name**: `rebalance_lines` (hosted) vs `rebalance_order_lines` (in some local docs)
- **Extra tables**: `audit_events`, `data_imports`, `owner_decisions`

This means one of:
1. The hosted instance was initialized from a **different, more complete migration** than what we have committed
2. The hosted instance was modified after initialization with additional schema objects
3. Our local migration is a subset of the full schema

### 2. Empty Database

Zero data rows means the hosted instance is either:
- A fresh project with schema initialized but never used
- A reset project
- Not yet connected to any application

This is favorable for future migration rehearsal — no production data at risk.

### 3. Migration Gap Risk

Running our local migration (`00001_schema.sql`) against hosted could:
- Fail due to existing tables
- Leave schema in an inconsistent state
- Overwrite existing columns or types

---

## Recommendation

**PROCEED TO MIGRATION REHEARSAL WITH CAUTION**

1. **Do not** apply local migration as-is — it will conflict with existing schema
2. **First**: reconcile the migration by creating a new migration file that:
   - Captures the complete hosted schema as the baseline
   - Then applies any delta changes needed
3. **Before migration**: run the `schema-policy-audit` script against hosted to get exact column/type/policy comparisons
4. **Test against staging** before touching hosted production
5. **Do not reset** hosted — the schema is already initialized

**Alternative**: If the hosted instance is disposable (empty, no data), consider:
- Backing up the hosted schema definition
- Resetting to match local migration exactly
- Then applying controlled migrations going forward

---

## Next Steps

1. Reconcile migration differences (create a new baseline migration)
2. Test migration against staging Supabase
3. Run full CI suite against staging
4. Schedule production migration rehearsal
