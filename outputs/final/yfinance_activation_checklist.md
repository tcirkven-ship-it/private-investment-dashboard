# Simplified forward-research activation checklist

**Current readiness:** PASS
**Active prospective design:** `YF-FWD-SIMPLE-001`, `active_waiting_for_first_month_end`
**Superseded:** execution-heavy `YF-FWD-001`, never activated

| Gate | Status |
|---|---|
| Factor formulas and alias version frozen | PASS |
| Universe-refresh rules frozen | PASS |
| YF-QVP N=30 portfolio rules frozen | PASS |
| Next-valid-session raw-Close convention frozen | PASS |
| Variable contributions and SPY/QQQ parity | PASS |
| Deterministic simplified raw-share ledger | PASS |
| Relevant tests | PASS — 48 |
| Two daily-price rehearsals | PASS — byte-identical |
| Immutable source snapshot and manifests | PASS |
| Code/config hashes | PASS |
| Git version control | PASS — post-cleanup base `131632b962c457e71828acd2f5c7cbf2ff19c5b6` |
| Separate explicit activation approval | PASS — received 2026-06-22 |
| Immutable activation manifest | PASS |
| Contribution events registered | 0 — no funding invented |
| Mid-month initial ranking | NOT CREATED — required wait observed |

> The paper results exclude commissions, spreads, slippage, taxes, currency conversion, and broker-specific charges.

No broker, fee schedule, intraday data, partial-fill model or precise order-time simulation is an activation dependency. The experiment is active but waiting for the first completed month-end; it is not a live-trading recommendation.

**Subsequent reset:** this checklist is historical. EXP-0017 is a decoupled evidence ledger and no longer gates access to current scores. Daily/on-demand decision support is a separate version and does not imply a transaction.
