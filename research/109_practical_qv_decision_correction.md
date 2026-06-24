# Practical QV — decision correction (SURVIVOR-BIASED, APPROXIMATE NON-PIT YFINANCE BACKTEST)

## Supersession

This document supersedes the M0 B2 P100 pilot selection in `research/108`.
The previous conclusion incorrectly stated that M0 passes all practical
gates. Every model fails the frozen 200% annual turnover gate.

## Corrected conclusion

**NO MODEL PASSES ALL FROZEN PRACTICAL GATES — LIMITED-CAPITAL PILOT
REQUIRES AN EXPLICIT TURNOVER-GATE OVERRIDE**

## Pilot candidate comparison

| Criterion | M0 B2 P100 | M1 B2 Q veto | M2 B2 V veto |
|---|---:|---:|---:|
| Ann ret | +50.9451% | +44.8143% | +50.0726% |
| SPY rel | +28.2904% | +22.1597% | +27.4180% |
| QQQ rel | +22.7027% | +16.5720% | +21.8303% |
| Vol | +34.6060% | +29.3328% | +27.9627% |
| Max DD | -34.6040% | -27.7881% | -26.8999% |
| TO | 5.85 | 5.69 | 5.78 |

## Selection (with TO override)

**SELECT M1 B2 QUALITY VETO FOR LIMITED-CAPITAL PILOT WITH TURNOVER-GATE OVERRIDE**

M1 is preferred over M0 because:
- Lower volatility (29.3% vs 34.6%)
- Lower drawdown (-27.8% vs -34.6%)
- Quality filter is historically defensible (annual statements with 3mo lag)
- Comparable returns (44.8% vs 50.9%)
- 569% turnover vs 585% — similar

M2 (Value veto) is NOT selected because proxy Value uses current shares ×
historical price — non-PIT and vulnerable to share-count changes.

## Pilot limitations

1. Survivor-biased current universe — no inactive/delisted securities
2. Approximately 3 years of usable Q/V data (2023-2025)
3. Non-PIT Value proxy for M2 (not applicable to selected M1)
4. Turnover (~569%) far above the frozen 200% ceiling
5. Potential tax impact from high turnover (short-term gains)
6. Spread and commission costs not fully modeled at 10bps
7. No guarantee that historical returns will persist
8. Limited-capital pilot only — not a validated strategy