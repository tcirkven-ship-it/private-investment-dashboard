# Yfinance prospective activation readiness decision

> **Superseded decision.** This FAIL applied to execution-heavy `YF-FWD-001`. Broker fees, intraday windows and broker reconciliation were removed from the active protocol by `YF-FWD-SIMPLE-2.0.0`. The current readiness decision is `research/44_simplified_activation_readiness.md`. The old experiment was never activated.

## Decision: FAIL — not ready to activate

Checkpoint 3 completed the requested rehearsal engineering but does not pass every activation gate. `YF-FWD-001` remains `registered_not_started`.

## Completed gates

- Primary hypothesis frozen as `YF-QVP`, N=30, equal target weights, monthly selection, rank-60 retention, quarterly correction, USD 250 Friday-mapped contributions, maximum three underweights, fractional primary, and SPY/QQQ comparators.
- `YF-P`, `YF-QP`, and `YF-QVGP` frozen as ablations; N=20/40, whole shares, and USD 500 biweekly frozen as sensitivities.
- Universe refresh behavior implemented as a reason-coded state machine.
- Five-minute 15:45–15:55 ET paper execution convention selected by a no-return availability smoke test.
- Raw-share ledger, dividends, splits, missing/unfilled/partial orders, cash controls, eligibility/rank exits, trimming, caps, and corporate-action exceptions implemented.
- SPY/QQQ parity implemented and tested.
- 44 repository tests pass.
- Two complete rehearsals on the same score, raw snapshot, intraday archive, and config produced byte-identical directories and identical ledger checksums. They are not prospective trades or recommendations.
- Python 3.12.13 environment and yfinance 1.4.0 dependencies are locked.

## Failed or incomplete gates

1. **No Git commit hash exists.** The workspace is not a Git repository, so the required immutable commit reference cannot be recorded. File hashes exist, but the user explicitly required a Git commit hash before activation.
2. **The cost freeze is incomplete.** The base IBKR commission and fractional schedule are modeled, but venue-dependent exchange, clearing, regulatory, and pass-through fees under Tiered pricing are not. The official broker schedule identifies these as additional costs.
3. **No broker-statement reconciliation exists.** The ledger has deterministic paper tests but no independent sandbox/broker execution reconciliation. This is not required for rehearsal mechanics but is prudent before claiming activation-grade execution fidelity.

The first two are hard activation blockers. Initializing version control and freezing a complete conservative cost schedule would be material follow-up work. After those changes, all checksums and both rehearsals must be regenerated under a new readiness version before the user reviews activation again.

## Rehearsal result

The constrained research target contained 30 names. The USD 250 rehearsal routed hypothetical orders to NTCT, CRUS, and EIX solely because all holdings began at zero and rank was the deterministic underweight tie-break. All three fractional rehearsal limits filled under archived 2026-06-18 bars. The whole-share sensitivity filled two NTCT shares and one EIX share; CRUS rounded to zero. SPY and QQQ received identical USD 250 flows and execution policies. These are mechanics checks, not recommended trades and not part of `YF-FWD-001`.

## Required next action

Do not activate. Establish a version-controlled commit, choose and implement a complete cost/fee convention, rerun tests and both rehearsals, and request a fresh readiness review. Activation still requires a separate explicit instruction afterward.
