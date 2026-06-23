# Price persistence experiment — decision

> Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.

## Determinations

| Candidate | Specification | Classification |
|---|---|---|
| A3 | base/min3/rank90/entry2 | FAIL (turnover > 250%) |
| A3 | exit2 | FAIL (DD vs SPY per fold: −15.09pp, threshold −15pp) |
| A3 | combined | FAIL (absolute max DD: −44.38%, threshold −40%) |
| B2 | base/min3/rank90/entry2 | FAIL (turnover > 250%) |
| B2 | exit2 | FAIL (DD vs SPY per fold: −15.83pp) |
| B2 | combined | FAIL (absolute max DD: −43.12%) |
| D1 | all | FAIL (max DD > 40% and DD vs SPY > 15pp for all) |

## Summary

**No specification passes every development gate.** The closest is A3 with two-consecutive-below-60 exit confirmation (64% turnover, 24.69% return, 6/6 SPY wins) but it fails the DD-vs-SPY-per-fold threshold by 0.09pp in the 2016 fold.

The two-consecutive-below-60 exit confirmation is a meaningful mechanical improvement that can be considered for any future practical portfolio implementation — it dramatically reduces whipsaw turnover. But it does not resolve the fundamental drawdown limitations of the Price signals themselves.

## Broader conclusion

**Price-only signal research is exhausted under the current yfinance survivor-biased dataset.**

Every candidate from Price Generation 2 (families A–E) and every mechanical variant in the persistence experiment has failed at least one preregistered gate. The limitations are structural:

1. Turnover from the rank-60 buffer (base: 311–618%)
2. Drawdown concentration in certain years (2016, 2018, 2020)
3. Inability to achieve positive QQQ-relative returns without extreme turnover
4. Survivor bias inflating point estimates

A robust Price signal may still exist but cannot be demonstrated with the available data. The forward evidence ledger and paid-data preparation remain the only viable paths for QVP validation.

## Required update

- The Price component in the YF-QVP scanner is frozen and technically functional.
- No change to the current QVP weights, factors, or scanner is authorized.
- No new Price signal research under yfinance is justified.
