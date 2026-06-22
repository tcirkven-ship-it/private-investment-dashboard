# Phase 1A research audit and gap analysis

**Audit date:** 2026-06-21  
**Scope:** Completed Phase One artifacts through EXP-0010  
**Preservation rule:** The existing experiments and FAIL decision remain unchanged. This audit narrows what that FAIL establishes.

## Corrected conclusion

**C03-M and the nine related price-only variants tested on the current-OEF proxy did not satisfy the frozen best-effort approval standard.** C03-M failed the QQQ holdout, stressed-cost, turnover, uncertainty, and parameter-stability gates. Every candidate also failed the decisive historical-universe/delisting data-integrity gate.

This establishes failure of the **tested preliminary price generation**. It does not establish that momentum generally fails, that direct-stock strategies generally fail, that price-plus-fundamental strategies fail, that passive investing is necessarily superior for this investor, or that no active strategy can satisfy the original objective. Historical point-in-time fundamentals were unavailable and the requested price-plus-fundamentals investigation was not performed.

The 2023–2026 strategy evaluation was run in one batch after code/configuration hashes were recorded. However, the benchmark ledgers already included that period before the strategy freeze, and the raw files were not physically partitioned. It was therefore not a strictly sealed, protocol-compliant final holdout. There is no repository evidence that the strategy outcome was viewed or used to tune C03-M before its run.

## Scope of the evidence

| Statement | Assessment | Audit conclusion |
|---|---|---|
| 1. C03-M failed the preregistered validation standard. | **Supported** | It failed multiple performance/implementation gates and the automatic data gate. |
| 2. All ten registered candidates failed the preregistered standard. | **Supported with scope qualification** | All ten **tested price variants** fail approval, at minimum through the common data-integrity defect. This is not the original C01–C10 fundamental family. |
| 3. Price-only momentum strategies generally fail. | **Unsupported** | One biased mega-cap proxy and a small related grid cannot support a general claim. |
| 4. Direct-stock strategies generally fail. | **Unsupported** | Only a narrow price-only architecture was tested. |
| 5. Price-plus-fundamentals strategies fail. | **Untestable with current evidence** | No historical fundamental strategy was run. |
| 6. Passive investing is necessarily superior for this investor. | **Unsupported** | SPY and QQQ were hurdles, not a personalized allocation proof. |
| 7. No active strategy could satisfy the objectives. | **Untestable with current evidence** | The audit rejects this generation, not the full feasible strategy class. |

“Validation failure” is broader than “strategy failure”: C03-M did not meet the approval protocol, and the available data could not validly estimate the historical performance of the intended strategy class. An attractive biased point estimate cannot cure that defect, but the defect also prevents a general negative conclusion.

## Original-mandate completion matrix

| Requested area | Classification | What was actually established |
|---|---|---|
| Investment-universe construction | Attempted but invalid because of data limitations | A reproducible current 2026 OEF liquid mega-cap proxy was created; it is not a historical eligible universe. |
| Historical constituents | Impossible with available data | No effective-dated OEF/index or broad listing history was available. |
| Delisted securities | Impossible with available data | Inactive listings, terminal proceeds, and delisting returns were absent. |
| Point-in-time fundamentals | Impossible with available data | SEC ingestion was planned but not implemented; no normalized as-filed vintage panel existed. |
| Requested fundamental-factor families | Impossible with available data | Some formulas were architected; none was historically tested. |
| Price factors | Partially completed | 12–1, 9–1 and 6–1 momentum, low volatility, and one momentum/low-volatility rank composite were tested. Most requested price signals were not. |
| Composite scoring | Partially completed | Only equal percentile-rank momentum/low-volatility was run. Fundamental composites and alternate transformations were not. |
| Portfolio-size testing | Partially completed | N=10, 20, 30, 40 and 50 were tested; 15, 25 and 75 were omitted. |
| Position sizing | Partially completed | Equal target weights and contribution-directed underweight filling only. Score, volatility and constrained-risk sizing were not tested. |
| Contribution allocation | Partially completed | Up to three underweight buys plus weekly/biweekly/monthly cash schedules. Other requested allocation/no-trade/whole-share alternatives were absent. |
| Entry rules | Partially completed | Momentum rank, history, price, liquidity and current-sector constraints. No quality, valuation, persistence or filing-freshness gates. |
| Exit rules | Partially completed | Rank-60/eligibility exits, position trimming and quarterly correction. Fundamental, revision, trend, and genuine terminal-event exits were not tested. |
| Stop-loss alternatives | Not attempted | The no-stop baseline was used; trailing and volatility-adjusted stops were not compared. |
| Rank buffers | Partially completed | The 2N buffer was used; the planned 1.5N neighbor was not tested. |
| Rebalance frequency | Partially completed | Monthly selection/quarterly weight correction only. Contribution-frequency tests were not selection-frequency tests. |
| Execution timing | Partially completed | Month-end signal and next-session synthetic adjusted-close fill. No open/midday/window, delayed, whole-share or missed-limit tests. |
| Transaction costs | Partially completed | Fixed commissions plus generic expected/stressed impact. No historical spread calibration, FX, settlement or missed-fill model. |
| Benchmark construction | Partially completed | Contribution-matched distribution-aware SPY/QQQ proxy ledgers passed accounting checks. Broad-US and full theoretical-index ledgers were not built. |
| Rolling performance | Partially completed | Three- and five-year win rates were coded; ten-year and richer rolling diagnostics were omitted from the original report. |
| Walk-forward validation | Partially completed | Chronological development/walk-forward/holdout labels were used, but no repeated anchored outer folds; the universe defect invalidates definitive inference. |
| Multiple-testing controls | Partially completed | A bounded ten-candidate family and block bootstrap were used. The preregistered studentized/whole-search/deflated-Sharpe controls were not performed. |
| Regime analysis | Partially completed | Retrospective bull/bear and high/low-volatility diagnostics only. |
| Parameter stability | Partially completed | Lookback and portfolio-size neighbors only; buffer, lag, cap, weighting, universe and rebalance neighborhoods were absent. |
| Final holdout | Attempted but invalid because of data/control limitations | One-batch strategy evaluation under frozen hashes, but benchmark holdout information existed before freeze and no physical access control existed. |
| Adversarial review | Partially completed | Substantive falsification was documented; independence of the original reviewer was not evidenced in repository artifacts. Phase 1A added an independent skeptical audit. |
| IBKR practicality | Partially completed | Commissions, fractional support, order burden and fractional-MOC mismatch were reviewed; FX, taxes, account plan, settlement and alternate-fill tracking were incomplete. |

The original project was therefore **not fully completed**. It completed a useful preliminary price-only prototype, benchmark/accounting infrastructure, and a negative validation finding for that prototype.

## OEF historical-universe audit

### Why it was selected

The official iShares OEF snapshot was chosen because it was free, official, reproducible, liquid, bounded, and operationally relevant. It was explicitly a fallback proxy, not the originally intended historical universe.

- Effective holdings date: **2026-06-18**.
- Extract: 101 US/USD equity rows, reduced to 100 issuer-deduplicated names; GOOGL was retained over GOOG by current fund weight.
- Eligibility at each signal date: at least 252 price observations, raw close at least USD 5, and prior-63-session median dollar volume of at least USD 5 million.
- Current sector labels and one currently preferred share class were projected backward.

### What is missing and why it matters

Former constituents that were removed, acquired, bankrupt, delisted, or simply ceased to be mega-caps are absent. Conditioning the 2010 opportunity set on survival and membership in 2026 plausibly inflates estimated momentum returns and understates drawdown/terminal-loss risk. The exact bias is not mechanically guaranteed for every period, but it is structurally material and cannot be quantified from the survivor-only data.

The existing approximate attribution reinforces the concern without measuring the missing counterfactual: the top five current winners generated about 28.5% of approximate profit, the top ten 46.9%, and the top twenty 68.7%. MU alone was 7.45%, so the result was not dependent on one stock; it was broadly dependent on a universe composed of companies that survived and became/remained important by 2026.

No result based on this backward-projected universe can support a live active recommendation.

## Fundamental-research gap inventory

All accounting signals require accession-specific as-reported values, verified filing/acceptance timestamps, one-session primary and five-session sensitivity lags, effective-dated security mapping, and point-in-time shares/sector/market values. Latest-restated histories projected backward are not adequate.

| Requested factor | Tested? | Intended formula/status | Minimum indispensable inputs | Main comparability/vintage issue |
|---|---|---|---|---|
| ROIC | No | EBIT / average invested capital; IC = debt + preferred + common equity − cash | EBIT, debt, preferred, equity, cash, adjacent balance dates, 4-quarter TTM | Not comparable for financials; nonpositive IC rule required |
| Gross profitability | No | (Revenue − COGS) / average assets | Revenue, COGS, assets, 4 quarters plus prior balance | Financial/REIT taxonomy and sector effects |
| ROE | No; formula not frozen | Net income attributable to common / average common equity | Attribution, preferred dividends, common equity | Negative/small equity and bank economics |
| ROA | No; denominator not fully frozen | Net income / average assets | Net income, assets | Capital-intensity and financial-sector differences |
| Operating margin | No; formula not frozen | Operating income or EBIT / revenue | Operating income/EBIT, revenue | Banks lack comparable sales/operating structure |
| FCF margin | No; formula not frozen | (CFO − capex) / revenue | CFO, capex, revenue | Capex signs, leases and sector capital intensity |
| Earnings/cash-flow stability | No | Earnings: negative 12-quarter SD of quarterly NI/assets; cash-flow formula not frozen | 12 consecutive quarters of NI, assets and CFO | Missing-quarter selection and fiscal alignment |
| Accrual quality | No | (CFO − net income) / average assets, higher is better | CFO, NI, assets | Financial companies require different interpretation |
| Piotroski strength | No | Nine-component F-score | Two annual statements covering profitability, leverage/liquidity, issuance and efficiency | Original setting was high book-to-market; universal use is an extension |
| Leverage | No standalone | Falling long-term debt/assets appeared only inside F-score | Debt, assets, cash if net leverage | Utilities/financials are structurally leveraged; lease rules matter |
| Interest coverage | No; formula not frozen | EBIT or EBITDA / interest expense | TTM EBIT/EBITDA and interest | Interest is operating for banks; negative EBIT rules needed |
| Balance-sheet strength | No; composite not frozen | Only partial F-score concepts defined | Debt, cash, current items, equity/liabilities | Requires sector-specific treatment |
| Bankruptcy risk | No; model not frozen | Altman/Ohlson/CHS choice unresolved | Model-dependent statements, market cap, returns and volatility | Calibration and sector exclusions are essential |
| Earnings yield | No standalone | EBIT/EV was defined instead | TTM EBIT/NI, point-in-time market cap or EV | Negative earnings and financial-sector valuation |
| FCF yield | No | (CFO − capex) / EV | CFO, capex and all EV components | Financials excluded; negative FCF retained as low rank |
| Enterprise-value valuation | No | EBIT/EV and FCF/EV; EV includes debt, preferred, minority interest less cash | TTM flows plus point-in-time shares/price and balance items | Positive-EV rule; financial/REIT treatment |
| Book-to-market | No; formula not frozen | Common book equity / market equity | Adjusted common equity and point-in-time market cap | Negative equity and intangible-heavy sectors |
| Sales-based valuation | No; formula not frozen | Price/sales or EV/sales unresolved | Revenue, market cap/EV | Thin-margin sectors and banks incomparable |
| Shareholder yield | No | (Common dividends + repurchases − common issuance) / market cap | Payout/issuance cash flows, shares and market cap | Stock compensation, M&A and repurchase taxonomy |
| Revenue growth | No | Three-year revenue CAGR with positive endpoints | Three annual vintages | Acquisitions, divestitures and FX |
| Earnings growth | No; formula not frozen | CAGR/change convention unresolved | Multi-period NI/EPS and shares | Negative bases and dilution |
| FCF growth | No; formula not frozen | Multi-year CFO−capex growth | Multi-year CFO/capex | Negative endpoints and investment cycles |
| Asset growth | No | Negative annual asset growth rank | Two annual asset vintages | Acquisitions and financial/utility economics |
| Capex/investment intensity | No; formula not frozen | Capex/assets or capex/sales unresolved | Capex, assets/revenue, acquisitions/depreciation | Large structural sector differences |
| Earnings revisions | Deferred | No formula frozen | Timestamped estimate vintages, fiscal targets, broker/consensus IDs and actuals | Expensive licensed PIT history; stale-estimate controls |

Price-only C03-M does not answer any of these price-plus-fundamental hypotheses.

## Benchmark-policy audit

SPY and QQQ remain separate required hurdles. Beating both is intentionally demanding because QQQ contains concentrated growth/technology and factor exposures that differ from the broad S&P 500. Failing QQQ can reflect lack of stock-selection skill, an unfavorable factor/sector mix, or both; the hurdle remains failed unless the investor changes it.

Phase 1A added descriptive Fama–French five-factor plus momentum diagnostics. Over the available 2010–2026 factor overlap, C03-M had beta about 1.03 to SPY and 0.83 to QQQ, a large positive momentum loading (0.256), and a negative SMB loading (−0.080), consistent with momentum and mega-cap exposure. QQQ had stronger negative HML/value and CMA/conservative-investment loadings. C03-M's estimated factor alpha was positive, but it comes from the same survivor-biased full sample and is not validation evidence.

Using current 2026 sector labels projected backward, C03-M averaged approximately 19.9% Information Technology and reached 33.1%. Historical SPY/QQQ sector weights were not in the preserved dataset, so exact active technology exposure is unverified. Three-, five-, and ten-year rolling QQQ win rates were approximately 61.4%, 52.5%, and 27.9%; long-window consistency was weak.

## Fractional Market-on-Close correction

The exact modeled transaction—fractional units at the next session's adjusted close—is not an available broker order. More importantly, adjusted close is a synthetic total-return accounting value, not an attainable market price. IBKR's reviewed MOC workflow does not support fractional quantities.

This is primarily an implementation issue, not proof that the economic signal fails. Economically similar alternatives include regular-hours fractional marketable-limit or patient-limit orders, whole-share closing orders with residual cash, and aggregated lower-frequency purchases. Each creates tracking difference through spread/slippage, missed fills, delay, or cash drag and must be tested prospectively. The present model cannot quantify that difference because intraday quotes, fill probabilities, raw-share corporate-action accounting, and whole-share sensitivity were not included.

## Audit bottom line

The largest defect is not ordinary Yahoo price noise. It is conditioning historical selection on 2026 survival/membership, followed by the complete absence of point-in-time fundamental history. The preliminary FAIL remains correct for approving C03-M or this tested generation, while the broader original mandate remains incomplete.
