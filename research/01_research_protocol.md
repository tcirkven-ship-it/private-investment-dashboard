# Research protocol and proposed success preregistration

**Protocol ID:** RP-001  
**Version:** 0.1 draft  
**Prepared:** 2026-06-21  
**Freeze status:** Not frozen  
**Final holdout status:** Untouched; no dataset has been selected or loaded

> **Best-effort generation addendum, 2026-06-21:** The user authorized completion using the best available zero-cost data. `RP-001-BEST-EFFORT-V1` was frozen before individual-stock results; its one-use 2023–2026-06-18 holdout is now consumed. The final decision is **FAIL**. See `research/16_final_recommendation.md`. The original integrity thresholds were not weakened.

## 1. Research objective

Determine whether a transparent, long-only portfolio of liquid US-listed individual equities, funded with USD 250 weekly, can produce credible after-cost out-of-sample performance against contribution-matched S&P 500 and Nasdaq-100 benchmarks while remaining operationally realistic for an individual investor using Interactive Brokers.

The result may be **pass**, **conditional pass**, or **fail**. The program does not presume that a successful strategy exists and does not infer future returns from a historical result.

## 2. Scope and exclusions

Included in Phase One: point-in-time data assessment, factor evidence, precise hypotheses, benchmark validation, recurring-contribution accounting, long-only portfolio construction, realistic execution and cost models, chronological backtests, walk-forward validation, robustness, falsification, and a manual or semi-manual playbook.

Excluded until separately authorized: production software, automated order routing, brokerage credentials, live orders, leverage, short selling, options, margin, news/social sentiment, and jurisdiction-specific tax advice.

## 3. Testable claims

### Primary null

After realistic costs and selection-bias controls, no preregistered direct-stock strategy delivers economically meaningful and sufficiently stable out-of-sample performance above both contribution-matched primary benchmarks.

### Primary alternative

At least one simple, evidence-supported strategy satisfies every critical data, performance, risk, stability, implementation, and adversarial-review gate defined below without using the final holdout for rule selection.

### Secondary questions

- Do quality, value, momentum, investment, financial-strength, and shareholder-yield signals survive separately after point-in-time controls?
- Does a simple composite add value beyond its components and beyond factor exposure to small/illiquid stocks?
- What portfolio size and contribution policy balance diversification, turnover, cash drag, and operational burden?
- Do weekly contributions improve outcomes materially relative to USD 500 biweekly or monthly aggregation after costs?
- Does a passive core plus active satellite improve robustness without being misreported as a direct-stock result?

Secondary findings cannot rescue a failed primary objective by silently changing the hurdle.

## 4. Evidence and workstreams

| Workstream | Mandate | Checkpoint output | Independence requirement |
|---|---|---|---|
| A. Literature | Replication-aware evidence for signals, portfolio design, contributions, tax-aware maintenance, and execution | Search log, literature review, evidence matrix | Separate sources from strategy results |
| B. Data integrity | Point-in-time, delisting, identifier, action, licensing, and vendor assessment | Requirements matrix, provider decision, data-quality report | Can reject all affordable options for definitive work |
| C. Strategy architecture | Precise simple candidate families, formulas, lags, ablations, and parameter neighborhoods | Preregistered hypotheses | No final-holdout access |
| D. Statistics | Walk-forward, multiple testing, uncertainty, stability, and holdout audit | Validation protocol and skeptical review | Can veto unsupported success claims |
| E. Portfolio construction | Size, weights, concentration, contribution routing, and turnover | Portfolio comparison plan/results | Must consider burden as well as return |
| F. Execution | Current IBKR facts, costs, order conventions, FX, and practical constraints | Dated operational report | Official sources preferred |
| G. Adversarial review | Attempt to invalidate the preferred candidate | Challenge report and responses | Conducted after main results; cannot be the strategy designer |

## 5. Checkpoint sequence and gates

| Checkpoint | Required completion | Gate to proceed |
|---|---|---|
| 1. Protocol | Plan, assumptions, success draft, source plan, data matrix, backtest/walk-forward architecture, registry | Internal consistency review; no large-scale optimization |
| 2. Data readiness | Vendor comparison, selected dataset/version, QA report, bias and license assessment | Data classified definitive, prototype-only, or rejected; holdout dates and access controls set |
| 3. Baselines and single factors | Validated contribution benchmarks, neutral baselines, single-factor results, correlations, falsifications | Benchmark/accounting tests pass; only evidence-supported factors advance |
| 4. Composites and portfolios | Preregistered composites, ablations, sizes, weights, contribution rules, turnover controls | Candidate set and parameter neighborhoods frozen |
| 5. Walk-forward | Stitched OOS results, rolling comparisons, costs, stability, uncertainty | Success protocol frozen before final-holdout access |
| 6. Adversarial review | Independent attack on bias, fills, lags, concentration, regimes, costs, and ambiguity | Every material issue answered or conclusion downgraded |
| 7. Final recommendation | Exact specification or explicit failure, playbook, strategy card, Phase Two options only | No live recommendation from preliminary evidence |

## 6. Proposed success protocol

The thresholds below are **researcher proposals**, not established facts and not yet frozen. They will be finalized before candidate selection can be influenced by final-holdout performance. The unresolved investor drawdown tolerance may tighten the risk gate but may not be loosened in response to poor results.

### 6.1 Measurement basis

- Use the stitched genuinely out-of-sample return path plus one untouched final holdout.
- Compare expected-cost net strategy returns with contribution-matched, investable-proxy benchmark ledgers. Also report theoretical total-return indexes separately.
- The primary funding case is USD 250 weekly. USD 500 biweekly and monthly aggregation are mandatory implementation sensitivities.
- Report both TWR and XIRR. Neither alone determines success.
- Use the S&P 500 and Nasdaq-100 as separate required benchmarks; never average them into an easier hurdle.

### 6.2 Critical pass gates

All critical gates must pass for an unconditional pass.

| Gate | Proposed threshold | Rationale and interpretation |
|---|---|---|
| Data integrity | Definitive-grade classification; survivorship, delisting, actions, filing availability, identifiers, and missingness controls pass documented QA | A strong result on structurally biased data is not evidence of strategy success |
| Benchmark integrity | Exact external cash-flow equality; dividends and proxy expenses included; deterministic accounting tests pass | Eliminates contribution and total-return mismatch |
| Economic TWR | Expected-cost stitched OOS annualized active return at least +1.0 percentage point versus **each** primary benchmark | Seeks a margin large enough to matter after research uncertainty and effort |
| Money-weighted outcome | OOS XIRR advantage at least +1.0 percentage point versus each contribution-matched benchmark in the primary funding case | Confirms that contribution timing does not reverse the claim and applies the same economic hurdle |
| Stressed costs | Active annualized return remains positive versus each benchmark under 2× expected spread/slippage plus applicable commissions | Rejects an edge that disappears under plausible execution friction |
| Independent windows | For a definitive pass, at least 7 non-overlapping annual walk-forward windows; positive active return versus each benchmark in at least 60% with a positive median, and no single window supplies more than 50% of cumulative active wealth | Limits dependence on one episode; 5–6 windows can support at most a conditional conclusion |
| Rolling consistency | Beats each primary benchmark in at least 60% of eligible rolling 3-year and 5-year windows; 10-year windows reported when available | Full-period averages alone are insufficient |
| Uncertainty/selection | One-sided 95% studentized time-series-bootstrap lower bound for mean active return is above zero versus each benchmark; the whole registered search survives a dependence-aware superiority test at 5%, and the selected model has at least 95% deflated-Sharpe probability | Bounds adverse uncertainty and adjusts for model search; conditional evidence may use a positive point estimate with an interval that includes zero |
| Drawdown | Maximum drawdown no more than 5 percentage points worse than the S&P 500 and not above 50% absolute; any investor-supplied lower tolerance replaces the 50% cap | Prevents return-only selection; provisional until investor tolerance is known |
| Volatility | Annualized volatility no more than 1.20 times S&P 500 volatility | Rejects simple risk amplification masquerading as skill |
| Turnover | Expected-case gross annual turnover at or below 100%; stressed-cost case remains viable at realized turnover | Keeps costs and manual maintenance plausible; contribution buys are reported separately |
| Parameter stability | Across the preregistered neighboring grid, at least 70% of valid neighbors have positive active return versus both benchmarks and the neighborhood median retains at least half of the selected configuration’s active return | Prefers plateaus to sharp optima |
| Influence | Removing the best stock and separately the best calendar year does not make active annualized return worse than -0.5 percentage point versus either benchmark; top-name and top-period contributions fully reported | Limits dependence on a lucky outlier |
| Investability | Every modeled order obeys price/liquidity/security-type rules; no negative cash or unavailable fractional assumption; concentration limits pass | A statistical edge must be executable |
| Adversarial review | No unresolved critical bias, leakage, benchmark, cost, or implementation finding | Approval requires an independent attempt to falsify it |

### 6.3 Supporting diagnostics, not substitutes

Sharpe, Sortino, alpha, information ratio, capture ratios, factor regressions, win rate, profit factor, and p-values inform interpretation but cannot compensate for failure of economic, data, or implementation gates. Core-plus-active results are reported as a separate architecture and cannot silently replace a failed direct-stock test.

### 6.4 Decision rule

- **Pass:** Every critical gate passes on stitched OOS and final holdout; exact rules are reproducible; adversarial review has no unresolved critical issue.
- **Conditional pass:** Pooled net outperformance remains positive against both benchmarks, no integrity or fail-band condition occurs, and no more than two secondary gates fall into a prespecified conditional band—for example 5–6 outer windows, 50–59% rolling consistency, 100–150% turnover, a positive point estimate whose interval includes zero, or a named non-performance limitation such as unresolved tax/FX suitability. Conditions and a revalidation plan must be explicit. A structural survivorship or look-ahead defect cannot receive a conditional pass.
- **Fail:** Either benchmark economic gate fails; a critical data/bias/control gate fails; success depends on holdout-led redesign, one narrow parameter, uninvestable securities, or unrealistic fills; or the final holdout contradicts the frozen claim.

Failure does not authorize threshold relaxation. A new strategy generation requires a new preregistration and an unused holdout.

## 7. Bias controls

- Historical universes use dated membership or a broad dated listing universe, never today’s constituents.
- Fundamentals are keyed to actual availability, not merely fiscal period end, and restatements are not backfilled into earlier knowledge.
- Delisted securities and terminal outcomes remain in the opportunity set and portfolio ledger.
- Signal formulas, missing-data rules, lags, tie-breaks, costs, and execution times are configuration-controlled.
- Chronological splits replace random cross-validation.
- Every attempted candidate and parameter grid is logged, including failures.
- Final-holdout files are access-controlled and excluded from exploratory reports until a signed freeze checklist passes.
- Same-day fills are permitted only when every input was demonstrably available before the modeled order cutoff.

## 8. Candidate search budget

The exact count will be frozen at strategy preregistration. Checkpoint 1 limits architecture to the named evidence-supported families: quality, value, momentum, investment/conservatism, financial strength, shareholder yield, and simple two- or three-family composites. Each composite must have a simpler comparator and an ablation. Timing alternatives are an implementation sensitivity, not a large alpha-mining grid.

## 9. Data-dependent decisions still to freeze

Checkpoint 2 must set, without viewing strategy outcomes:

- reliable data start/end dates and final-holdout calendar dates;
- permanent identifier, universe, delisting, and restatement treatment;
- exact fundamental availability lags by data field/provider;
- security types and sector-specific metric handling;
- minimum price, market capitalization, dollar volume, trading history, and IPO seasoning;
- benchmark series/proxies, expense histories, and corporate-action treatment;
- expected and stressed commission/spread/slippage/FX models; and
- physical/logical holdout access controls.

## 10. Checkpoint 1 decision

The protocol is ready for review as a preregistration draft, but research is **not data-ready**. The next decision is whether a provider can meet the critical point-in-time and survivorship requirements at an acceptable cost. No strategy performance experiment should be interpreted before that gate passes.
