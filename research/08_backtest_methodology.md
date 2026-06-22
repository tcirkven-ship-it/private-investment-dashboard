# Backtest architecture and methodology

**Version:** 0.1 preregistration draft  
**Status:** Architecture only; no market data selected and no results computed  
**As of:** 2026-06-21

## Design objective

Build the smallest research system that can reproduce point-in-time eligibility, signals, portfolio decisions, recurring cash flows, attainable execution, costs, corporate actions, and contribution-matched benchmarks. It is a research ledger, not a trading application.

## Layered architecture

| Layer | Inputs | Output | Required audit control |
|---|---|---|---|
| Raw ingestion | Vendor files/API responses and metadata | Immutable snapshots in `data/raw/` | Retrieval time, provider/version, checksum, schema, license note |
| Identity and events | Permanent IDs, tickers, listings, delistings, mergers, splits, dividends | Security master and corporate-action event table | No ticker-only joins; balanced event reconciliation |
| Point-in-time fundamentals | Filing/publication timestamps, fiscal periods, original/restated values | As-of facts with availability timestamps | As-of query tests; no future filing visible |
| Market data | Prices, volume, shares, adjustment factors | Raw and derived market series | Split/dividend consistency; missing-session flags |
| Universe | Historical listings/constituents and eligibility facts | Dated eligible-security set | No current-constituent reconstruction; delisted names retained |
| Factors | Frozen formulas and lags | Dated raw values, winsorized values, ranks, composite scores | Cross-sectional timestamp checks; missingness log |
| Portfolio decision | Holdings, cash, scores, constraints, contribution | Target and proposed order list | Deterministic tie-breaks; decision snapshot archived |
| Execution | Orders, next attainable prices, spread/slippage/commission model | Fills and rejected/unfilled orders | Signal time precedes fill time; no negative cash |
| Accounting | Fills, cash flows, dividends, events, fees | Position, cash, tax-independent portfolio ledger | Shares and cash roll forward exactly |
| Reporting | Ledger and benchmark ledgers | Metrics, tables, charts, machine-readable results | Metric unit tests and reconciliation |

## Research clock

Every observation has at least four times:

1. `observation_period_end`: economic period the value describes;
2. `available_at`: earliest timestamp the research is allowed to know it;
3. `decision_at`: when eligibility, signals, and orders are frozen;
4. `fill_at`: attainable modeled execution time.

The engine rejects records where `available_at > decision_at` and orders where a required end-of-day input is available only after the modeled fill. Fundamentals use verified filing/publication time when trustworthy; otherwise the protocol applies a conservative lag stated in the experiment configuration.

## Portfolio event order

For each scheduled event, the engine processes a fixed order:

1. apply splits, mergers, delistings, cash distributions, and other effective corporate actions;
2. post contributions that are actually available;
3. update point-in-time eligibility and signals using only `available_at <= decision_at`;
4. handle mandatory corporate-action or eligibility exits;
5. apply normal rank buffers, holding-period rules, no-trade bands, and turnover budget;
6. direct new cash to underweight approved holdings before creating avoidable sells, if that policy is active;
7. create orders with deterministic tie-breaking;
8. execute at the configured attainable price and charge all costs;
9. preserve uninvested residual cash; and
10. archive the decision, order, fill, holding, and cash snapshots.

Unscheduled risk reviews may generate orders only for a frozen list of exceptional events. They are not a discretionary way to improve a backtest after observing prices.

## Benchmark construction

Each benchmark receives exactly the strategy’s external contribution amount and availability timestamp. The benchmark ledger uses total-return data or an investable proxy with dividends, fees, fractional/whole-share rules, residual cash, and transaction costs modeled consistently. At minimum:

- S&P 500 total return and a practical proxy such as SPY when needed;
- Nasdaq-100 total return and a practical proxy such as QQQ when needed;
- Nasdaq Composite only when suitable total-return data are available; and
- a broad US market diagnostic.

Comparisons report index-theoretical and investable-proxy results separately. A lump-sum benchmark is never compared with a contribution-funded strategy as the primary result.

## Cost model

All experiments store a versioned cost configuration. Current broker facts will be verified later; the architecture already requires:

| Component | Low | Expected | Stressed |
|---|---|---|---|
| Commission | Verified schedule or zero where genuinely applicable | Verified schedule plus minimums | Higher of verified schedule and conservative generic floor |
| Half-spread | Security/date-specific estimate where reliable | Liquidity-bucket estimate | Adverse percentile by liquidity bucket |
| Slippage | Small liquid-universe allowance | Side- and volatility-aware model | Multiplied expected slippage and delayed execution |
| Market impact | Near zero only for demonstrably tiny participation | Participation/liquidity function | Tighter liquidity cap plus higher impact coefficient |
| FX | Zero in pretax USD layer | Explicit only in FX scenario | Small frequent conversions and adverse batch assumptions |
| Benchmark fee | Published expense ratio for proxy | Same | Same plus tracking sensitivity |
| Patient limits | Not assumed filled for free | Probabilistic/missed-order scenario | Missed orders and next-session adverse fill |

No strategy is described as “after cost” unless commission, spread, slippage, residual cash, benchmark expense, and applicable FX assumptions are present.

## Performance accounting

The canonical ledger stores external flows separately from investment returns. Reports include:

- total contributed capital and ending value;
- time-weighted return from subperiod returns around external flows;
- money-weighted return/XIRR using dated investor cash flows;
- CAGR only where its interpretation is meaningful;
- annualized active return against contribution-matched benchmarks;
- volatility, downside volatility, Sharpe, Sortino, beta, model-labeled alpha, information ratio, and capture ratios;
- maximum drawdown, drawdown duration, and Calmar ratio;
- turnover defined both as gross traded value divided by average NAV and sells-only diagnostic;
- cash drag, number of trades, holding period, transaction costs, exposure, concentration, and factor diagnostics; and
- rolling 3-, 5-, and 10-year relative outcomes where the sample supports them.

Return metrics must state cash-flow timing, annualization convention, risk-free series, benchmark series, and whether values are gross, expected-cost net, or stressed-cost net.

## Experiment sequence

1. **Accounting sanity:** deterministic toy ledgers for contributions, dividends, splits, fees, delistings, residual cash, TWR, and XIRR.
2. **Benchmark validation:** reconcile total-return index and investable proxy; prove identical external cash-flow schedules.
3. **Neutral baselines:** equal-weight eligible universe and simple buy-and-hold diagnostics.
4. **Single-factor tests:** one frozen formula at a time, including missingness, coverage, correlation, and turnover.
5. **Preregistered composites:** only evidence-supported simple combinations; include ablations.
6. **Portfolio construction:** size, weights, contribution policy, buffers, and rebalance frequency.
7. **Nested walk-forward:** selection only inside training/validation; stitch untouched test segments.
8. **Robustness and falsification:** costs, lags, universes, regimes, parameter neighborhoods, influential names/years.
9. **Final holdout:** one access after freeze and signed readiness checklist.

## Critical validation tests

Tests must cover at least:

- future-dated fundamentals cannot enter an as-of query;
- current index membership cannot define historical eligibility;
- a delisted security remains in history and receives the configured terminal treatment;
- split shares and price adjust without creating wealth;
- dividends create the correct cash or reinvestment effect exactly once;
- contribution timestamps and amounts are byte-for-byte equal across strategy and benchmark ledgers;
- no-margin rules prevent negative settled cash;
- order fill time is later than signal availability;
- TWR is invariant to a pure external cash flow at the valuation boundary;
- XIRR matches independently calculated toy cases within tolerance;
- turnover excludes external contributions from investment return; and
- deterministic seed/configuration reruns reproduce checksums and metrics.

Benchmark validation and point-in-time leakage tests are release blockers, not optional diagnostics.

## Configuration and output contract

Every run receives a unique experiment ID already present in `research/experiment_registry.csv` and a frozen configuration containing dataset, universe, signal, portfolio, execution, costs, dates, random seed, and code/config checksum. Results are written under `outputs/experiment_runs/<experiment_id>/` with metrics, trades, monthly returns, exposures, diagnostics, and an audit manifest. Failed runs retain their logs and decision.

## What is deliberately not built now

No broker connection, order transmitter, dashboard, production scheduler, credential store, tax engine, or large optimizer belongs in Checkpoint 1.
