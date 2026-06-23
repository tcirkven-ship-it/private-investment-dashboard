# A3 SMA150 exit experiment — preregistration

**Evidence label:** Post-confirmatory exit-mechanics robustness research using a survivor-biased historical yfinance universe.

## Variants

| ID | Rank exit | SMA exit | Entry SMA req | Exit logic |
|---|---|---|---|---|
| V0 | 2-consecutive below 60 | No | No | rank-only |
| V1 | No | Close < SMA150 | Yes | SMA-only |
| V2 | 2-consecutive below 60 | Close < SMA150 | Yes | OR (either triggers) |
| V3 | 2-consecutive below 60 | Close < SMA150 | Yes | AND (both required) |

SMA150 = simple mean of latest 150 adjusted daily closes.
Trend condition: AdjClose[t] < SMA150[t] at monthly score date.
Transaction at next valid session close.

## Common mechanics

- A3 = 0.5×rank(M12_1) + 0.5×rank(M6_1), N=30, monthly review
- Rank-60 retention for V0/V2/V3; SMA150 entry required for V1-V3
- Survivors drift; quarterly corrective rebalance
- 10bps one-way cost sensitivity primary
- SPY and QQQ benchmarks
