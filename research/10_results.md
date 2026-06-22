# Results — best-effort free-data generation

**Experiment generation:** `RP-001-BEST-EFFORT-V1`  
**Primary candidate:** C03-M, 12–1-month total-return momentum  
**Pre-holdout:** 2010-01-01 through 2022-12-31  
**Final holdout:** 2023-01-01 through 2026-06-18  
**Final classification:** **FAIL**

## What was actually tested

The historical experiment used the 100 issuer-deduplicated equity holdings in the official iShares S&P 100 ETF snapshot dated 2026-06-18. It projected that current liquid mega-cap universe backward and used locally stored yfinance adjusted-price, volume, dividend, and split histories. SPY and QQQ received identical USD 250 weekly contributions.

The primary stock portfolio held 30 names, ranked monthly on 12–1-month momentum, retained holdings through a rank-60 buffer, targeted equal weights, corrected weights quarterly, and routed weekly cash to at most three underweights. Expected costs were USD 0.35 per order plus five basis points of one-way price impact; the stressed case used USD 1.00 plus ten basis points.

Accounting passed eight deterministic unit tests and six integrated benchmark checks. All 100 stock histories passed the registered file and time-series checks.

## Stitched 2010–2026 result

These figures are numerically reproducible but structurally biased because the 2026 universe is projected backward.

| Metric | C03-M | SPY | QQQ |
|---|---:|---:|---:|
| Total contributed | $214,500 | $214,500 | $214,500 |
| Ending value | $1,570,117 | $820,567 | $1,403,434 |
| Annualized TWR | 20.55% | 14.03% | 19.30% |
| XIRR | 21.42% | 14.80% | 20.29% |
| Annualized volatility | 18.88% | 17.14% | 20.65% |
| Maximum drawdown | -32.41% | -33.72% | -35.12% |
| Explicit modeled costs | $7,450 | $407 | $407 |
| Annualized discretionary turnover | 177.66% | — | — |

The full-sample point estimate exceeded SPY by 6.52 percentage points annualized TWR and QQQ by 1.24 points. XIRR advantages were 6.62 and 1.14 points respectively. These values do **not** establish alpha because the data-integrity gate fails.

## Pre-holdout versus final holdout

| Metric | Pre-holdout 2010–2022 | Holdout 2023–2026-06-18 |
|---|---:|---:|
| C03-M annualized TWR | 17.09% | 34.50% |
| Active TWR vs SPY | +5.34 pp | +11.47 pp |
| Active TWR vs QQQ | +1.72 pp | **-0.83 pp** |
| XIRR advantage vs SPY | +5.09 pp | +11.66 pp |
| XIRR advantage vs QQQ | +1.81 pp | **-0.50 pp** |
| Annualized turnover | **184.03%** | **172.00%** |
| Stressed active TWR vs QQQ | +0.92 pp | **-0.99 pp** |

The final holdout therefore failed the required QQQ economic and stressed-cost gates. It also repeated the turnover failure.

## Consistency and uncertainty

- Positive calendar-year active return occurred in 13 of 17 years versus SPY and 11 of 17 versus QQQ.
- Holdout 2023 trailed SPY by 7.86 points and QQQ by 36.55 points; subsequent holdout years were positive.
- The stitched moving-block bootstrap 95% interval for annualized active return was +2.68% to +9.32% versus SPY, but **-3.58% to +4.81% versus QQQ**. Estimated probability of positive active return versus QQQ was only 63.1%, far below the 95% hurdle.
- Removing the best strategy year reduced the QQQ active point estimate to +0.98%, below the +1.0% hurdle.
- Starting the measurement in 2015 reduced the QQQ active point estimate to +0.53%.

## Contribution timing

Weekly, biweekly, and monthly aggregation produced nearly identical holdout TWRs: 34.50%, 34.50%, and 34.49%. Modeled holdout explicit costs fell from about $3,150 weekly to $3,003 monthly. No credible timing alpha appeared; lower-frequency aggregation mainly reduced orders and operational burden.

## What was not historically testable

The requested quality, value, profitability, financial-strength, investment, shareholder-yield, and fundamental composite strategies were not tested as historical claims. Free yfinance statements are not point-in-time vintages, and SEC ingestion was not run without a compliant owner-supplied contact identity. Treating latest statements as historical knowledge would have manufactured look-ahead bias.

Machine-readable results:

- `outputs/experiment_runs/EXP-0006/accounting_validation.json`
- `outputs/experiment_runs/EXP-0009/summary.json`
- `outputs/experiment_runs/EXP-0010/summary.json`
- `outputs/experiment_runs/EXP-0010/robustness_audit.json`

