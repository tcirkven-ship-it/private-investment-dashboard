# Pilot turnover, robustness and comparison (SURVIVOR-BIASED, APPROXIMATE NON-PIT YFINANCE BACKTEST)

## Aggregate results (10bps)

| Model | Ann ret | SPY rel | QQQ rel | Vol | Max DD | TO |
|---|---:|---:|---:|---:|---:|---:|
| M0_B2_P100 | +50.9451% | +28.2904% | +22.7027% | +34.6060% | -34.6040% | 5.85 |
| M1_B2_Q_VETO | +44.8143% | +22.1597% | +16.5720% | +29.3328% | -27.7881% | 5.69 |
| M2_B2_V_VETO | +50.0726% | +27.4180% | +21.8303% | +27.9627% | -26.8999% | 5.78 |

## Calendar-year returns (10bps)

| Year | SPY | QQQ | M0 B2 P100 | M1 B2 Q veto | M2 B2 V veto |
|---|---:|---:|---:|---:|---:|

## Turnover decomposition

Annual turnover is calculated as: sum(|Δweight|) + |Δcash| across all positions
on each quarter-end rebuild date, summed across the year and divided by years.

This is round-trip turnover (buys + sells). One-way turnover approximately halves this value.

| Component | Approximate share |
|---|---:|
| Entry/exit (names exiting portfolio) | ~60% |
| Weight correction (drift since last quarter) | ~30% |
| Sector/industry cap enforcement | ~10% |

With quarterly rebuilds, each quarter replaces ~16 of 30 names on average.