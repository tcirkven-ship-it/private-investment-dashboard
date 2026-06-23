# Corrected A3 exit2 evaluation — state-machine defect fixed

**Evidence label:** Post-confirmatory exit-mechanics robustness research using a survivor-biased historical yfinance universe.

## Bug description

The original exit2 implementation cleared the exit-confirmation counter
for ALL survivors at each review, including stocks still below rank 60
whose counter had not yet reached the confirmation threshold.

Buggy code pattern (present in price_persistence.py, a3_sma150_exit.py,
and a3_exit2_evaluation.py):

```
for idx in survivors:
    exit_signals.pop(idx, None)  # clears counter for ALL survivors
```

This prevented any rank-based exit from ever triggering (V0 had 0 full
exits across the entire 2021-2025 evaluation period despite 90.8% of
held-stock-month observations having rank > 60).

Fix: only clear the counter when the stock's rank recovers to <= 60
(already handled by the `else: exit_signals.pop(idx, None)` branch
in the main loop). Remove the blanket survivors loop.

## Development reproduction (2015–2020, 10bps cost)

| Metric | Original (buggy) | Corrected |
|---|---:|---:|
| Annualized return | +24.69% | +27.2511% |
| Annual gross turnover | 63.88% | 4.32 |
| Max drawdown | -36.61% | -44.2601% |

## Evaluation results (2021–2025, 10bps cost)

| Metric | Original (buggy) | Corrected | SPY | QQQ |
|---|---:|---:|---:|---:|
| Annualized return | +23.04% | +35.3153% | +14.3961% | +15.1367% |
| Annual gross turnover | 63.19% | 4.24 | — | — |
| Max drawdown | -28.44% | -35.1331% | — | — |

## Level 1 evaluation gates (10bps cost)

- Net return > SPY: PASS
- Net return > QQQ: PASS
- TO < 150%: FAIL
- Max DD > -40%: PASS

**One or more gates FAIL. A3 exit2 is no longer PASS.**

## Recommendation

1. **Fix the bug** in all affected simulator files (price_persistence.py,
   a3_sma150_exit.py, a3_exit2_evaluation.py, sma150_instrumentation_audit.py,
   state_machine_audit.py).
2. **Rerun full development and evaluation** with the corrected code.
3. **Reapply the development gates** from the persistence experiment.
4. **Issue a fresh PASS/FAIL decision** based on the corrected results.
5. **Do not preserve the previous PASS automatically.**