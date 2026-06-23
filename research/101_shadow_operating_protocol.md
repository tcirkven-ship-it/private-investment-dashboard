# Shadow operating protocol

## Missing-Quality behavior

- Computation: annual statements with 3-month publication lag
- Coverage: bottom 10% excluded only among stocks with valid composite Quality
- Missing: stocks without valid composite Quality remain eligible (not excluded)
- Label: DATA_COVERAGE_INSUFFICIENT — not excluded but flagged in report
- Min components: at least 2 of 4 Quality factors must be non-missing for a valid composite

## Activation status

| Model | Status |
|---|---|
| A3_P100 | INITIALIZED |
| A3_G3_QUALITY_VETO | INITIALIZED |
| B2_P100 | INITIALIZED |
| B2_G3_QUALITY_VETO | INITIALIZED |
| SPY | INITIALIZED |
| QQQ | INITIALIZED |

## First decision

The first legitimate prospective decision requires a fresh integrity-passed
scanner snapshot generated on or after the activation date (2026-06-23).
The June 22, 2026 snapshot is NOT a valid prospective decision because
it predates activation. Do not backfill.

## Idempotency

The shadow runner checks whether a given decision date has already been
processed before applying any transactions. Rerunning the same date
produces no duplicate events.