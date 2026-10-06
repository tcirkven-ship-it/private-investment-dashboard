# INVALIDATION NOTE — 2026-Q3 stale-source export

**Folder:** `2026-Q3_asof-2026-09-30_generated-2026-10-06_1328` (renamed with `INVALID_stale-source_` prefix on 2026-10-06)
**csv_sha256:** `649b271c826f`

## Why invalid

This export was built from the stale source snapshot `2026-07-01T053352Z` (July data) and
relabeled as `2026-Q3` / `as_of 2026-09-30`. The generator's `--as-of` override rewrote the factor
input date while the underlying data remained July; the old validation compared the relabeled date
against itself and passed. See `research/decision_log.md` DEC-064.

## Superseded by

`2026-Q3_asof-2026-09-30_generated-2026-10-06_1724`
- source_snapshot_id: `2026-10-06T142958Z` (data date 2026-10-06, 6 days after as_of)
- csv_sha256: `bb5f7ce025b4`
- validation: PASSED with the new freshness gates

## App-side handling

The app snapshot loaded from this invalid export was `nb-muwq0av2`
(generated_at `2026-10-06T13:28:19.932925+00:00`).
It is invalidated by SQL migration `web/supabase/migrations/00007_snapshot_invalidation.sql`,
which sets its status to `SUPERSEDED` and records the invalidation reason in `warnings`.

Invalid or superseded snapshots are excluded from Top 30 and Compare defaults and from the
snapshot history selector by the app's `PUBLISHED`-only queries.

## Retention

Do not delete. This folder is retained as audit evidence per the quarterly export retention policy
(see iCloud backup README: `InvestmentTrackerBackups/README.md`).
