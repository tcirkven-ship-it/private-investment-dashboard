# Private Investment Dashboard — Row Level Security Matrix

## Policy pattern

All private tables use the same base policy: `owner_id = auth.uid()`. Published model data and security reference data are world-readable to the authenticated owner.

## Matrix

| Table | SELECT | INSERT | UPDATE | DELETE | Notes |
|---|---|---|---|---|---|
| profiles | owner matches | admin only, via trigger | owner only | never | Created by auth trigger |
| app_settings | owner matches | never | owner only | never | |
| securities | authenticated | admin/service key | admin/service key | admin/service key | Read-only reference data |
| model_versions | authenticated | service key | never | never | Immutable after creation |
| model_snapshots | authenticated | service key, draft status | status transition only | never | Cannot delete published snapshots |
| model_snapshot_holdings | authenticated | service key | never | never | Immutable |
| portfolios | owner matches | owner only | owner only | owner only (soft: is_archived) | |
| transactions | owner matches (via portfolio) | owner only (via portfolio) | never (correction only) | never (correction only) | Correction adds new event |
| price_observations | authenticated | service key | never | never | |
| portfolio_valuations | owner matches (via portfolio) | — | — | — | Computed or imported |
| benchmark_valuations | authenticated | service key | never | never | |
| rebalance_events | owner matches (via portfolio) | service key | owner only | never | |
| rebalance_lines | owner matches (via event → portfolio) | service key | never | never | |
| audit_events | owner matches | service only | never | never | Append-only |

## Service-role operations

The following operations use the Supabase service-role key and never execute in the browser:

- Importing model snapshots
- Importing price observations
- Creating model_versions and model_snapshots
- Writing audit_events for model import operations

## Status transition rules

model_snapshots.status transitions:

```
DRAFT → VALIDATED → APPROVED → PUBLISHED → SUPERSEDED
  ↑          |            |
  └──────────┴────────────┘ (reject only)
```

- Only forward transitions allowed
- PUBLISHED can only move to SUPERSEDED
- SUPERSEDED is final

## Special cases

- Transaction deletion is physically prevented. Corrections create new transaction events with `corrected_by` referencing the corrected event.
- Portfolio deletion is prevented after first transaction. Use `is_archived = true` instead.
- Security ticker changes create a new security record; the old ticker is marked inactive with `superseded_by` pointing to the new record.
