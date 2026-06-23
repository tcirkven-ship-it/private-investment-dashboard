# Price frequency, size and retention results

> Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.

## Review frequency — P4/N=30/rank-2N

| Review | Eval. ann. return | Active vs SPY | Active vs QQQ | Max DD | Turnover |
|---|---:|---:|---:|---:|---:|
| Daily | 9.08% | −5.32% | −6.06% | −25.76% | 1,277.00% |
| Weekly | 8.80% | −5.60% | −6.34% | −25.21% | 959.23% |
| Biweekly | 8.83% | −5.56% | −6.31% | −30.17% | 833.14% |
| Monthly | 12.85% | −1.55% | −2.29% | −21.49% | 681.70% |

Daily and weekly review reduced returns and multiplied turnover. Monthly is the
least-bad operational frequency, not an alpha source.

## Retention — P4/N=30/monthly

| Exit rule | Eval. ann. return | Active vs SPY | Active vs QQQ | Max DD | Turnover |
|---|---:|---:|---:|---:|---:|
| Immediate/top N | 12.23% | −2.17% | −2.91% | −21.28% | 935.91% |
| Rank 1.5N | 11.90% | −2.50% | −3.24% | −22.70% | 772.12% |
| Rank 2N | 12.85% | −1.55% | −2.29% | −21.49% | 681.70% |

The rank-2N buffer reduced turnover and modestly improved return, but turnover
remained nearly seven times average capital annually. None passed.

## Portfolio size — P4/monthly/rank-2N

| N | Eval. ann. return | Active vs SPY | Active vs QQQ | Max DD | Turnover |
|---:|---:|---:|---:|---:|---:|
| 20 | 12.61% | −1.78% | −2.52% | −26.22% | 738.24% |
| 30 | 12.85% | −1.55% | −2.29% | −21.49% | 681.70% |
| 40 | 12.06% | −2.33% | −3.07% | −21.80% | 625.52% |

The negative conclusion is not sensitive to N. N=30 had the best point return;
N=40 lowered turnover, but all sizes lagged both benchmarks and breached the
200% development turnover ceiling.

At USD 250, equal deployment across N=20/30/40 implies only USD 12.50/8.33/6.25
per target, so practical contributions need batching or underweight routing.
