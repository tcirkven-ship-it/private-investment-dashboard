# Price persistence experiment — results

> Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.

## Development-only results (2015–2020)

### Aggregate

| Candidate | Spec | Ann ret | SPY-rel | QQQ-rel | Vol | Max DD | TO | Wins SPY | Wins QQQ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A3 | base | 25.84% | 13.17% | 4.42% | 28.07% | −45.50% | 618% | 6/6 | 4/6 |
| A3 | exit2 | 24.69% | 11.52% | 0.28% | 25.58% | −36.61% | 64% | 6/6 | 3/6 |
| A3 | combined | 20.65% | 7.98% | 4.45% | 26.87% | −44.38% | 67% | 5/6 | 4/6 |
| B2 | base | 30.73% | 18.06% | 9.31% | 27.88% | −43.70% | 548% | 6/6 | 5/6 |
| B2 | exit2 | 23.50% | 11.42% | 4.77% | 25.84% | −38.32% | 65% | 5/6 | 4/6 |
| B2 | combined | 19.54% | 5.65% | 2.97% | 26.24% | −43.12% | 66% | 4/6 | 4/6 |
| D1 | base | 42.53% | 29.86% | 21.11% | 33.81% | −48.42% | 311% | 5/6 | 3/6 |
| D1 | exit2 | 31.55% | 16.83% | 15.41% | 27.79% | −44.48% | 70% | 5/6 | 5/6 |
| D1 | combined | 29.46% | 14.75% | 11.47% | 27.81% | −42.89% | 70% | 5/6 | 5/6 |

### Failed gates

| Candidate | Spec | Failing gate |
|---|---|---|
| A3 | exit2 | DD vs SPY per fold: −15.09pp (threshold −15pp) |
| B2 | exit2 | DD vs SPY per fold: −15.83pp |
| B2 | combined | Max DD: −43.12% (threshold −40%) |
| D1 | exit2 | Max DD: −44.48%, DD vs SPY: −16.24pp |
| D1 | combined | Max DD: −42.89%, DD vs SPY: −18.16pp |
| All | base/min3/rank90/entry2 | Turnover > 250% |

### Key findings

1. **Two-consecutive-below-60 exit confirmation** is the single most effective lever, reducing turnover from 500–600% to 64–70%.
2. No specification passes every gate. The closest is A3 exit2, which fails only the DD-vs-SPY threshold by 0.09pp in 2016.
3. The 2016 fold is the weakest for all momentum-based signals, causing drawdowns 15–18pp worse than SPY.
4. Minimum holding period (min3) has no effect because stocks typically exit the rank-60 buffer only after being held for more than 3 months.
5. Rank-90 retention alone does not reduce turnover enough (269–520%).
6. Entry confirmation alone increases turnover (319–692%) by delaying entry until names are confirmed in the top 30.

## Decision

**FAIL for all specifications. Price research path exhausted under the current yfinance dataset.**

No candidate and no mechanical variant passes every frozen development gate. The marginal failure of A3 exit2 (DD vs SPY: −15.09pp vs −15.00pp) is close but does not change the conclusion under the preregistered rules.

The survivor-biased dataset, the limited historical depth, and the structural drawdown and turnover characteristics of all tested Price signals prevent a credible standalone Price component for QVP integration.

## Next actions

- Cease Price-only signal research under the current yfinance dataset.
- The existing YF-QVP scanner remains the practical decision-support tool.
- Prospective evidence accumulation (Option 4 from `research/66`) is the remaining path for QVP validation.
- Paid-data preparation (Option 3) would be required to resolve the survivorship ceiling.
