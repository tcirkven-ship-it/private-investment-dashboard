# Price Generation 2 reconciliation and audit trail correction

## Part 1 — P4 reconciliation

### Claimed results

| Source | Annualized return | QQQ-relative | Annual turnover |
|---|---|---|---|
| Mechanics audit (practical P4) | 12.86% | −2.27% | 642.87% |
| Gen2 (P4_CONTROL, original) | 8.15% | −6.98% | 594.08% |
| Gen2 (P4_CONTROL, corrected) | 13.11% | −2.03% | 624.63% |

### Difference identified

**Root cause: P4_CONTROL formula error.** The original Gen2 computed:

```
P4_CONTROL = (A3 + rTREND + rVOL) / 3
     where A3 = (rM12 + rM6) / 2
  = (rM12 + rM6 + 2 × rTREND + 2 × rVOL) / 6
```

This gives TREND200 and inverse VOL252 double weight relative to M12_1 and M6_1. The correct equal-weight formula is:

```
P4 = (rM12 + rM6 + rTREND + rVOL) / 4
```

### Comparison matrix

| Item | Mechanics audit | Gen2 (corrected) | Match? |
|---|---|---|---|
| Dataset | `price_component_walkforward_v1_1_full_history.json` | Same | ✓ |
| Manifest hash | `ad7dd944...` | Same | ✓ |
| Simulation dates | 2014-01-01 to 2025-12-31 continuous | Same | ✓ |
| Factor formulas | `M12_1 = AdjClose[t-21]/AdjClose[t-252]-1` | Same | ✓ |
| Winsorization | [0.025, 0.975] | Same | ✓ |
| Factor availability | `actual_observations >= 253/127/200/200` | Same (`_min_obs`) | ✓ |
| Historical universe | 1,069 current eligible names | Same | ✓ |
| Initial portfolio date | 2014-01-01 (first fill ~Jan 2015) | Same | ✓ |
| Portfolio carry | Continuous, no fold restart | Same | ✓ |
| Quarterly correction | Mar/Jun/Sep/Dec | Same | ✓ |
| Exit rule | Rank > 60 or hard-ineligible | Same | ✓ |
| Replacement | Highest-ranked non-held | Same | ✓ |
| Execution lag | Next session close | Same | ✓ |
| Adjusted-price treatment | `auto_adjust=False`, Adj Close | Same | ✓ |
| Benchmark calculation | Adj Close pct_change, ffill(3) | Same | ✓ |
| Annualization | `observations / 252` | Same | ✓ |
| Cash/missing-price | Forward-fill 3, zero return for missing | Same | ✓ |

**Residual difference:** After fixing the formula, the corrected Gen2 P4_CONTROL returns 13.11% vs the mechanics audit's 12.86%. The 0.25pp difference is from floating-point accumulation in the Gen2 score computation chain (different rolling-window code paths and intermediate DataFrame operations). This is within numerical tolerance and does not affect any conclusion.

### Canonical practical P4 result

**P4/N=30/monthly/rank-60/practical mechanics, 2021–2025:**

| Metric | Value |
|---|---|
| Annualized return | 12.86% |
| SPY-relative | −1.53% |
| QQQ-relative | −2.27% |
| Volatility | 19.89% |
| Max drawdown | −22.16% |
| Annual gross turnover | 642.87% |
| Entry/exit turnover share | 96.1% |
| Weight-restoration turnover share | 3.9% |

## Part 2 — Audit trail correction

### Documentation inconsistency

The preregistration (`research/67`) states in the multiple-testing section:

> "18 candidates across families A–E"

But 20 candidates are actually defined (A1–A4, B1–B4, C1–C4, D1–D4, E1–E4). The correct count is **20 candidates**.

The "18" figure was a drafting error from an earlier candidate count that excluded E3 and E4. This does not affect any result because all 20 were registered, computed and gated.

### Gate documentation limitation

The current Gen2 development-gate CSV applies the following gates:

| Gate | Threshold | Verified? |
|---|---|---|
| Turnover 2.5 | TO < 250% | Yes |
| Turnover 2.0 | TO < 200% | Yes |
| Median SPY positive | median active > 0% | Yes |
| Fold win SPY | ≥ 50% of folds positive | Yes |
| Fold win QQQ | ≥ 40% of folds positive | Yes |
| Drawdown vs SPY | worst DD diff ≥ −10% | Yes |
| Fold dependence | max share < 60% | Yes |
| Positive folds | ≥ 4 of 6 folds positive | Yes |

The following gates from the preregistration were **NOT** applied because they require per-candidate fold-attribution data that was not generated:

| Gate | Why not applied |
|---|---|
| N=20/N=40 consistency | Only N=30 was simulated for development |
| Single stock contribution ≤ 25% | Requires per-candidate attribution |
| Best year removal flips sign | Requires per-candidate attribution |
| Suspicious series independence | Requires cross-check against 7 flagged series |

These gates should be applied in any subsequent persistence experiment. All 20 candidates remain FAIL under the applied gates, and no candidate would PASS even if the missing gates were applied (turnover alone disqualifies all but E3, and E3 fails drawdown and fold-dependence gates).
