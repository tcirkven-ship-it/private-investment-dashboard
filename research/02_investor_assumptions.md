# Investor assumptions and unresolved inputs

**Version:** 0.1 draft  
**As of:** 2026-06-21  
**Purpose:** Define the investor context without converting unresolved personal details into hidden model choices.

## Known project constraints

These are instructions for the research program, not inferred investor facts.

| Item | Working value | Treatment in research |
|---|---|---|
| Broker | Interactive Brokers | Current operational facts must later be verified from official IBKR sources and dated. No account connection is permitted. |
| Primary contribution | USD 250 weekly | Apply identical amount and date to strategy and every benchmark. |
| Alternative contribution | USD 500 every two weeks | Required comparison; also test monthly aggregation. |
| Asset type | Long-only US-listed individual equities | No OTC/penny stocks; ETFs are benchmark instruments or a separately reported core-plus-active alternative. |
| Leverage and derivatives | None | No margin, short sales, or options in tests. |
| Horizon | Multiyear | Evaluate rolling 3-, 5-, and 10-year periods when history allows. |
| Reporting currency | USD | Separate any later FX-aware layer from the pretax USD strategy record. |
| Execution mode | Manual or semi-manual is acceptable | Every surviving rule must be executable from a weekly checklist. |
| Fractional shares | Permitted where supported | Run a no-fraction sensitivity and model residual cash consistently. |
| News and sentiment | Deferred | Not part of core candidate selection in Phase One. |

## Conservative research defaults

These defaults prevent the program from stalling. They are provisional and will be exposed in sensitivity analysis.

| Assumption | Default | Why conservative or practical | Sensitivity required |
|---|---|---|---|
| Contribution timestamp | Cash available before the scheduled decision; otherwise next eligible session | Prevents fictitious use of unavailable cash | Same-day available vs next-session available |
| Signal availability | Prices only after the bar closes; fundamentals only after verified filing/publication timestamp or a conservative lag | Prevents look-ahead | Exact timestamp vs +1 session; longer lags |
| Fill | Next attainable session price under the selected order convention | Avoids same-close execution on end-of-day signals | Open, VWAP proxy, close/auction where information timing permits |
| Fractional execution | Expected case allows eligible fractions; conservative case uses whole shares and residual cash | Reflects likely but non-universal support | Fractional vs whole-share |
| Taxes | Excluded from primary performance | Jurisdiction and account type are unknown | Later jurisdiction-specific layer only |
| FX | Excluded from primary USD performance | Deposit currency is unknown | EUR-to-USD conversion scenario after funding facts are known |
| Investor labor | Weekly review acceptable | Stated project preference | Compare weekly, biweekly, monthly workload and trade count |
| Liquidity | Use a liquid US universe with price, market-cap, and dollar-volume floors | Avoids uninvestable microcaps | Large-cap-only and stricter-liquidity cases |
| Borrowing | Cash balance cannot be negative | Matches no-margin rule | None |
| Missing data | Do not impute a favorable signal; use documented neutral/exclusion rules by field | Prevents missingness from becoming alpha | Alternate neutral vs exclusion treatment |

Exact numeric liquidity floors, accounting lags, and universe cutoffs will be frozen only after the selected dataset’s coverage is measured. Choosing them before inspecting coverage would create false precision.

## Unresolved investor inputs

The research proceeds without these answers, but each can change implementation or the final suitability interpretation.

| Priority | Input needed | Why it matters | Current fallback |
|---|---|---|---|
| High | Country of tax residence, citizenship constraints if relevant, and account type | Dividends, capital gains, withholding, loss treatment, and product access can differ | Report pretax USD and do not provide tax advice |
| High | Deposit currency and expected conversion method | Weekly FX conversion could dominate small-trade costs | Primary USD layer; later batch-conversion sensitivities |
| High | Maximum tolerable peak-to-trough loss and behavioral stop point | Determines whether an otherwise valid strategy is usable | Draft protocol caps relative drawdown deterioration and flags absolute drawdowns above 35% |
| High | Preference for 100% active stocks versus passive core plus active satellite | Changes benchmark tracking, concentration, and burden | Evaluate direct-stock strategy first and core-plus-active separately |
| Medium | Current portfolio and whether new contributions are the only investable cash | Determines transition trades and tax lots | Model a clean start; no forced liquidation |
| Medium | Time available for weekly review and acceptable number of orders | Determines feasible portfolio size and rebalance process | Report trade count and estimated manual burden |
| Medium | Sector, industry, ESG, employer-stock, or security exclusions | Changes universe and diversification | No bespoke exclusions beyond security-type and liquidity rules |
| Medium | Need for income, planned withdrawals, or emergency liquidity | Accumulation assumptions may be inappropriate | No withdrawals in core tests |
| Low now | Preference for market, limit, or closing-auction orders | Affects operational design more than signal research | Test realistic execution conventions later |

## Scenario layers

Results must not blend these layers:

1. **Research return:** pretax USD, point-in-time strategy, benchmark-matched cash flows.
2. **Trading-cost return:** commissions, spread, slippage, residual cash, and benchmark expenses.
3. **FX-aware return:** explicit contribution currency, conversion schedule, and FX cost.
4. **Tax framework:** only after jurisdiction and account facts are supplied; no guessed tax rates.

## Change control

An investor clarification is recorded in `research/decision_log.md`. If it changes universe, signal, portfolio, or success rules after those rules are frozen, the current final holdout cannot be used to select the replacement rule.
