# QVP integration — historical proxy results

**Evidence label:** Exploratory survivor-biased historical Price research

## P100 baseline (immediate rank-60 exit, no exit confirmation)

| Backbone | Ann ret | SPY-rel | QQQ-rel | Vol | Max DD | TO | Avg holding (days) |
|---|---:|---:|---:|---:|---:|---:|---:|
| A3 P100 | +24.3557% | +11.6854% | +2.9318% | +26.3866% | -39.4966% | 0.65 | 0 |
| B2 P100 | +23.4157% | +10.7454% | +1.9918% | +25.8390% | -38.3185% | 0.65 | 0 |

## Historical QVP proxy — NOT COMPUTED

A full historical QVP comparison requires computing Quality and Value
factors from historical statement data with conservative filing lags.
This requires:

1. Extracting trailing-12m income/cash-flow/balance-sheet data for each
   historical score date from the available annual/quarterly statements.
2. Applying a 3-month publication lag to approximate filing dates.
3. Computing Enterprise Value (for Value factors) using historical price
   × current shares outstanding as an approximate proxy.

The Quality factors (ROA, GPA, FCF_MARGIN, DEBT_ASSETS) can be computed
from annual statements only, which provides approximately one data point
per year per stock. This gives 4 factor-level observations that change
annually rather than monthly — which is exactly the stabilizing effect
that Q/V overlay is expected to provide.

**Not computed in this task** because the infrastructure to extract
historical statement data for arbitrary historical score dates does not
yet exist. Building it would require significant engineering.

Pending recommendation: INCONCLUSIVE — QVP historical proxy computation
requires a dedicated implementation task before any conclusion can be drawn.
However, the current architecture comparison (Part 2) shows that Q/V
overlays meaningfully change portfolio membership, which is a necessary
prerequisite for any stabilizing effect.