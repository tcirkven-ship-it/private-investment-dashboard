# Research continuation decision

**Status:** Phase 1A audit complete; no new optimization authorized  
**Preserved decision:** C03-M/tested price generation remains FAIL for live approval

## Recommendation

If the investor's objective remains the **original historical price-plus-fundamentals mandate**, choose **Path A** and obtain research-grade data before any new strategy test. That is the only path designed to answer the original question.

If the monetary data budget remains **zero**, choose **Path C**. It is honest and useful, but it cannot complete the original historical mandate. Do not run another survivor-biased yfinance/OEF optimization campaign.

Path B is the pragmatic middle choice only if the investor explicitly accepts a narrower question and non-equivalence to the original mandate.

## Path A — Research-grade completion

### Data and design

- Obtain a CRSP-like survivor-aware security/return/event layer and a Compustat-like point-in-time/as-reported fundamental layer, with effective-dated identifiers and a documented link table.
- Obtain historical membership only where an index-membership robustness test is used; use a reproducible broad historical listing universe for the primary test.
- Require written rights for local snapshots, deterministic reruns and aggregate publication.
- Run the vendor gold-set/time-travel audit before factor calculation.
- Create a new preregistration generation. Do not use 2023–2026 as its final holdout.
- Implement the original fundamental families, simpler parents, composites, repeated chronological outer folds, formal multiplicity controls, execution sensitivities, and an untouched future holdout.

### Likely cost/work

Institutional CRSP/Compustat/WRDS pricing is quote-based in the reviewed public material and may be impractical for an individual without university/institutional access. Obtain a written quote rather than estimating a purchase from marketing pages. Work is substantial: security linking, fiscal normalization, vintage controls, corporate actions, delisting treatment, tests and repeated validation are a multi-month research project even after data access.

### Benefit

This is the only path capable of supporting a defensible answer to the full original mandate, including historical fundamental signals and survivorship controls.

### Limitations

Research-grade does not mean perfect: missing delisting returns, provider corrections, classification changes, taxes, FX and model-selection uncertainty remain. A complete study may still conclude FAIL.

## Path B — Reduced-scope but credible research

### Proposed restriction

Before viewing any new result, restrict the question to:

- large, liquid US common stocks from a historical listing/constituent source that passes the pilot;
- the reliable overlap beginning around the modern SEC XBRL era rather than forcing twenty years;
- nonfinancial operating companies initially, with financials/REITs excluded or modeled separately;
- a small subset of well-defined factors whose fields pass time-travel tests—for example momentum, gross profitability, accrual quality and EV-based value;
- monthly selection and quarterly weight correction;
- equal weighting plus contribution-directed buys; and
- a small one-at-a-time parameter neighborhood, not a Cartesian search.

Candidate stacks include an audited Sharadar Core bundle; Norgate plus a purpose-built SEC layer; or paid Massive market/reference data plus SEC as-filed facts. Publicly listed market-data prices range from hundreds of dollars per year for Norgate packages to $29/$79/$199 monthly Massive tiers; Sharadar requires a current quote. Fundamental add-ons, engineering time, VAT and retention constraints are additional.

### Benefit

This can produce credible evidence for a narrower liquid-large-cap, shorter-history question at an individual-researcher budget.

### Limitation

It is **not equivalent** to the original mandate. It has fewer regimes, lower statistical power, fewer factor families, and may exclude sectors or histories central to the broader question. Approval would apply only to the preregistered reduced scope.

## Path C — Forward paper portfolio

### Proposed experiment

Register a new `C03-M-FORWARD-1` paper experiment; do not activate it merely by writing this plan.

- Preserve the C03-M signal: 12–1 total-return momentum, monthly ranking, 30 equal-weight targets, rank-60 retention buffer, $5 price and $5 million 63-day median dollar-volume eligibility.
- Use each universe snapshot only from its effective date forward. Archive official OEF holdings monthly or replace OEF with a clearly frozen forward listing rule.
- Simulate $250 on the first trading session on or after each Friday, matching the existing code convention.
- Route cash to at most three largest underweights; no discretionary mid-month signal refresh.
- Record raw-share quantities, explicit dividend cash, splits, actions, commissions, residual cash and actual paper order outcomes.
- Use executable paper orders: timestamped regular-hours fractional limit/marketable-limit orders, with unfilled orders left unfilled. Do not substitute adjusted close as an order price.
- Maintain identical SPY and QQQ paper ledgers, including the same contribution availability and execution convention.
- Save immutable weekly data, ranks, holdings, order/fill/rejection, benchmark and manifest snapshots with checksums.
- Make no retrospective rule change. Any change ends the experiment and creates a new ID.

### Observation period

Minimum **36 months**, preferably **60 months**, unless an abandonment rule triggers. This will still contain few independent regimes and cannot by itself prove a durable edge.

### Prespecified abandonment/revision triggers

- Data lineage or snapshot failure that prevents reconstruction.
- Any use of unavailable/future information or a retrospective ledger correction that changes decisions materially.
- Trailing-12-month gross discretionary turnover above the existing 100% limit after the first complete year.
- Persistent inability to implement fractional orders or more than 10% of intended order notional left unfilled over a rolling quarter.
- Sector/name constraint breach not corrected under the frozen rules.
- Absolute drawdown above 50% or more than five percentage points worse than SPY.
- After 36 months, failure of the frozen economic/operational gates. Revision requires a new preregistration; it may not relabel the completed paper period as untouched evidence.

### Cost and benefit

Monetary data cost can remain near zero using yfinance for prototype prices, official OEF snapshots and SEC filings, but operating/engineering cost is meaningful. The benefit is genuinely prospective evidence without historical survivor selection. The limitation is time: several years are required, and the result remains specific to its forward market regime.

## Specific investor decision required

Before further experimentation, the investor must choose the acceptable **evidence and budget tier**:

1. **Original mandate:** authorize research-grade vendor quotations/purchase and multi-month rebuild (Path A).
2. **Narrower mandate:** authorize a defined individual-researcher data budget and accept a shorter/restricted study (Path B).
3. **Zero monetary data budget:** accept forward paper evidence only and a 3–5 year horizon (Path C).

No new factor search, formula change, parameter optimization or use of the consumed 2023–2026 period for selection should begin until that decision is recorded.
