# Simplified yfinance prospective paper protocol

**Active protocol version:** `YF-FWD-SIMPLE-2.0.0`  
**Prospective ID:** `YF-FWD-SIMPLE-001`  
**Status:** frozen and activation-ready; not activated  
**Supersedes:** the execution-heavy `YF-FWD-001` design, which was never activated

## Purpose

Prospectively observe whether a transparent Quality + Value + Price ranking process is maintainable and whether its selections add value relative to Price alone, SPY and QQQ. This is low-frequency research, not a broker simulator.

Primary: `YF-QVP`, 30 equal-target-weight names, monthly ranks after the final completed regular session, retain through rank 60, quarterly corrective review, sector/industry/position limits, and cash directed toward at most three largest approved underweights. `YF-P`, `YF-QP` and `YF-QVGP` are frozen ablations and may not replace the primary based on forward returns.

## Data and decision clock

1. Archive the complete month-end yfinance universe, prices, actions, statements, metadata, factor inputs, scores and checksums.
2. Calculate ranks only after the final completed regular trading session and after the immutable snapshot completes.
3. Generate paper decisions from that snapshot.
4. Execute paper buys/sells at the first valid raw official Close on a trading session strictly after the decision date.
5. If raw Close is missing/nonpositive, defer to the next valid session. Never substitute Adjusted Close and never use same-day Close after consuming that day's completed data.
6. Raw Close values holdings. Adjusted data remain permitted only for properly defined total-return price signals.

## Contributions

Contribution amount and date are external inputs. Zero, USD 250, USD 500, USD 1,000, any other positive amount, and weekly/biweekly/monthly/irregular dates are supported. Contributions never change universe, ranks, eligibility, entry/exit or target weights.

Add cash; calculate current approved target values; buy up to three largest underweights without contribution-driven sales; retain residual cash. Fractional shares are mathematically available in the primary paper ledger. Whole shares are a nonblocking sensitivity.

## Accounting and parity

Maintain raw shares, cash, external contributions, next-session raw-Close buys/sells, explicit reliable ordinary dividends, verified splits, holdings, target holdings and portfolio value. SPY and QQQ receive exactly the same contribution amounts on the same dates under the same next-valid-session raw-Close, zero-cost, residual-cash and share convention.

For unresolved acquisitions, mergers, spin-offs, bankruptcies, delistings or other events: flag manual review, suspend new activity, preserve verified shares/cash, record uncertainty and do not fabricate proceeds.

> The paper results exclude commissions, spreads, slippage, taxes, currency conversion, and broker-specific charges.

This is an intentional research simplification, not a claim that real trading is costless or that paper returns are realizable.

## Change and activation rule

Any material factor, universe, portfolio, accounting or daily-execution change ends the prospective version and requires a new ID. Activation requires the frozen config, tests, immutable initial snapshot, hashes, Git code commit and separate explicit user approval. Paper success never triggers live trading.

