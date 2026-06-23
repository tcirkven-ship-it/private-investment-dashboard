# Frozen Price repeated walk-forward — summary

| Period | P4 ann. return | SPY | QQQ | Active vs SPY | Active vs QQQ | Gross turnover |
|---|---:|---:|---:|---:|---:|---:|
| Development folds, 2015–2020 | 10.76% | 12.67% | 21.42% | −1.91% | −10.66% | 629.00% |
| Evaluation folds, 2021–2025 | 12.85% | 14.40% | 15.14% | −1.55% | −2.29% | 681.70% |

No configuration passed the development gates, so evaluation was diagnostic
and could not generate a PASS. P4 was defensive in 2022 and strong in 2024,
but trailed both benchmarks in 2021, 2023 and 2025.

Removing FTAI widened both deficits. Removing 2024 reduced P4 to 6.14%
annualized versus 11.84% SPY and 12.59% QQQ. Rank weighting worsened return,
concentration and turnover.

Conclusion: the exact P4 implementation is look-ahead controlled, but repeated
folds show no robust standalone benchmark value. The evidence remains
survivor-biased because the 1,069-name set is today's eligible universe
projected backward.
