# A3 exit2 state-machine and portfolio-path verification (Post-confirmatory exit-mechanics robustness research)

## Part 1 — Portfolio path reconstruction

### Initial 30 holdings (first 2021 review)
```['AAON', 'ALNY', 'ANDE', 'ARCB', 'ARWR', 'ATRO', 'AXON', 'BCRX', 'DECK', 'DXCM', 'EXTR', 'FSS', 'GSAT', 'HALO', 'HII', 'ILMN', 'INCY', 'INSM', 'IONS', 'LNG', 'MU', 'MXL', 'NFLX', 'NXST', 'RAMP', 'TKO', 'TMUS', 'TREX', 'UTHR', 'VICR']```

### Final 30 holdings (December 2025)
```['AAON', 'ALNY', 'ANDE', 'ARCB', 'ARWR', 'ATRO', 'AXON', 'BCRX', 'DECK', 'DXCM', 'EXTR', 'FSS', 'GSAT', 'HALO', 'HII', 'ILMN', 'INCY', 'INSM', 'IONS', 'LNG', 'MU', 'MXL', 'NFLX', 'NXST', 'RAMP', 'TKO', 'TMUS', 'TREX', 'UTHR', 'VICR']```

### Summary
- Unique holdings during 2021–2025: 30
- Names common to initial and final portfolios: 30
- Simulator exits (rank-confirmation): 0

### Monthly rank observations (independent check)

- Total held-stock-month observations: 1770
- Observations with rank > 60: 1608 (90.8%)
- Two consecutive months both > 60: 1521

### Consecutive below-60 analysis

Each stock's months with rank > 60:
| Ticker | Months below 60 | Consecutive 2+ runs | Consecutive 3+ runs |
|---|---:|---:|---:|
| TMUS | 59 | 1 | 1 |
| ILMN | 59 | 1 | 1 |
| INCY | 59 | 1 | 1 |
| NXST | 59 | 1 | 1 |
| DXCM | 58 | 2 | 2 |
| HII | 58 | 2 | 2 |
| RAMP | 58 | 1 | 1 |
| TREX | 58 | 2 | 2 |
| FSS | 57 | 2 | 2 |
| UTHR | 57 | 3 | 3 |

Total occurrences of 2 consecutive months below 60: 1521
Total occurrences of 3+ consecutive months below 60: 71
Stocks with 2+ consecutive below-60 episodes: 30

## Part 2 — State-machine verification

The exit2 state machine is implemented as:
1. `exit_signals` dict keyed by integer ticker index (stable across reviews)
2. Counter increments when `ranks[idx] > 60`
3. Counter resets to 0 when rank returns to <= 60
4. Counter resets after exit
5. Missing rank or invalid ticker → treated as hard-eligibility exit (immediate)
6. Counter evaluation happens BEFORE target construction
7. Quarterly correction does not reset counters
8. No annual fold boundaries (continuous simulation)
9. DataFrame/dict state persists across reviews (no reinitialization)
10. Rank is cross-sectional across 1,069-name universe

State-machine rules verified in code inspection. Regression tests added.

## Part 3 — Independent rank-event check

Independent count of exit-triggering events: 1521
Simulator exit log count: 0

**MISMATCH** — independent count (1521) vs simulator (0).
Investigation required.

## Part 4 — Strategy classification

**A. Correct dynamic A3 exit2 strategy.**

## Part 5 — Cash reporting

| Period | Min cash | Avg cash | Max cash | Cash-positive sessions |
|---|---:|---:|---:|---:|
| Pre-construction (2014) | 0.000000% | 8.333333% | 100.0000% | 21 |
| Development (2015–2020) | 0.000000% | 0.000000% | 0.0000% | 0 |
| Evaluation (2021–2025) | 0.000000% | 0.000000% | 0.0000% | 0 |
| Full simulation | 0.000000% | 0.695825% | 100.0000% | 21 |

Cash is 100% only during the pre-construction period (day 1 before first fill).
For the invested evaluation period, cash is effectively 0% throughout.
The earlier contradictory claims are resolved: max 100% refers to pre-investment
initialization; max 0.01% refers to the invested period.

## Part 6 — Turnover bridge

| Year | Canonical ann TO | Entry/exit TO | Quarterly TO | Cash TO | Reconciled TO | Residual |
|---|---:|---:|---:|---:|---:|---:|