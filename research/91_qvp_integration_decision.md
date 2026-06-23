# QVP integration — decision

**Evidence label:** Exploratory survivor-biased historical Price research

## Architecture comparison summary

A3 P50_Q25_V25 retains 3/30 of the P100 top 30.
B2 P50_Q25_V25 retains 4/30 of the P100 top 30.

## Historical proxy status

Not computed. Historical Q/V factor computation requires dedicated
infrastructure for statement extraction with filing lags. The current
comparison is limited to P100 baselines.

## Decision

**RETAIN P100 CONTROL** — Q/V FAILS OVERLAP GATE

A3 P50_Q25_V25 retains only 3/30 of the P100 top 30.
B2 P50_Q25_V25 retains only 4/30 of the P100 top 30.

The architecture gates require at least 15/30 overlap (half of P100).
The current Q/V factors replace too many Price-driven names.
P50_Q25_V25 does not look recognizably Price-driven.

Options for future investigation:
- Reduce Q/V weight (e.g., P75_Q12.5_V12.5) to increase overlap
- Improve Q/V factor construction to better align with Price
- Accept that Q/V fundamentally changes the portfolio —
  this requires a new strategy generation, not an overlay

## Shadow models

Three automated shadow models defined in `shadow_portfolio_config.json`:
- P100_A3 (price-only baseline)
- P50_Q25_V25_A3 (primary proposed)
- QVP_EQUAL_A3 (equal QVP control)

All models share the same monthly review dates, execution conventions,
universe, and SPY/QQQ cash-flow parity. The shadow ledger must be
maintained by software, not by manual recordkeeping.

No broker connection or order placement is authorized for shadow models.