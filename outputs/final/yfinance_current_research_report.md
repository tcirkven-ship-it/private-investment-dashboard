# Yfinance current research report

## Executive conclusion

Phase 1B Checkpoint 2 receives a **conditional pass for current-universe engineering and scoring**. It does not approve an investment strategy.

The yfinance-only process found 2,207 unique current screened equities and retained 698 eligible domestic USD nonfinancial/non-REIT names. All ticker bundles completed without endpoint errors. Factor coverage stayed strong in the USD 2B–5B and USD 5B–10B groups, so the earlier 110-large-company sample did not conceal a broad smaller-cap coverage collapse.

Semantic validation mattered. FCF, EBITDA, gross-profit, and date-aligned annual/quarterly identities reconciled well. Yahoo's current operating-margin metadata did not consistently match statement margins; split events did not consistently appear as jumps in share history; and a complete explicit enterprise-value bridge existed for only 201 names. Consequently `OP_MARGIN`, `DILUTION`, and `EBIT_EV` are diagnostic, not primary. Shareholder yield remains rejected.

The frozen current primary sets are:

- Price: `M12_1`, `M6_1`, `TREND200`, inverse `VOL252`;
- Quality: `ROA`, `GPA`, `FCF_MARGIN`, inverse `DEBT_ASSETS`;
- Value: `FCF_YIELD`, `SALES_EV`, `BOOK_MARKET`;
- Growth: `REV_GROWTH`, `MARGIN_CHANGE`.

Strict common-factor scoring produced 698 `YF-P`, 676 `YF-QP`, 674 `YF-QVP`, and 672 `YF-QVGP` scores. The tables are research inspection outputs, not recommended holdings. The current cross-section contains about 11.05 effective independent signals including expectations diagnostics; `RS252_SEC` is redundant with `M12_1` at 0.958 Spearman and is not primary. Revision breadth, EPS trend, revenue-estimate growth, and four-event surprise are implemented for prospective diagnostics; recommendation change is rejected because Yahoo returned consensus counts rather than the required event semantics.

## Proposed next stage—not activated

The proposed primary prospective candidate is `YF-QVP`, with `YF-P`, `YF-QP`, and `YF-QVGP` as ablations and N=30 as the primary size. This choice is based on architecture, coverage, semantics, and current concentration—not returns. `YF-FWD-001` remains inactive pending explicit review of factor sets, ledger tests, fill convention, costs, and success thresholds.

## Biggest unresolved problem

Yfinance still cannot reconstruct a historical investable universe, delisting outcomes, permanent identities, or filing-time/restatement vintages. Better formulas cannot fix that. Price tests on today's names are survivor-biased, and historical statements are only approximate-lag, currently retrievable/restated exploration. The only complete-strategy evidence available under the free-data constraint is a long prospective archive.

## Reproducibility

- Raw snapshot: `data/raw/yfinance_phase1b_checkpoint2/2026-06-22T_currentZ`
- Snapshot manifest SHA-256: `d94f0498e79eddf8b3c96b2b0c56d9dec82fdb9460a4e5b3f30ac6ee5c2c3373`
- Analysis: `outputs/experiment_runs/EXP-0014`
- Content-addressed archive: `data/archive/yfinance_phase1b_cas/manifests/2026-06-22T_currentZ.json`
- Tests: 22 passing

No historical return optimization, live recommendation, target portfolio, brokerage order, or activation occurred.
