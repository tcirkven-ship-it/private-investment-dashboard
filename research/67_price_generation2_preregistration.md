# Price Generation 2 — Preregistration

**Version:** PRICE-GEN2-1.0.0  
**Preregistered:** 2026-06-23, before any computation  
**Scanner boundary:** commit `52aa05b`; run `2026-06-22T172514Z`

> Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.

## Objective

Determine whether any interpretable Price formulation besides the frozen P4 can meet practical turnover, drawdown and benchmark-relative gates using the available survivor-biased historical yfinance data. A passing candidate would become the frozen Price input for a subsequent QVP-weight experiment.

## Prohibitions

- No automated parameter optimization against evaluation
- No thousands of technical-indicator combinations
- No candidate selected on highest return alone
- No evaluation inspection before complete preregistration freeze
- No P1, P2, P3 or P4 promotion under a new name
- No scanner, Q-factor or V-factor modification
- No stock recommendations

## Candidate families

### Family A — Medium-term momentum

| ID | Formula | Rationale |
|---|---|---|
| A1 | `M12_1`: adj_close[t-21] / adj_close[t-252] - 1 | Classic 12-1 momentum, identical to P1 |
| A2 | `M6_1`: adj_close[t-21] / adj_close[t-126] - 1 | Shorter lookback, P1 component |
| A3 | Equal percentile average of M12_1 and M6_1 | Combined medium-term momentum |
| A4 | 2/3 × M12_1 + 1/3 × M6_1 (percentile-weight blend) | Front-loaded 12-month signal |

### Family B — Momentum plus trend

| ID | Formula | Rationale |
|---|---|---|
| B1 | A3 + TREND200 (equal percentile average) | Momentum plus price/200-ma level |
| B2 | A3 + MA50_200: adj_close[50-ma] / adj_close[200-ma] - 1 | Moving-average crossover signal |
| B3 | A3 + SLOPE200: 200-day linear regression slope scaled by price | Positive trend direction |
| B4 | A3 + PCT_ABOVE_200: fraction of last 63 sessions above 200-ma | Trend persistence measure |

### Family C — Breakout and relative strength

| ID | Formula | Rationale |
|---|---|---|
| C1 | `HIGH52W`: distance from 52-week max price, ranked inversely | Closer to high = stronger |
| C2 | A3 + HIGH52W equal percentile average | Momentum plus breakout |
| C3 | `SPY_REL_6M`: 6-month stock return minus 6-month SPY return; `SPY_REL_12M`: 12-month version; equal average of both | Relative strength vs market |
| C4 | Cross-sectional A3 + SPY_REL (average of C3) | Dual momentum |

### Family D — Controlled risk adjustment

| ID | Formula | Rationale |
|---|---|---|
| D1 | A3 / VOL252 (percentile of ratio) | Returns per unit risk |
| D2 | A3 percentile - 0.25 × VOL252 percentile | Penalty for high vol |
| D3 | A3 with highest-volatility decile excluded; remaining ranked by A3 | Cap extreme vol |
| D4 | A3 with VOL252 capped at 80th percentile before ranking | Soft vol cap |

P4 (A3 + VOL252 inverse) is retained as the failed control, not a candidate.

### Family E — Trend quality

| ID | Formula | Rationale |
|---|---|---|
| E1 | `REGR_SLOPE_200` / `REGR_RESID_VOL_200`: t-stat of 200-day trend | Signal-to-noise of trend |
| E2 | Fraction of positive monthly returns over prior 12 months | Consistency |
| E3 | Inverse of max drawdown over 252-day formation period | Stability of momentum |
| E4 | Rank consistency: min(rank percentile across A3 evaluated at 3/6/12 months) | Agreement across horizons |

### Family F — Entry and exit mechanics (applied to strongest development finalists only)

| ID | Variation |
|---|---|
| F1 | Immediate top-N exit (retention 1.0) |
| F2 | Rank-2N retention |
| F3 | Rank-1.5N retention |
| F4 | Rank-2N + 1-month minimum holding period |
| F5 | Rank-2N + 3-month minimum holding period |
| F6 | Rank-2N + 2-consecutive-below-60 exit confirmation |

## Portfolio framework

| Parameter | Primary | Sensitivity |
|---|---|---|
| Direction | Long-only | — |
| Portfolio size | N=30 | N=20, N=40 |
| Construction | Equal weight | — |
| Review | Monthly | Weekly (finalists only) |
| Retention | Rank 2N (60) | Immediate, 1.5N (finalists only) |
| Survivors | Drift; no monthly equal-weight restoration | — |
| Weight correction | Quarterly (Mar/Jun/Sep/Dec) | — |
| Execution | Next-valid-session close | — |
| Costs | Zero primary; realistic-cost sensitivity | — |
| Benchmarks | SPY, QQQ | — |

## Chronological validation

**Development folds (candidate filtering):**

| Fold | Train end | Test year | Role |
|---|---|---|---|
| D1 | 2014 | 2015 | rejection |
| D2 | 2015 | 2016 | rejection |
| D3 | 2016 | 2017 | rejection |
| D4 | 2017 | 2018 | rejection |
| D5 | 2018 | 2019 | rejection |
| D6 | 2019 | 2020 | finalist selection |

**Evaluation folds (finalists only, untouched until after selection):**

| Fold | Train end | Test year |
|---|---|---|
| E1 | 2020 | 2021 |
| E2 | 2021 | 2022 |
| E3 | 2022 | 2023 |
| E4 | 2023 | 2024 |
| E5 | 2024 | 2025 |

## Development gates

A candidate advances past development only if the aggregate 2015–2020 result meets ALL of:

- Annualized gross turnover < 250% (target < 200%)
- Median active TWR vs SPY > 0%
- Fold win rate vs SPY >= 50%
- Fold win rate vs QQQ >= 40%
- Worst drawdown difference vs SPY >= -10%
- Maximum single-fold share of absolute active SPY <= 60%
- Positive return in at least 4 of 6 development folds
- N=30, N=20 and N=40 all show consistent direction
- No single stock contributes > 25% of total positive contribution
- No single year removed flips the sign of total return
- Not dependent on suspicious >500% adjusted-price jump series

Gates are inspected before evaluation. If multiple pass, the selection order is:
1. Lowest annualized gross turnover
2. Highest median active TWR vs QQQ
3. Portfolio size closest to 30
4. Monthly before weekly

## Evaluation metrics (for each finalist)

- Annualized TWR vs SPY and QQQ
- Volatility, max DD and duration, downside deviation
- Sharpe (zero rf)
- Annual gross turnover, entry/exit turnover, weight-restoration turnover
- Number of purchases, sales, average holding period
- Rolling 12/24/36-month benchmark win rates
- Calendar-year benchmark wins
- Top-stock concentration (HHI, top-5 weight)
- Top-period positive contribution share
- Remove best stock sensitivity
- Remove best year sensitivity
- Rank-weight sensitivity (percentile weighting)
- Realistic cost sensitivity (10 bps one-way)
- Dependence on suspicious series

## Decision classifications

| Classification | Meaning |
|---|---|
| PASS FOR QVP INTEGRATION RESEARCH | Survived development, competitive evaluation, turnover controlled; may proceed to QVP weight experiment |
| CONDITIONAL PASS | Survived development but has notable weakness; proceed with caution |
| FAIL | Failed a hard development gate |
| INCONCLUSIVE DUE TO DATA LIMITATIONS | Result cannot be interpreted because of structural survivor-bias or data ceiling |

A PASS does not mean proven alpha. It means the candidate is sufficiently robust to become the frozen Price input for the next experiment.

## Multiple-testing controls

- 18 candidates across families A–E
- Finalist selection restricted to development-only metrics
- Report total candidates tested before any selection
- Bootstrap uncertainty intervals for primary benchmark comparison
- Explicit false-discovery and selection-bias discussion

## Family-level exploration

Before any candidate is evaluated, the family definitions, gates, selection rule, and evaluation plan are frozen here. No candidate observed to perform poorly may be replaced by a similar candidate with modified parameters after seeing results.
