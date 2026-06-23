# Repeated Price walk-forward results

> Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.

The immutable pull completed all 1,069 current eligible stocks plus SPY and QQQ.
P4 factor-ready coverage grew from 792 names in 2015 to 1,069 in 2025. This is
much broader than the 80-history fallback, but membership is still the current
survivor set projected backward.

## Development outcome

No P4 configuration passed all 2015–2020 development gates. The lowest-turnover
monthly/rank-2N P4 variants still required 584%–629% annual gross turnover, and
most failed QQQ fold consistency. Under the preregistered fallback, P4/N=30/
monthly/rank-2N was frozen only as a diagnostic reference; standalone Price was
already ineligible for a PASS.

The reference returned 10.76% annualized in development, versus 12.67% SPY and
21.42% QQQ, with −43.01% maximum drawdown and 629.00% annual gross turnover.

## Frozen evaluation folds

| Fold | Year | P4 | SPY | QQQ | Active vs SPY | Active vs QQQ | P4 max DD | Gross turnover |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| E1 | 2021 | 15.90% | 28.73% | 27.42% | −12.82% | −11.52% | −18.93% | 812.44% |
| E2 | 2022 | −10.73% | −18.24% | −32.68% | +7.51% | +21.95% | −16.47% | 586.04% |
| E3 | 2023 | 13.60% | 26.41% | 55.40% | −12.81% | −41.80% | −13.87% | 758.56% |
| E4 | 2024 | 43.84% | 24.89% | 25.58% | +18.95% | +18.26% | −8.54% | 565.45% |
| E5 | 2025 | 8.12% | 17.87% | 20.96% | −9.75% | −12.84% | −17.32% | 686.28% |

Across 2021–2025, P4 returned **12.85% annualized**, versus **14.40% SPY** and
**15.14% QQQ**. It beat each benchmark in 2 of 5 folds. Rolling 12/24/36-month
win rates were 51.0%/70.3%/68.0% versus SPY and 51.0%/51.4%/52.0% versus QQQ.
Maximum drawdown was −21.49%, volatility 19.76%, zero-risk-free Sharpe 0.71,
and annual gross turnover 681.70%.

P4 was defensive in 2022 and strong in 2024, but materially lagged in 2021,
2023 and 2025. Repeated later folds do not show stable standalone value.
