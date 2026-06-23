# Price Generation 2 — decision (Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.)

**No candidate passed every development gate.**
P4_CONTROL remains the only evaluated reference.

Total candidates tested: 20
Passed development: 0

## Decision classification

**FAIL** — no candidate passed development gates.

**P4 (failed control) determination: FAIL** (reaffirmed).

## Summary

The available yfinance survivor-biased data does not support a credible standalone
Price signal under practical portfolio mechanics. Turnover is the primary constraint:
entry and exit churn from the rank-60 buffer drives 93%+ of all turnover regardless of
which composite signal is used. No candidate in this generation passed every development
gate with turnover below 250% and positive benchmark-relative median return.

A robust Price signal may still exist, but cannot be demonstrated with the current
survivor-biased universe and limited historical depth. The evidence ceiling is
INCONCLUSIVE for true historical US equity markets.