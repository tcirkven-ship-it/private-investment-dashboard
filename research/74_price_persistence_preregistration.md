# Price persistence experiment — preregistration

**Version:** PRICE-PERSISTENCE-1.0.0  
**Preregistered:** 2026-06-23, before any persistence computation  
**Parent:** Price Generation 2 (`research/67`–`research/71`)

> Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.

## Candidates (frozen shortlist from Gen2)

- A3: combined 12-1 and 6-1 momentum
- B2: momentum plus 50/200-day moving-average relationship
- D1: momentum per unit volatility (A3 / VOL252 ratio)
- E3 excluded per diagnostic audit (score-construction artifact)

## Mechanics specifications

Each candidate is tested with these six specifications:

| # | Name | Min hold | Exit confirm | Retention | Entry confirm |
|---|---|---|---|---|---|
| 1 | base | 0 | 0 | 2N (60) | 0 |
| 2 | min3 | 3 mo | 0 | 2N (60) | 0 |
| 3 | exit2 | 0 | 2 mo below rank | 2N (60) | 0 |
| 4 | rank90 | 0 | 0 | 3N (90) | 0 |
| 5 | entry2 | 0 | 0 | 2N (60) | 2 mo top-30 |
| 6 | combined | 3 mo | 2 mo below rank | 3N (90) | 2 mo top-30 |

## Revised development gates

A specification may become a finalist only if:

| Gate | Threshold |
|---|---|
| Annual gross turnover | < 250% (prefer < 200%) |
| Median active vs SPY | > 0% |
| Median active vs QQQ | > 0% |
| Fold wins vs SPY | >= 4 of 6 |
| Fold wins vs QQQ | >= 3 of 6 |
| Absolute max drawdown | < 40% |
| Max DD vs SPY per fold | not worse than 15pp |
| Max fold share of active SPY | < 60% |
| Best stock removal | does not eliminate advantage |
| Best year removal | does not eliminate advantage |
| N=20/30/40 direction | same sign across sizes |
| Suspicious series | not driving result |

## Evaluation

If one or more specifications pass all development gates, freeze no more than two finalists using:
1. Lowest turnover
2. Best median QQQ-relative
3. Lowest fold dependence
4. Lowest drawdown

Then evaluate on untouched 2021–2025 folds. If no specification passes, declare this Price research path exhausted under the current dataset.
