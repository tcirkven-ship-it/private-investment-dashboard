# First month-end run instructions — YF-FWD-SIMPLE-001

## Before month-end

Do nothing to ranks or portfolio state. Do not generate a mid-month target list. Record a contribution only when the user explicitly supplies its date and amount; otherwise leave the append-only ledger unchanged.

## Snapshot and decision sequence

After the final completed regular trading session of the first month-end following activation:

1. Verify the activation manifest, Git link, active bundle hashes and clean working state.
2. Create a new timestamped immutable prospective directory; never overwrite the activation baseline or an earlier forward snapshot.
3. Retrieve the complete current universe and all required yfinance bundles with `auto_adjust=False`; archive parameters, endpoint results, raw Close, Adjusted Close, dividends, splits and checksums.
4. Validate completeness and reconstructability before computing any decision.
5. Apply the frozen universe exclusions, alias map and `YF-FACTOR-1.0.0` formulas.
6. Calculate YF-QVP and the fixed YF-P/YF-QP/YF-QVGP comparisons without changing formulas or selecting a replacement from observed results.
7. Rank only after the completed month-end data are archived. Apply N=30, equal targets, rank-60 retention and the existing sector, industry and position constraints.
8. Create the initial paper target and parallel SPY, QQQ and YF-P states. Apply only explicit contribution events, identically to YF-QVP, SPY and QQQ.
9. Date the decision after the completed snapshot. Paper transactions use the first positive raw daily Close on a session strictly after the decision date; defer missing/nonpositive prices. Never transact or value with Adjusted Close.
10. Archive all inputs, outputs, exclusions, constraints, events, decisions and checksums, then append a registry result/status update without rewriting this activation manifest.

Reliable ordinary dividends and splits use the deterministic ledger rules. Suspend an affected position and require manual review for unresolved mergers, acquisitions, spin-offs, bankruptcies, ticker changes, apparent delistings or other complex events; do not fabricate proceeds.

Every report must state: “The paper results exclude commissions, spreads, slippage, taxes, currency conversion, and broker-specific charges.”

The resulting target is a standardized paper-research artifact, not a live order list or personalized investment advice.
