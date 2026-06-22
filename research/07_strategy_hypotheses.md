# Candidate strategy architecture

**Version:** 0.1 hypothesis draft  
**As of:** 2026-06-21  
**Status:** No data accessed, no results, and no candidate frozen  
**Purpose:** Define a bounded, transparent hypothesis library for later evidence and data review

## 1. Shared research clock

At a scheduled month-end decision date `d` after the regular close:

- market signals may use prices through `d`;
- fundamentals are the latest as-filed facts with verified acceptance/publication no later than the previous session’s close;
- primary processing lag is one full session and robustness lag is five sessions;
- orders use an attainable next-session convention, never the signal-date close; and
- amendments/restatements enter only after their public availability.

If data provide only fiscal period dates or latest-restated history, the test is prototype-only. Fixed 90-calendar-day quarterly and 120-day annual lags may be diagnostics but do not cure historical restatement leakage.

## 2. Primary universe hypothesis

At each decision date, include primary common shares of domestic operating companies on NYSE, Nasdaq, or NYSE American that satisfy:

- at least 252 trading sessions since listing or de-SPAC;
- split-adjusted close at least USD 5;
- point-in-time market capitalization at least USD 1 billion in constant 2026 dollars;
- median prior-63-session dollar volume at least USD 5 million in constant 2026 dollars, with at least 55 observations;
- trading on at least 80% of the prior 63 sessions and a valid current close; and
- for fundamental arms, a latest quarterly period no older than 180 days and annual period no older than 550 days.

Exclude OTC securities, ETFs, closed-end funds/BDCs, preferreds, warrants, units, limited partnerships, royalty trusts, pre-merger SPACs, ADRs, REITs, and financial companies from the primary accounting universe. Financials and REITs need separate field definitions; they are not assigned superficial EV/EBIT, leverage, or gross-profitability comparability. Utilities remain but are ranked within sector. Biotechnology is not excluded as a class.

Required robustness universes, not tunable choices:

- strict liquid: USD 2 billion market cap / USD 10 million median dollar volume;
- large-cap: USD 5 billion / USD 20 million;
- broader diagnostic: USD 500 million / USD 2 million; and
- genuine historical S&P 1500-style membership if licensed dated membership is available.

The constant-dollar floor requires a frozen inflation series at Checkpoint 2.

## 3. Common score transformation

For a signal `x`, convert values to a point-in-time sector percentile from 0 (worst) to 1 (best), using average ranks for ties. If a dated sector contains fewer than 20 eligible names, use the full cross-section and flag the fallback.

Primary composites are simple arithmetic means of percentile ranks. No fitted factor weights, optimizer, or black-box model is permitted in this generation. Deterministic tie-break: higher score, then higher 63-day dollar volume, then ascending permanent security ID.

## 4. Primitive signal dictionary

Accounting flows use trailing four consecutively available quarters unless a formula is explicitly annual.

| ID | Proposed formula | Direction and interpretation | Main data caveat |
|---|---|---|---|
| `P` Profitability | Mean sector ranks of `(Revenue − COGS) / average assets` and `EBIT / average invested capital`, where invested capital is debt + preferred + common equity − cash | Higher is better; operating productivity | Nonpositive invested capital is missing; financials excluded |
| `Q` Quality | Mean of `P`, negative accruals `(CFO − net income) / average assets`, and negative 12-quarter SD of quarterly net income/assets | Profitability, cash conversion, stability | Requires consecutive quarters and exact cash-flow signs |
| `V` Value | Mean sector ranks of `EBIT / EV` and `FCF / EV`, with `FCF = CFO − capex` and `EV = market equity + debt + preferred + minority interest − cash` | Higher yield is cheaper | EV must be positive; negative earnings/FCF remain valid low ranks |
| `M` Momentum | Total return from `d−252` to `d−21` | Higher 12–1-month return is better | Corporate-action and dividend consistency required |
| `I` Conservative investment | Negative annual asset growth | Lower growth ranks higher | Acquisitions and sector economics can distort meaning |
| `F` Financial strength | Sector rank of 0–9 Piotroski score using latest two available fiscal years | Higher is stronger | Original setting was high book-to-market; issuance fields can be weak |
| `Y` Net shareholder yield | `(common dividends + common repurchases − common equity issuance) / current market cap` | Higher net distribution is better | Repurchase and issuance history may be incomplete |
| `L` Low risk | Negative annualized SD of daily log total returns over 252 sessions, at least 200 returns | Lower volatility ranks higher | Beta/sector/valuation exposures require attribution |
| `G` Durable growth | Three-year revenue CAGR, positive endpoints; QGARP entry requires positive raw CAGR | Higher positive growth is better | Mature-reporting and survivorship selection risk |

The Piotroski components are: positive ROA, positive CFO, rising ROA, CFO greater than net income, falling long-term-debt/assets, rising current ratio, no common-equity issuance, rising gross margin, and rising asset turnover.

## 5. Preregistered candidate families

| Candidate | Score/gate | Incremental claim | Primary falsifier |
|---|---|---|---|
| C01-Q | `Q` | Quality adds after-cost OOS value | Cash-conversion/stability ablations show only profitability or missingness selection |
| C02-V | `V` | Value survives without microcaps | Large/liquid universe, lag, or distress controls remove it |
| C03-M | `M` | Momentum survives next-session fills and turnover costs | Only same-close or one schedule works |
| C04-QV | `(Q + V) / 2` | Quality mitigates value traps | No OOS return, drawdown, or consistency gain over both parents |
| C05-QM | `(Q + M) / 2` | Quality moderates fragile momentum | No prespecified benefit over both parents |
| C06-VM | `(V + M) / 2` | Opposing failure modes diversify | One leg entirely determines ranks/results |
| C07-QVM | `(Q + V + M) / 3` | Balanced core is more regime-robust | Fails best two-family parent or leave-one-out test |
| C08-QGARP | `(Q + V + G) / 3`; entry `Q ≥ 0.50`, `V ≥ 0.25`, raw revenue CAGR > 0 | Growth adds only with adequate quality and valuation | Growth adds nothing, recreates momentum, or one gate supplies result |
| C09-PY | `(P + Y) / 2` | Profitability plus net payout captures operating and capital discipline | Debt-funded payouts, field errors, or one leg dominates |
| C10-ENS | Equal mean of `Q,V,M,I,F,Y,L` | Broad ensemble trades peak return for stability | No prespecified risk/consistency benefit over C07, or redundant legs add only missingness/turnover |

These ten satisfy the requested family comparison without inventing more factor variants. Earnings revisions remain outside this generation unless a credible timestamped source passes the data gate.

## 6. Shared portfolio hypothesis

- Monthly score review; weekly contributions use the last frozen approved list.
- Baseline `N = 30`, equal-weight target; primary neighbors 20 and 40.
- Enter the highest-ranked eligible non-held names subject to constraints.
- Normal exit when global candidate rank is worse than `2N`; buffer neighbor `1.5N`.
- No stop loss in the primary rule.
- Entry caps: 5% name, 25% sector, 15% industry.
- Drift-review caps: 7.5% name, 30% sector, 20% industry.
- Correct weights quarterly only when absolute name drift exceeds 2 percentage points.
- Gross 12-month discretionary turnover budget: 100%; mandatory action/delisting/hard-eligibility exits are exempt and separately reported.
- Allocate each weekly contribution to at most three approved holdings with the largest dollar shortfalls to target, proportional to deficits; minimum order USD 25; retain residual cash.
- Fractional shares are the primary operational assumption; whole-share/residual-cash is mandatory sensitivity.
- If constraints prevent filling `N`, hold cash rather than violate limits.
- Weekly cash does not trigger discretionary selling or a fresh signal search.

Hard review/exit events: delisting, acquisition, bankruptcy, suspension, loss of common-share eligibility; price below USD 3; real market cap below USD 750 million; real 63-day dollar volume below USD 3 million at two consecutive month-ends; required fundamentals stale beyond 240 days or missing for two reviews; or an unresolvable constraint breach.

## 7. Missing-data and sector rules

- Explicit zero is a value; unknown is not zero.
- A primitive requires all of its listed components; missing a family affects only arms using that family.
- No favorable forward-fill or cross-sectional imputation in the primary case.
- A holding that unexpectedly loses a score receives no new contribution and is frozen for one review; persistent absence forces exit at the next review.
- Report coverage and missingness by date, sector, size, and eventual outcome.
- Required diagnostics: neutral rank `0.5` imputation, common-support Q/V/M comparison, and missingness-indicator analysis.
- Primary ranks are sector-neutral; raw market-wide ranks are a required robustness case.
- Current sector labels cannot be projected backward.

## 8. Bounded parameter neighborhoods

Do not run a Cartesian product. Test the baseline plus one-at-a-time neighbors:

| Choice | Baseline | Neighbors |
|---|---|---|
| Momentum | 12–1 months | 6–1, 9–1 |
| Portfolio size | 30 | 20, 40 |
| Rank buffer | `2N` | `1.5N` |
| Two-family weights | 50/50 | 40/60, 60/40 |
| Three-family weights | Equal thirds | Three 40/30/30 rotations |
| QGARP `(Q,V)` gates | (0.50, 0.25) | (0.40, 0.20), (0.60, 0.30) |
| Sector cap | 25% | 20%, 30% |
| Contribution order count | 3 | 1, 5 |
| Fundamental processing lag | 1 session | 5 sessions |
| Selection/weight correction | Monthly/quarterly | Monthly/monthly, quarterly/quarterly |

The wider requested portfolio-size grid from 10 to 75 is a separate portfolio-construction workstream and is not crossed with every strategy.

## 9. Required ablations and falsification

Run: each primitive; each quality component removed; EBIT/EV vs FCF/EV; each momentum lookback; each composite vs parents; leave-one-family-out C10; QGARP without growth and each gate; sector-neutral vs raw; primary vs strict/large universes; complete cases vs neutral missing ranks; expected/stressed costs, delayed execution, and no fractions; buffer/rebalance/turnover controls removed; removal of best stock/year/top sector; and equal-weight eligible-universe/matched-sector baselines.

Reject or downgrade a family if it depends on current constituents, later restatements, unavailable filings, same-close fills, omitted delistings/dividends, inconsistent benchmark cash flows, one exact parameter, small/illiquid names, missingness, one sector/stock/year, or implausible turnover/cash drag. A composite must add either net OOS return or a prespecified risk/consistency benefit over simpler parents.

An ablation cannot become the preferred strategy without a new preregistration generation.

## 10. Decisions required before freeze

- Validate every primitive’s evidence grade and provider field map.
- Decide whether financials and REITs receive separate models or remain explicit exclusions.
- Freeze inflation series, sector history, field signs, TTM rules, EV components, and repurchase/issuance semantics.
- Reconcile the ten candidates and ablations with the multiple-testing budget.
- Confirm that weekly contributions plus monthly selection fit the investor’s desired operating burden.

Until then, the only authorized experiments are deterministic accounting and benchmark validation tests already in the registry.
