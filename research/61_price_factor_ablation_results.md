# Price factor-ablation results

> Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.

All decisive rows use the complete 1,069-history pull, N=30, monthly review,
rank-2N retention, equal weight and the unconstrained version.

| Candidate | Factors | Development ann. return | Evaluation ann. return | Eval. active vs SPY | Eval. active vs QQQ | Eval. max DD | Eval. vol. | Eval. turnover |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 12–1 | 24.14% | 37.61% | +23.21% | +22.47% | −31.53% | 37.87% | 493.07% |
| P2 | P1 + 6–1 | 29.78% | 43.29% | +28.89% | +28.15% | −36.06% | 41.24% | 725.36% |
| P3 | P2 + trend | 27.99% | 43.17% | +28.77% | +28.03% | −35.88% | 40.25% | 618.93% |
| P4 | P3 + inverse volatility | 10.76% | 12.85% | −1.55% | −2.29% | −21.49% | 19.76% | 681.70% |

P2 and P3 have high survivor-biased point returns, but also equity-like
drawdowns, roughly 40% annual volatility and 619%–725% annual gross turnover.
They are not practical replacements selected by this experiment. Seven source
series contain isolated adjusted-price jumps over 500%, and the dataset omits
inactive/delisted securities; those defects can especially inflate high-momentum
ablations.

Inverse volatility radically changes the signal. P4 roughly halves volatility
and improves maximum drawdown versus P3, but gives up about 30 percentage points
of annualized evaluation return and falls below both benchmarks. The frozen
four-factor Price composite therefore does not inherit the historical return of
its momentum-only components.
