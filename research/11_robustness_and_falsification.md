# Robustness, falsification, and adversarial review

## Verdict

The preferred candidate does not survive the complete protocol. The adversarial conclusion is **FAIL**, even though several historical point estimates are attractive.

## Parameter and portfolio stability

Only two of ten registered candidates were positive against both SPY and QQQ in both pre-holdout and holdout periods: the 10- and 20-stock momentum portfolios. Their annualized turnover was approximately 875% and 258% in the holdout, so neither satisfies the 100% cap or a reasonable manual-maintenance standard.

The frozen 30-stock candidate changed from +1.72 points annualized versus QQQ pre-holdout to -0.83 points in the holdout. The 9–1-month neighbor changed from +3.61 to -6.07 points. This is not a stable parameter plateau.

## Influence checks

- The largest approximate stock P&L contributor was MU at about $100,945, 7.45% of total portfolio profit. Removing that P&L leaves a large positive nominal profit, so one-stock dependence is not the main failure.
- Removing the best calendar year leaves +0.98 points annualized versus QQQ, slightly below the hurdle.
- Later starting dates consistently reduce the QQQ advantage: approximately +1.24 points from 2010 but +0.53 from 2015.
- The strategy's annualized active return versus QQQ was negative in high-volatility sessions and in SPY bull years, while it was positive in lower-volatility and SPY bear regimes. Regime dependence is material.

## Adversarial findings

| Finding | Severity | Resolution |
|---|---|---|
| Current 2026 OEF holdings projected backward | Critical | Unresolved; automatically fails definitive and conditional-pass data gates |
| Missing inactive names and delisting returns | Critical | Unresolved |
| Historical point-in-time fundamentals unavailable | Critical | Requested price-plus-fundamental strategy was not historically validated |
| Holdout trailed QQQ | Critical performance | Failed TWR, XIRR, and stressed-cost QQQ gates |
| Annualized turnover 172–184% | Critical implementation | Failed 100% threshold; concentrated variants were much worse |
| QQQ bootstrap interval includes zero | Critical uncertainty | Failed the 95% lower-bound requirement |
| Only 20% of candidates positive vs both benchmarks in both stages | High | Failed stability requirement |
| Holdout sector exposure reached 33.14% | High | Exceeded 30% drift cap on 18 sessions |
| Fractional MOC execution unsupported by IBKR | High execution | Next-session adjusted-close model cannot be implemented literally with fractional MOC orders |
| Taxes, investor-specific FX, and exact account pricing unresolved | High suitability | Results remain pretax USD estimates |
| Generic five/ten-basis-point impact assumptions | Medium | Stressed case included, but historical spreads were unavailable |
| One-stock dependence | Low | Top name represented only 7.45% of approximate profit |

## Multiple-testing interpretation

Ten bounded price variants were registered before the holdout. No holdout result was used to redefine the primary candidate. Formal whole-search superiority tests would not rescue this generation: the primary fails data, QQQ holdout, turnover, uncertainty, and implementation gates independently.

## Challenge conclusion

The favorable full-sample result is most plausibly interpreted as a useful exploratory momentum observation amplified by current-winner universe selection, not as sufficient evidence for a deployable direct-stock strategy.

