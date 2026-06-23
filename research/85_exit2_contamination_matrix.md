# Exit2 contamination matrix

## Bug description

The exit-confirmation state machine cleared the below-rank counter for ALL surviving holdings each month:

```python
for idx in survivors:
    exit_signals.pop(idx, None)  # clears counter for ALL survivors
```

This prevented the counter from ever reaching the confirmation threshold (2). No rank-based exit ever triggered.

## Impact by module

| Module | Exit confirm used? | Results affected? | Rerun required? | Superseded by |
|---|---|---|---|---|
| `price_persistence.py` | Exit2/combined specs use confirm_months=2 | **YES** — exit2/combined TO and returns are wrong. base/min3/rank90/entry2 specs have confirm_months=0 (immediate exit), unaffected. | YES | `corrected_persistence_rerun.py` |
| `a3_exit2_evaluation.py` | Yes (exit_confirm_months=2) | **YES — INVALIDATED**. Zero exits occurred; strategy was effectively static. | YES | `corrected_exit2_evaluation.py` |
| `a3_sma150_exit.py` | V0/V3 use rank exit with confirm=2 | **YES, partially**. V0/V3 rank-exit counts wrong. V1/V2 bypass rank exit (SMA-dominant), unaffected. | YES for V0/V3 results | N/A (V0/V3 not adopted) |
| `sma150_instrumentation_audit.py` | Reporting only | **YES** — exit-cause counts reflect buggy simulator. Audit document correctly identifies the discrepancy and led to the state-machine audit. | No — the audit discovered the bug | `research/84` |
| `state_machine_audit.py` | Bug discovery | Already documents the bug and corrected results. | No | Already current |
| `corrected_exit2_evaluation.py` | Fixed version | Always had correct state machine. Used for corrected results. | No | Already current |

## Impact by document

| Document | Strategy | Impact | Superseded by |
|---|---|---|---|
| `research/74` | Persistence preregistration | **None** — preregistration only, no computation | — |
| `research/75` | Persistence results | **Affected for exit2/combined** — TO and returns wrong. base/min3/rank90/entry2 unaffected. | `research/86` |
| `research/76` | Persistence decision | **Affected** — gate evaluations for exit2/combined invalid. | `research/87` |
| `research/77` | A3 exit2 preregistration | **None** — preregistration only | — |
| `research/78` | A3 exit2 evaluation | **INVALIDATED** — zero exits meant effectively static strategy. | `research/84` |
| `research/79` | A3 exit2 decision (PASS) | **INVALIDATED** — PASS was based on non-functioning exit mechanism. | `research/84` |
| `research/80` | SMA150 preregistration | **None** — preregistration only | — |
| `research/81` | SMA150 results | **Partially affected** — V0/V3 rank-exit counts. V1/V2 unaffected. | `research/83` (audit doc) |
| `research/82` | SMA150 decision | **Not materially affected** — V1/V2 already failed TO gate; V3 non-improving. | — |
| `research/83` | Instrumentation audit | **Affected** — exit counts from buggy simulator. | `research/84` |
| `research/84` | State machine audit | **Already corrected** — documents bug and corrected results. | Already current |

## Scanner check

The daily scanner (`src/daily_screen.py`) does NOT contain portfolio simulation, exit logic, or the defective state machine. It computes factor scores, ranks stocks, and produces decision-support reports. **The scanner is unaffected.**

## Summary

| Severity | Count |
|---|---|
| Documents invalidated | 2 (research/78, research/79) |
| Documents partially affected | 3 (research/75, research/76, research/81) |
| Modules requiring rerun | 3 (price_persistence.py, a3_exit2_evaluation.py, a3_sma150_exit.py) |
| Modules with corrected version | 1 (corrected_exit2_evaluation.py) |
| Modules unaffected | src/daily_screen.py, all data/ and research/configs/ |
