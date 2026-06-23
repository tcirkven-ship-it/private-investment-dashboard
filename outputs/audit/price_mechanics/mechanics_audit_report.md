# Price backtest portfolio-mechanics audit

## Question answers

**1. Were all surviving holdings reset to equal weight at every monthly review?**

Yes. The published `simulate()` calls `target_weights(selected, ...)`, which assigns equal weight
(0.033333) to every selected name at EACH monthly review. All survivors are restored to equal weight.
+6.9182% of total turnover comes from this weight restoration.

**2. Were only rank-below-60 and hard-ineligible positions sold?**

Approximately yes. `choose_target()` ranks all names, retains existing holdings within
rank 60 (the buffer), and fills remaining slots from top-ranked non-held names.
However, the equal-weight restoration also partially sells positions that remain in the
portfolio — those are not rank-60 exits but weight-adjustment sales.
In the strict sense, positions exit only when they fall below rank 60 OR when
they are forced out by sector/industry caps (constrained versions only).

**3. Were new positions funded by selling existing surviving positions?**

Yes. The portfolio is always fully invested (cash ≈ 0). New positions enter at weight 1/N,
funded by the equal-weight restoration that reduces overweight survivors.

**4. Was price-drift correction performed monthly, quarterly, or only when necessary?**

Every monthly review performs implicit full drift correction by resetting all weights to 1/N.
There is no separate drift-tracking step; the equal-weight assignment overwrites any drift.

**5. How exactly was annual gross turnover calculated?**

Daily turnover = sum(|new_weight - old_weight|) + |new_cash - old_cash| over all positions.
This is round-trip (two-way) turnover as a fraction of NAV.
Annualized = sum of daily turnover across the evaluation period / number of years.

**6. Did turnover include both buys and sells?**

Yes. sum(|new_weight - old_weight|) captures both weight increases (buys) and decreases (sells).
Cash changes are also included.

**7. What NAV denominator was used?**

Weights are fractions of TWR portfolio NAV after daily return accrual.
Portfolio_growth normalizes weights on each date. Weights always sum to 1 - cash.

**8. How much turnover came from each source?**

| Source | Existing (annualized) | Share |
|---|---:|--:|
| Total | 6.82 | 100.00% |
| Entry/exit (complete) | 6.35 | +93.0818% |
| Weight restoration | 0.47 | +6.9182% |
| Portfolio constraints | 0.00 | 0.00% |
| Fold initialization | 0.00 | 0.00% |
| Fold termination | 0.00 | 0.00% |
| Other | 0.00 | 0.00% |

**9. Did every annual evaluation fold restart from cash?**

No. The simulation runs one continuous portfolio from its 2014 start through 2025.
Each evaluation fold is a calendar-year slice of the same continuous path. There is no
cash reset between years.

**10. Were the reported 2021–2025 results created by linking one continuous portfolio
or aggregating independently restarted annual portfolios?**

One continuous portfolio. The published assembly code (`metrics()` then `fold_rows()`)
slices the same `ledger` DataFrame by calendar year. All 2021–2025 fold results are
non-overlapping slices of the same equity curve. There is no chain-linking or compounding
across independent resets.

---

## Published-reproduction verification

| Metric | Published | Reproduced | Verdict |
|---|---:|---:|:---:|
| Annualized return | +12.8466% | +12.8466% | PASS |
| Annual gross turnover | 6.82 | 6.82 | PASS |
| Max drawdown | -21.4900% | -21.4900% | PASS |
| Volatility | +19.7556% | +19.7556% | PASS |

Reproduction matches exactly. Proceeding to practical comparison.

## Existing vs practical mechanics — P4/N=30/monthly/rank-60, 2021–2025

| Metric | Published | Practical | Difference |
|---|---:|---:|---:|
| Annualized return | +12.8466% | +12.8619% | +0.0153% |
| SPY-relative return | -1.5496% | -1.5343% | +0.0153% |
| QQQ-relative return | -2.2901% | -2.2748% | +0.0153% |
| Volatility | +19.7556% | +19.8948% | +0.1392% |
| Max drawdown | -21.4900% | -22.1578% | -0.6678% |
| Annual gross turnover | 6.82 | 6.43 | -0.39 |
| Total purchases | 484 | 484 | 0 |
| Total sales | 484 | 484 | 0 |
| Average holding period | 0.23 yr | 0.23 yr | |

### Turnover decomposition — 2021–2025

| Source | Existing (annualized) | Share | Practical (annualized) | Share |
|---|---:|---:|---:|---:|
| Total | 6.82 | 100.00% | 6.43 | 100.00% |
| Entry/exit | 6.35 | +93.0818% | 6.17 | +96.0531% |
| Weight restoration | 0.47 | +6.9182% | 0.25 | +3.9469% |

### Annual breakdown — Existing (published) mechanics

| Year | Return | SPY-rel | QQQ-rel | Vol | Max DD | Gross TO | Entry/exit TO | Weight-restore TO |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021 | +15.9040% | -12.8247% | -11.5157% | +25.6536% | -18.9311% | 8.12 | 7.61 | 0.51 |
| 2022 | -10.7349% | +7.5058% | +21.9479% | +18.5986% | -16.4666% | 5.86 | 5.49 | 0.37 |
| 2023 | +13.5966% | -12.8141% | -41.8017% | +16.6741% | -13.8688% | 7.59 | 7.12 | 0.47 |
| 2024 | +43.8353% | +18.9488% | +18.2570% | +17.7463% | -8.5393% | 5.65 | 5.12 | 0.53 |
| 2025 | +8.1191% | -9.7537% | -12.8359% | +18.8329% | -17.3151% | 6.86 | 6.38 | 0.48 |

### Annual breakdown — Practical mechanics

| Year | Return | SPY-rel | QQQ-rel | Vol | Max DD | Gross TO | Entry/exit TO | Weight-restore TO |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021 | +15.6457% | -13.0831% | -11.7741% | +26.0482% | -19.4104% | 7.68 | 7.43 | 0.25 |
| 2022 | -11.0564% | +7.1844% | +21.6264% | +18.6495% | -16.5710% | 5.57 | 5.40 | 0.17 |
| 2023 | +14.0144% | -12.3963% | -41.3839% | +16.7297% | -13.9798% | 7.17 | 6.92 | 0.25 |
| 2024 | +44.6001% | +19.7137% | +19.0219% | +17.8437% | -8.5827% | 5.24 | 4.89 | 0.35 |
| 2025 | +7.8528% | -10.0200% | -13.1022% | +18.8275% | -17.1841% | 6.49 | 6.24 | 0.25 |

---

## Decisions

### 1. Turnover mathematical correctness

The published annualized gross turnover (6.82) is mathematically
correct given the code's definition: sum of daily |weight change| + cash change across all
positions, annualized as total / years. This is round-trip turnover as a fraction of NAV.
Reproduction matches the published figure exactly.

### 2. Match to intended practical mechanics

The published backtest does NOT match the intended practical mechanics in one material way:
it resets ALL surviving positions to equal weight at every monthly review.
Weight restoration accounts for +6.9182% of total turnover.

The practical mechanics (sell-only-below-60, survivors drift, quarterly correction only)
reduce weight-restoration turnover to +3.9469% and
lower total annualized gross turnover from 6.82 to
6.43 — a reduction of
0.39.

The rank-60 buffer determines which names enter/exit; both variants make the same 484 purchases and 484 sales. The turnover reduction comes entirely from not adjusting surviving positions' weights at non-quarterly reviews.

### 3. Fold-restart effect

The fold-restart effect is ZERO. The simulation is one continuous portfolio from 2014 through
2025. Evaluation folds are calendar-year slices of the same equity curve. No fold restart, no
cash reset, no initialization turnover, and no termination turnover occur.

Therefore fold-restart effects did NOT distort the published turnover or return figures.

### 4. Do practical mechanics materially change the P4 conclusion?

Published P4 active return vs QQQ: -2.2901%
Practical P4 active return vs QQQ: -2.2748%

Practical turnover: 6.43 vs published 6.82.
- Practical mechanics also trail QQQ (-2.2748% active return).
- The practical changes do not rescue P4 from benchmark underperformance.
- Turnover (6.43) still exceeds the 200% ceiling by a wide margin.

### 5. Final determination

**P4 remains FAIL.**

The practical mechanics comparison shows that:
- The single mechanical change (no monthly equal-weight restoration, quarterly correction only)
  reduces turnover but does not change the competitive conclusion.
- P4 underperforms QQQ by -2.2748% under practical mechanics.
- Annual turnover (6.43) exceeds 200%.
- Fold restarts do NOT distort the results.

The standalone P4 FAIL is robust to the practical mechanical adjustment.
No further investigation of portfolio-mechanics effects is warranted.

---

*This is a mechanical-fidelity comparison, not a new strategy search. No P1, P2, or P3
promotion. No scanner-launcher development. No new factor search.*