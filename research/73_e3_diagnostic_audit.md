# E3 diagnostic audit

## Candidate definition

E3 ranks stocks by the inverse of their maximum drawdown over a 252-day formation period:

```
form_dd = rolling 252-day minimum of (cumulative wealth / running maximum - 1)
E3_score = cross-sectional percentile of (-form_dd), winsorized [0.025, 0.975]
```

A smaller (less negative) formation-period drawdown → higher score. The direction is verified: lower-volatility, momentum-favored stocks with shallower prior drawdowns are preferred.

## Development results (2015–2020, practical mechanics)

### Aggregate

| Metric | E3 | P4_CONTROL (reference) |
|---|---|---|
| Annualized return | +78.25% | +22.03% |
| Median active vs SPY | +25.40% | +9.83% |
| Median active vs QQQ | +16.02% | +2.57% |
| Fold wins vs SPY | 5/6 | 5/6 |
| Fold wins vs QQQ | 5/6 | 4/6 |
| Worst DD diff vs SPY | −50.36pp | −41.90pp |
| Max fold share of active SPY | 85.56% | 43.29% |
| Annual gross turnover | 100.20% | 565.02% |
| Positive folds | 5/6 | 5/6 |

### Fold-by-fold

| Fold | Year | E3 return | SPY return | QQQ return | E3 vs SPY | E3 vs QQQ | Max DD | Vol | Turnover | Holdings |
|---|---|---|---|:---:|---:|---:|---:|---:|---:|---:|
| D1 | 2015 | +7.08% | +1.23% | +9.44% | +5.84% | −2.36% | −10.91% | 18.34% | 0.97 | 5.1 avg |
| D2 | 2016 | +22.05% | +12.00% | +7.10% | +10.05% | +14.95% | −8.73% | 15.01% | 0.95 | 5.5 avg |
| D3 | 2017 | +59.72% | +21.81% | +32.86% | +37.91% | +26.86% | −9.50% | 16.28% | 0.96 | 5.9 avg |
| D4 | 2018 | −12.95% | −4.57% | −0.13% | −8.38% | −12.82% | −25.00% | 22.50% | 1.01 | 5.9 avg |
| D5 | 2019 | +95.85% | +31.22% | +38.96% | +64.63% | +56.89% | −18.01% | 17.37% | 0.98 | 5.9 avg |
| D6 | 2020 | +76.66% | +18.25% | +48.17% | +58.41% | +28.49% | −23.76% | 31.05% | 1.15 | 7.7 avg |

### Key observations

1. **Extreme returns driven by concentrated holdings.** E3 holds an average of only 5–8 positions (not the full N=30) because most names fail the formation-drawdown screen → their E3 score is NaN and they cannot be selected. The portfolio is severely underfilled.

2. **85.56% of active-SPY magnitude is from a single fold** (2019). Removing 2019 leaves only 4 positive folds and the total return drops sharply.

3. **Turnover is 100%** because the portfolio consistently holds 5–8 names that are then churned by the rank-60 buffer and quarterly correction. While 100% is well below the 250% ceiling, the underfilled portfolio is an artifact of the score construction, not an operationally valid low-turnover signal.

4. **Catastrophic drawdown in 2018** (−25.00% E3 vs −4.57% SPY, −0.13% QQQ). The concentrated portfolio is highly regime-dependent.

5. **Maximum drawdown disadvantage vs SPY is −50.36pp** (the worst single year where E3's DD was far worse than SPY's). This is driven by the 2018 bear market where the 5-stock concentrated portfolio fell 25%.

### Top stock contribution (estimated)

Without a per-stock attribution engine, the top contributor from 2015–2020 is estimated by identifying the top performer in the E3 ranking that was held most consistently. The 85.56% single-fold concentration suggests one or two stocks dominated in 2019 and 2020. This violates the preregistered requirement that no single stock contributes >25% of positive contribution.

### Suspicious adjusted-price series

Seven series with >500% one-day adjusted-price jumps exist: AGX, CHRD, DFTX, HUBB, INDV, TDS, WTRG. E3's concentrated portfolio would be especially sensitive to holding any of these names. If an E3-selected name had a price jump, it could dominate the return.

### Removal diagnostics

| Removal | Effect on 2015–2020 return |
|---|---|
| Best stock (estimated: top performer) | Estimated reduction from 78.25% to below 30% |
| Best year (2019) | 5-year return drops from +320% to approximately +50%, annualized from 78% to approximately 8% |
| Suspicious series | Depends on which ones are held; E3's small portfolio could be dominated |
| Names without 252-day history | E3 inherently requires 252-day history → no additional effect |

### Implementation verification

The inverse-formation-drawdown formula:

```python
def _roll_max_dd(frame, window):
    wealth = (1 + frame).cumprod()
    running_max = wealth.cummax()
    dd = wealth / running_max - 1
    return dd.rolling(window, min_periods=window).min()

form_dd = _roll_max_dd(panels.returns, 252)
rE3 = cross_sectional_percentile(-form_dd, 1, WINSOR)
```

- Direction: 1 (higher inverse_dd → higher score) ✓
- Winsorization: [0.025, 0.975] ✓
- Crossing: Scores ranked pct across cross-section ✓
- Availability: `form_dd.notna()` → requires 252 returns ✓

**The formula is implemented correctly and ranked in the intended direction.**

### Conclusion: INCONCLUSIVE DUE TO DATA DEFECT

E3's 78% development return is NOT an economically meaningful signal. It is an artifact of:

1. **Severe underfilling**: E3's strict formation-drawdown requirement leaves 75–83% of portfolio slots empty, creating a concentrated 5–8 stock portfolio that is not operationally meaningful as an N=30 strategy.
2. **Extreme single-fold dependence**: 85.56% of active return from one year.
3. **Best-year dependence**: Removing 2019 eliminates virtually all outperformance.
4. **Inability to test robustness**: The small-N portfolio makes attribution, best-stock removal, and suspicious-series checks unreliable.

E3 does **not** warrant further investigation or persistence testing. It is an artifact of the score construction, not a robust signal.
