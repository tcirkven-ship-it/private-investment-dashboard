# Phase 1B Checkpoint 2 decision

## Decision: conditional pass for current research implementation

Checkpoint 2 passes its engineering and current-cross-sectional objective with conditions. The full current universe is not truncated, all 698 eligible ticker bundles are clean, the alias layer is explicit and tested, semantic failures changed admission, fixed common factor sets were scored, and immutable storage is implemented.

This decision does **not** approve a historical fundamental backtest, claim durable outperformance, activate `YF-FWD-001`, select a recommended portfolio, or authorize live/paper orders. The evidence ceiling remains unchanged.

## Factor decision

Primary sets are Price `{M12_1, M6_1, TREND200, VOL252}`, Quality `{ROA, GPA, FCF_MARGIN, DEBT_ASSETS}`, Value `{FCF_YIELD, SALES_EV, BOOK_MARKET}`, and Growth `{REV_GROWTH, MARGIN_CHANGE}`. Operating margin, dilution, and EBIT/EV were demoted by semantic reconciliation; shareholder yield remains rejected. Recommendation change is also rejected because the Yahoo endpoint did not supply the upgrade/downgrade events required by the formula. Sector-relative 12-month strength is redundant with `M12_1` and remains diagnostic.

## Inactive primary hypothesis proposal

Propose `YF-QVP` as the primary candidate and retain `YF-P`, `YF-QP`, and `YF-QVGP` as ablations. This is a pre-return architectural choice: QVP combines three independently interpretable categories, scores 674 current names, materially reduces current sector concentration versus price alone, and does not make the two-factor Growth category essential to the primary claim.

Proposed operating rules remain N=30, equal target weights, monthly selection, `2N` rank buffer, quarterly weight correction, USD 250 weekly contributions, and separate SPY/QQQ comparators. Sensitivities are N=20/40, USD 500 biweekly, whole-share versus fractional, and expected/stressed costs. Exact paper-fill convention and cost hashes still require review.

Preliminary success criteria to freeze before activation:

- at least 95% of scheduled complete snapshots reconstruct exactly;
- primary factor coverage remains at least 80% overall and 70% in every included sector;
- zero negative-cash, dividend-double-count, or unreconciled corporate-action ledger defects;
- trailing 12-month gross discretionary turnover at or below 100%;
- after at least 36 months, preferably 60, net annualized TWR and XIRR exceed both contribution-matched SPY and QQQ by at least 1 percentage point, with no materially worse drawdown and positive rolling/uncertainty evidence;
- `YF-QVP` demonstrates a coherent incremental result versus `YF-P`, reported without selecting among ablations after seeing returns.

These criteria are proposals, not active protocol terms.

## Remaining activation blockers

Review the admitted sets, exact execution window/limit rule, paper-ledger tests, costs, and preliminary success thresholds. Only an explicit later approval may freeze and activate `YF-FWD-001`. Any activation must create a new immutable initial snapshot and registry/config hashes; this checkpoint's current score table is inspection evidence only.
