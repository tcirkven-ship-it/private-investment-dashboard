# Phase 1B statement aliases and semantic reconciliation

**Alias version:** `YF-ALIAS-1.0.0`  
**Alias configuration:** `research/configs/yfinance_statement_aliases_v1.json`  
**SHA-256:** `4a49cf35323fd75f64677dacc4cccb502400fc595f0c512ef3ff246f70e8cbba`

## Alias layer

All statement access is by explicit row name. Each canonical concept records accepted aliases, preferred endpoint/frequency, fallback order, sign, units, and limitations. Unknown rows remain missing; positional rows and zero imputation are prohibited.

The full-universe usage report is in `outputs/experiment_runs/EXP-0014/statement_alias_usage_summary.csv`. The main canonical fields were resolved as follows:

- `TotalRevenue`, `NetIncome`, `EBIT`, `OperatingCashFlow`, `FreeCashFlow`, `TotalAssets`, `StockholdersEquity`, and `OrdinarySharesNumber`: 698/698.
- Gross profit/cost of revenue: 677/698; 21 unresolved.
- Operating income: 696/698; two unresolved.
- Total debt: 695/698; three unresolved.
- Capital expenditure: 695/698; three unresolved.
- Interest expense: 639/698; 59 unresolved.
- Dividend, repurchase, and issuance rows remain materially sparse. Issuance is unresolved for 346 companies.

`TotalNonCurrentLiabilitiesNetMinorityInterest` was explicitly rejected as an alias for minority interest. Broadly similar labels are not semantic substitutes.

## Reconciliation results

| Test | Comparable | Tolerance | Pass rate | Median relative difference | Decision |
|---|---:|---:|---:|---:|---|
| FCF vs OCF − absolute capex | 695 | 2% | 98.85% | 0.00% | Pass |
| EBITDA vs EBIT + D&A | 695 | 5% | 98.71% | 0.00% | Pass |
| EV bridge, explicit preferred/minority only | 201 | 10% | 96.52% | 0.01% | Semantics pass; breadth insufficient for primary admission |
| Ordinary vs current info shares | 698 | 5% | 89.97% | 0.05% | Pass with outliers; diagnostic caution |
| Gross profit vs revenue − cost | 677 | 2% | 99.56% | 0.00% | Pass |
| Statement operating margin vs info margin | 586 | 2 percentage-point relative rule | 50.00% | 2.01% | Fail for primary use |
| Split ratio vs observed share-history jump | 142 events | 15% | 47.89% | 16.42% | Fail; share history appears frequently adjusted/non-event-like |

Annual-flow comparisons use four quarterly periods date-aligned to the same annual fiscal end—not the latest four quarters. Pass rates were 99.49% for revenue, 98.47% for operating income, 99.49% for net income, 99.66% for operating cash flow, and 99.32% for free cash flow. Comparable counts were 587–591 because four aligned quarters were not always returned.

## Semantic consequences

- `OP_MARGIN` remains diagnostic because current Yahoo `operatingMargins` does not reconcile consistently with the statement calculation.
- `DILUTION` remains diagnostic because split/share-count behavior does not reconcile consistently.
- `EBIT_EV` remains diagnostic: the explicit EV bridge is accurate where all components exist, but only 201 companies supplied every component.
- FCF-based, gross-profit, revenue-growth, and margin-change factors pass their applicable semantic checks.
- Shareholder yield remains rejected because its three cash-flow components are not jointly reliable or broad.

Observation-level differences, tolerances, notes, and pass flags are preserved in `semantic_reconciliation_observations.csv`.
