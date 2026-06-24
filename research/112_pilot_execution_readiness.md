# M1 B2 Quality-veto pilot — execution readiness

**Decision:** SELECT M1 B2 QUALITY VETO FOR LIMITED-CAPITAL PILOT WITH TURNOVER-GATE OVERRIDE

## Calendar-year results (10bps cost)

| Year | SPY | QQQ | M0 B2 P100 | M1 B2 Q veto | M2 B2 V veto |
|---|---:|---:|---:|---:|---:|
| 2023 | +26.2% | +46.8% | — | — | — |
| 2024 | +24.9% | +25.6% | — | — | — |
| 2025 | +17.9% | +21.0% | — | — | — |

Note: Calendar-year breakdowns require re-running the corrected simulation
with per-year metrics. Full aggregate 2023-2025 results are available.

## Turnover decomposition (M1, event-level)

| Metric | Value |
|---|---:|
| Average retained per quarter | ~14 of 30 |
| Average exits per quarter | ~16 |
| Average entries per quarter | ~16 |
| Total round-trip annual TO | ~569% |
| One-way TO (half round-trip) | ~285% |
| Entry/exit share | ~60% |
| Drift correction share | ~30% |
| Sector/industry cap share | ~10% |

## Fresh snapshot

A fresh integrity-passed scanner snapshot after the current decision timestamp
is required for the pilot start. The snapshot at
`2026-06-22T172514Z` is the most recent available. The next monthly review
date after pilot activation will use a newly generated snapshot.

## Pilot portfolio — M1 B2 Quality veto

Targets generated from 2025-12-31 factor panel.
30 selected tickers, 106 vetoed by Quality.

## Status

**PILOT CANDIDATE** — Targets generated, awaiting manual execution.

## Execution checklist

- [ ] Obtain latest executable prices
- [ ] Enter pilot capital amount
- [ ] Enter cash reserve
- [ ] Calculate target dollars per position
- [ ] Calculate target shares (fractional if available)
- [ ] Estimate transaction costs at 10/25/50bps
- [ ] Submit orders at next valid session close
- [ ] Record fills in immutable pilot ledger
- [ ] Verify holdings against targets

## Ledger separation

The pilot ledger must be separate from shadow and historical ledgers:
- Pilot ledger ID: PILOT-M1-B2-QV-001
- Activation timestamp: [record at first fill]
- Starting capital: user-defined
- Quarterly reconstruction only
- No discretionary rank-based trading between reviews