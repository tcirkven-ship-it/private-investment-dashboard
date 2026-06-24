# Portfolio concentration test (SURVIVOR-BIASED, APPROXIMATE NON-PIT YFINANCE BACKTEST)

## Aggregate results (2023-03-31 to 2025-12-31)

| Config | Cost | Ann ret | SPY-rel | QQQ-rel | Vol | Max DD | TO r-t | TO 1-way | Avg hold | Worst Q | Best Q | Pos Q % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C30 (N=30) | 10bps | +44.8143% | +22.1597% | +16.5720% | +29.3328% | -27.7881% | 5.69 | 2.85 | 30.0 | — | — | — |
| C20 (N=20) | 10bps | +44.7831% | +22.1285% | +16.5408% | +32.3449% | -30.8091% | 6.21 | 3.11 | 20.0 | — | — | — |
| C15 (N=15) | 10bps | +50.6600% | +28.0054% | +22.4177% | +34.2505% | -33.4739% | 6.37 | 3.18 | 15.0 | — | — | — |
| C30 (N=30) | 25bps | +43.5778% | +20.9232% | +15.3355% | +29.3505% | -27.9270% | 5.69 | 2.85 | 30.0 | — | — | — |
| C20 (N=20) | 25bps | +43.4325% | +20.7779% | +15.1901% | +32.3664% | -30.9674% | 6.21 | 3.11 | 20.0 | — | — | — |
| C15 (N=15) | 25bps | +49.2202% | +26.5656% | +20.9779% | +34.2698% | -33.6232% | 6.37 | 3.18 | 15.0 | — | — | — |
| C30 (N=30) | 50bps | +41.5350% | +18.8803% | +13.2926% | +29.3929% | -28.1583% | 5.69 | 2.85 | 30.0 | — | — | — |
| C20 (N=20) | 50bps | +41.2028% | +18.5482% | +12.9604% | +32.4160% | -31.2312% | 6.21 | 3.11 | 20.0 | — | — | — |
| C15 (N=15) | 50bps | +46.8439% | +24.1893% | +18.6016% | +34.3158% | -33.8720% | 6.37 | 3.18 | 15.0 | — | — | — |

## Current snapshot overlap

| Comparison | Overlap |
|---|---:|
| C30 ∩ C20 | 20 |
| C30 ∩ C15 | 15 |
| C20 ∩ C15 | 15 |

## Concentration diagnostics

| Metric | C30 | C20 | C15 |
|---|---:|---:|---:|
| Max sector exposure | 7/30 | 5/20 | 3/15 |
| Max industry exposure | 7/30 | 5/20 | 3/15 |

## Decision

C20 FAILS IMPROVEMENT GATES. Return improvement only -0.0312% (< 5pp).
C15 FAILS IMPROVEMENT GATES. Drawdown -5.6858% worse (> 5pp).

**Decision: KEEP N30** — neither N20 nor N15 meets all improvement gates.
The 5pp return improvement threshold is not achieved at either concentration level.