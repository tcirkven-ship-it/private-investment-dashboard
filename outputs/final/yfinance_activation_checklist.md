# Simplified forward-research activation checklist

**Current readiness:** PASS  
**Active prospective design:** `YF-FWD-SIMPLE-001`, not activated  
**Superseded:** execution-heavy `YF-FWD-001`, never activated

| Gate | Status |
|---|---|
| Factor formulas and alias version frozen | PASS |
| Universe-refresh rules frozen | PASS |
| YF-QVP N=30 portfolio rules frozen | PASS |
| Next-valid-session raw-Close convention frozen | PASS |
| Variable contributions and SPY/QQQ parity | PASS |
| Deterministic simplified raw-share ledger | PASS |
| Relevant tests | PASS — 44 |
| Two daily-price rehearsals | PASS — byte-identical |
| Immutable source snapshot and manifests | PASS |
| Code/config hashes | PASS |
| Git version control | PASS — `dfa839130a9fc5ea288c07cabefeae2f0e1240c4` |
| Separate explicit activation approval | PENDING — not given |

> The paper results exclude commissions, spreads, slippage, taxes, currency conversion, and broker-specific charges.

No broker, fee schedule, intraday data, partial-fill model or precise order-time simulation is an activation dependency. PASS means ready to start the simplified paper observation after separate approval; it is not a live-trading recommendation.

