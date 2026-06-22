# Weekly operating playbook — research and paper tracking only

**Status:** C03-M failed Phase One. This checklist must not be presented as an approved live-investment strategy.

## Ordinary weekly cycle

1. Update the local yfinance price/action snapshot without overwriting prior raw files.
2. Verify retrieval time, checksum, last trading date, missing prices, zero volumes, dividends and splits.
3. Use the last completed month-end score file; do not recalculate ranks mid-month.
4. Reconcile paper holdings, cash and the USD 250 simulated contribution.
5. Check mandatory exceptions: acquisition, delisting, suspension, bankruptcy, stale/missing data or broken corporate-action reconciliation.
6. Identify ordinary rank-buffer exits only at the monthly review; the normal exit threshold is rank worse than 60.
7. Route the simulated contribution to at most three approved holdings with the largest dollar underweights; retain cash if an order would be below USD 25.
8. Generate paper orders only. Never assume an unfilled limit order executed.
9. Check price above USD 5, prior-63-session median dollar volume above USD 5 million, name weight below 7.5%, and sector weight below 30%.
10. For fractional paper orders, model a next-session regular-hours limit/marketable-limit fill with logged slippage; do not use fractional MOC.
11. Record every proposed trade, rejection, price, modeled cost, reason and operator decision.
12. Archive the holdings, ranks, data manifest, orders and ledger under a dated immutable snapshot.

## Month-end review

- Calculate 12–1-month total-return momentum after the final close.
- Require at least 252 prior observations, price at least USD 5, and the liquidity threshold.
- Retain held names ranked 60 or better, subject to constraints.
- Fill vacancies from the highest ranks while limiting each sector to 25% at target weight.
- Submit/model decisions no earlier than the next trading session.

## Quarter-end addition

- Correct eligible holdings toward equal weight.
- Do not sell merely to invest the weekly contribution.
- Record total discretionary turnover and stop the experiment if trailing annualized turnover remains above 100%.

## Unscheduled review triggers

Only corporate action, delisting, bankruptcy, suspension, material data corruption, hard eligibility failure, or a constraint breach justifies an unscheduled review. Price decline alone is not a hard stop-loss rule.

## Research suspension conditions

Suspend scoring and create an incident record if:

- upstream adjusted prices or actions fail reconciliation;
- more than 10% of registered symbols fail the weekly update;
- a ticker/issuer mapping changes without review;
- any future data enter a historical as-of calculation;
- turnover, sector or name limits remain breached;
- the scoring rule is changed without a new preregistration; or
- paper results are being used to imply guaranteed future performance.

