# Simplified raw-share paper ledger validation

**Active ledger:** `YF-SIMPLE-LEDGER-2.0.0` in `src/paper/simple_ledger.py`  
**Superseded:** intraday/limit/partial-fill/commission ledger in `src/paper/ledger.py` (retained only for audit history)

The active ledger contains cash, externally supplied contributions, raw shares, zero-cost daily-Close buys/sells, raw-Close valuation, reliable ordinary dividends, verified splits, holdings/targets and manual-review suspension.

The 44-test repository suite passes. Simplified readiness tests prove: no same-day Close after a completed-data decision; next-valid-session deferral; variable and irregular contributions; exact strategy/SPY/QQQ contribution parity; fractional arithmetic; whole-share residual cash; zero costs; raw-Close rather than Adjusted Close; dividends; forward/reverse splits; negative-cash prevention; deterministic reconstruction; rank/eligibility exits; quarterly correction; and sector/industry/position limits.

Tests solely for intraday crossing, partial fills, expiration, retries, volume participation and commission formulas were removed from the active suite.

For an unresolved complex corporate action, the ledger suspends activity and preserves verified shares and cash. It records uncertainty but does not estimate/fabricate proceeds. Manual resolution is deliberately outside this small research ledger.

> The paper results exclude commissions, spreads, slippage, taxes, currency conversion, and broker-specific charges.

