# Frozen Price-component historical backtest specification

**Version:** `PRICE-WF-1.0.0`  
**Preregistered:** 2026-06-23, before development or evaluation results  
**Scanner boundary:** commit `52aa05b859999b52d1352a54b8d7fe5bfb378873`; run `2026-06-22T172514Z`

> Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.

## Scope and immutable boundary

This experiment tests only the frozen Price category. It does not alter or
historically validate Quality, Value, Growth, YF-QVP, the daily scanner, the
current universe-retrieval correction, or the current compact outputs. All
code and results are isolated from those paths.

The historical proxy universe is the 1,069-name eligible set from the corrected
current scanner snapshot, projected backward. This improves cross-sectional
breadth over the earlier 100-name OEF proxy but does not repair survivorship,
inactive-listing, delisting-return, permanent-identifier, ticker-change, or
historical-market-cap limitations.

The preregistered attempt to retrieve maximum history for all 1,069 names was
blocked before the first completed ticker by Yahoo HTTP 429 throttling. The
frozen no-cost fallback is therefore the already validated local maximum-history
yfinance files intersected with the corrected 1,069-name set. Coverage—not an
assumed full 1,069 histories—must be reported by year, and this narrower support
further lowers the evidence ceiling. No three-year scanner history may be
silently treated as maximum history.

## Exact factors

At each completed session, using adjusted prices available through that close:

- `M12_1 = AdjClose[t-21] / AdjClose[t-252] - 1`;
- `M6_1 = AdjClose[t-21] / AdjClose[t-126] - 1`;
- `TREND200 = AdjClose[t] / mean(last 200 AdjClose) - 1`;
- `VOL252 = sample SD(last up to 252 daily log adjusted returns) × sqrt(252)`,
  requiring at least 200 returns and ranked inversely.

Each factor is winsorized at the date-specific 2.5th and 97.5th
cross-sectional percentiles, ranked with average percentile ranks, and equally
averaged. Every factor required by P1–P4 must exist. There are no fitted
coefficients or optimized factor weights.

## Preregistered grid

P1 uses `M12_1`; P2 adds `M6_1`; P3 adds `TREND200`; frozen-primary P4 adds
inverse `VOL252`. Each is tested at N=20/30/40, daily/weekly/biweekly/monthly
review, and immediate/rank-1.5N/rank-2N retention. Equal weights and zero costs
are primary. This is 144 unconstrained configurations plus 144
current-classification-constrained sensitivities.

Unconstrained results are primary. The constrained sensitivity applies the
current 25% sector cap, 15% industry cap, current issuer/share-class deduplication,
and historical price/liquidity screens. Current classifications are not treated
as historical truth.

Signals formed at session `t` may rebalance only at the next session close.
New weights earn returns beginning with the following close-to-close interval.
This deliberately sacrifices one session rather than assume same-close fills.

## Repeated expanding chronological folds

| fold | training/observation window | test window | role |
|---|---|---|---|
| D1 | 2010–2014 | 2015 | development |
| D2 | 2010–2015 | 2016 | development |
| D3 | 2010–2016 | 2017 | development |
| D4 | 2010–2017 | 2018 | development |
| D5 | 2010–2018 | 2019 | development |
| D6 | 2010–2019 | 2020 | development |
| E1 | 2010–2020 | 2021 | untouched evaluation |
| E2 | 2010–2021 | 2022 | untouched evaluation |
| E3 | 2010–2022 | 2023 | untouched evaluation |
| E4 | 2010–2023 | 2024 | untouched evaluation |
| E5 | 2010–2024 | 2025 | untouched evaluation |

Only development folds may choose the P4 operational configuration. The
selection gates and lexicographic tie-break order are frozen in
`research/configs/price_component_walkforward_v1.json`. If no configuration
passes every development gate, Price cannot receive a PASS; P4/N30/monthly/2N
is then evaluated only as the pre-existing reference.

## Metrics and robustness

The result table reports total/TWR/annualized return, volatility, maximum
drawdown and duration, zero-risk-free Sharpe and downside deviation, gross
turnover, positions, cash, concentration, rolling 12/24/36-month relative win
rates, calendar-fold benchmark wins, extreme relative years, and top-five
stock/period contribution diagnostics. XIRR is not applicable because the
primary walk-forward uses no external contributions; SPY and QQQ share the
same dates and starting value.

Limited robustness is exactly: remove the best stock, remove the best year,
rank-weight sensitivity, P1–P4, N=20/30/40, weekly/monthly, immediate/2N, and
major drawdown/recovery regimes. No additional indicator or parameter search is
authorized.
