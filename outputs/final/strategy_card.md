# Strategy card — C03-M research candidate

**Status:** FAIL — paper research only; not approved for live use  
**Objective:** Test whether liquid mega-cap 12–1 momentum can outperform contribution-matched SPY and QQQ after costs.

| Element | Frozen research rule |
|---|---|
| Universe | Current 2026-06-18 OEF US equity holdings, one share class per issuer |
| Eligibility | 252 observations; price ≥ $5; prior-63-session median dollar volume ≥ $5m |
| Signal | Adjusted total return from session -252 through session -21 |
| Portfolio | Top 30; equal-weight target |
| Entry | Highest ranks subject to 25% target sector cap |
| Normal exit | Rank worse than 60 or hard eligibility failure |
| Review | Monthly after close; next-session modeled fill |
| Weight correction | Quarterly |
| Contribution | $250 weekly to at most three largest underweights; $25 minimum paper order |
| Risk limits | 7.5% name drift; 30% sector drift; no leverage or shorting |
| Benchmarks | Contribution-matched SPY and QQQ |
| Expected cost | $0.35/order + 5 bps one-way price impact |
| Observed turnover | 172–184% annualized — failed |
| Main weaknesses | Survivorship bias, no delistings/PIT fundamentals, QQQ holdout failure, instability, execution burden |

## Suspension conditions

Suspend paper tracking on data-reconciliation failure, future-data leakage, undocumented rule change, unresolved corporate action, persistent constraint breach or an attempt to reuse the completed holdout.

## Final determination

The candidate is not a validated investment strategy. Its favorable full-sample history is insufficient for deployment.
