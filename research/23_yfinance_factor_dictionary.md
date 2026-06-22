# Phase 1B proposed yfinance factor dictionary

**Status:** First-checkpoint formulas; admission is conditional on the completed coverage audit  
**Data classification:** Current/prospective, plus explicitly exploratory non-point-in-time statement history  
**Missing rule:** Unknown is missing, never zero

## Common calculation rules

- Preserve yfinance's raw CamelCase statement rows and map them through a versioned alias dictionary.
- For current/prospective flow factors, prefer the trailing statement. If absent, sum four consecutive quarterly periods; use the latest annual value only as a separately flagged fallback.
- For stock variables, use the mean of the latest two available quarterly balance dates where the formula requires an average; otherwise use the latest available balance.
- Current `marketCap`, `enterpriseValue`, analyst estimates and revisions may be used only in the current/prospective cross-section.
- Exploratory historical statements become available at the later of 90 days after a quarterly period end or 120 days after an annual period end. This is conservative lagging, not actual filing-time reconstruction.
- Require trading currency and financial currency to match for unconverted accounting/value factors. Otherwise mark missing until a yfinance-only FX conversion rule is separately frozen.
- Within each included Yahoo sector, winsorize continuous raw factors at 2.5%/97.5% when at least 20 valid names exist; otherwise use the full eligible cross-section and flag the fallback.
- Transform to percentile ranks from 0 (worst) to 1 (best). Ties receive average rank.
- If absolute Spearman correlation exceeds 0.85 persistently, retain the simpler/higher-coverage factor for the primary category and keep the other as a diagnostic.
- Do not impute cross-sectional medians in the primary model. A category score exists only when at least half of its admitted components, with a minimum of two, are present.

## Price and market factors

| ID | Formula | Inputs | Direction | Interpretation/notes |
|---|---|---|---|---|
| `M12_1` | `AdjClose[t-21] / AdjClose[t-252] - 1` | Daily Adjusted Close | Higher | Medium-term continuation; current-universe historical tests remain survivor-biased |
| `M6_1` | `AdjClose[t-21] / AdjClose[t-126] - 1` | Daily Adjusted Close | Higher | Shorter momentum neighbor, not an independently optimized rule |
| `RS63_MKT` | 63-session total return minus SPY 63-session total return | Stock/SPY Adjusted Close | Higher | Market-relative strength |
| `RS252_SEC` | `M12_1` minus current-sector median `M12_1` | Current Yahoo sector and prices | Higher | Sector-relative strength; current sector cannot be projected backward definitively |
| `TREND200` | `AdjClose / mean(AdjClose, 200) - 1` | Daily Adjusted Close | Higher | Long trend state |
| `VOL252` | annualized SD of 252 daily log total returns, min 200 | Adjusted Close | Lower | Total volatility/risk |
| `DOWNVOL252` | annualized root-mean-square of negative daily returns over 252 sessions | Adjusted Close | Lower | Downside variability; zero-negative-return edge cases missing |
| `DD252` | `AdjClose / max(AdjClose, prior 252) - 1` | Adjusted Close | Higher | Current drawdown; less negative is better |
| `LIQ63` | median of raw Close × Volume over 63 sessions, min 55 | Raw Close, Volume | Eligibility/higher diagnostic | Capacity/implementability, primarily a gate rather than alpha score |

The proposed Price category initially uses `M12_1`, `M6_1`, `TREND200`, and inverse `VOL252`. `RS63_MKT`, `RS252_SEC`, downside volatility and drawdown are diagnostics until correlation/stability review.

## Quality and financial-strength factors

| ID | Formula | Primary yfinance rows | Direction and guards |
|---|---|---|---|
| `ROA` | TTM `NetIncome` / average `TotalAssets` | Income, balance | Higher; average assets must be positive |
| `APPROX_ROIC` | TTM `EBIT` / average (`TotalDebt` + `StockholdersEquity` − cash) | Income, balance | Higher; invested capital must be positive; exclude financials/REITs |
| `GPA` | TTM `GrossProfit` / average `TotalAssets` | Income, balance | Higher; exclude sectors without comparable gross profit |
| `OP_MARGIN` | TTM `OperatingIncome` / TTM `TotalRevenue` | Income | Higher; positive revenue required |
| `FCF_MARGIN` | TTM `FreeCashFlow` / TTM `TotalRevenue` | Cash flow, income | Higher; positive revenue required |
| `CASH_CONVERSION` | TTM `OperatingCashFlow` / TTM `NetIncome` | Cash flow, income | Higher within winsorized range; primary use requires positive net income |
| `DEBT_ASSETS` | latest `TotalDebt` / `TotalAssets` | Balance | Lower; positive assets required |
| `NET_DEBT_EBITDA` | (`TotalDebt` − cash) / TTM `EBITDA` | Balance, income | Lower; nonpositive EBITDA is missing and separately distress-flagged |
| `INTEREST_COVER` | TTM `EBIT` / abs(TTM `InterestExpense`) | Income | Higher; absent/zero interest is not automatically infinity; cap/winsorize |
| `EARN_STABILITY` | negative SD of quarterly `NetIncome / TotalAssets` over five reported quarters | Quarterly income/balance | Higher; all five aligned quarters required |
| `DILUTION` | negative (`OrdinarySharesNumber[t] / OrdinarySharesNumber[t-1y] - 1`) | Annual balance; shares history diagnostic | Higher; corporate-action-adjusted consistency must pass |

The primary Quality category will use only admitted, nonredundant factors with at least 80% coverage in the eligible nonfinancial universe. Debt and cash-conversion measures remain separate diagnostics if their coverage or sector meaning is unstable.

## Value factors

These are current/prospective factors because their denominators come from current metadata.

| ID | Formula | Inputs | Guards |
|---|---|---|---|
| `EARN_YIELD` | TTM `NetIncome` / current `marketCap` | Statement + `Ticker.info` | Market cap positive; negative earnings valid low value |
| `FCF_YIELD` | TTM `FreeCashFlow` / current `marketCap` | Statement + info | Market cap positive; negative FCF valid low value |
| `EBIT_EV` | TTM `EBIT` / current `enterpriseValue` | Statement + info | EV positive; financials/REITs excluded |
| `SALES_EV` | TTM `TotalRevenue` / current `enterpriseValue` | Statement + info | EV and revenue positive |
| `BOOK_MARKET` | latest `StockholdersEquity` / current `marketCap` | Balance + info | Positive common equity and market cap |
| `SHAREHOLDER_YIELD` | `-(CommonStockDividendPaid + RepurchaseOfCapitalStock + IssuanceOfCapitalStock) / marketCap` | Cash flow + info | Requires verified Yahoo cash-flow sign convention and all components; otherwise exclude |

The initial Value category proposes `FCF_YIELD`, `EBIT_EV`, `SALES_EV`, and `BOOK_MARKET`, subject to coverage/correlation. Earnings yield and shareholder yield are diagnostics until denominator/sign and field stability pass.

## Growth and investment factors

| ID | Formula | Inputs | Guards |
|---|---|---|---|
| `REV_GROWTH` | latest annual `TotalRevenue` / prior annual − 1 | At least two annual periods | Both denominators positive |
| `OP_INC_GROWTH` | latest annual `OperatingIncome` / prior annual − 1 | Two annual periods | Both values positive; sign changes missing |
| `NI_GROWTH` | latest annual `NetIncome` / prior annual − 1 | Two annual periods | Both values positive; sign changes missing |
| `FCF_GROWTH` | latest annual `FreeCashFlow` / prior annual − 1 | Two annual periods | Both values positive; sign changes missing |
| `MARGIN_CHANGE` | latest TTM/annual operating margin minus prior comparable margin | Income statement | Same frequency and positive revenue required |
| `ASSET_GROWTH` | latest annual `TotalAssets` / prior annual − 1 | Balance | Report both raw growth and inverse conservative-investment rank |

The proposed Growth category uses revenue growth and margin change first; earnings/FCF growth are supplemental because sign-changing bases cause selection bias. Inverse asset growth is a separate conservatism diagnostic rather than silently treated as “growth.”

## Current revisions and expectations

| ID | Formula | Endpoint | Evidence use |
|---|---|---|---|
| `EPS_REV_BREADTH` | `(upLast30days - downLast30days) / max(1, up + down)` averaged over `0q`, `+1q` | `get_eps_revisions()` | Prospective only |
| `EPS_TREND` | current estimate / estimate 30 days ago − 1 for `0y` and `+1y` | `get_eps_trend()` | Prospective only; positive prior estimate required |
| `REV_EST_GROWTH` | current-year average revenue estimate / reported year-ago revenue − 1 | `get_revenue_estimate()` | Prospective only |
| `SURPRISE4` | mean reported `surprisePercent` over latest four events | `get_earnings_history()` | Current/recent snapshot only, not projected backward |
| `REC_CHANGE` | net recent analyst recommendation upgrades/downgrades | `get_recommendations()` | Diagnostic only until event semantics and coverage are stable |

These signals are not included in the first four candidate composites. They will be archived from activation and may support a separately preregistered future generation.

## Admission thresholds

- **Core candidate:** calculable for at least 80% of the eligible nonfinancial/non-REIT universe and at least 70% of each included sector, with stable formula semantics.
- **Supplemental only:** 60–79.9% overall coverage or one remediable sector-coverage weakness.
- **Reject as sparse:** below 60% coverage.
- Coverage alone is insufficient: fail a factor for inconsistent signs/units, unstable schema, noncomparable sectors, excessive missingness, unavailable denominator history, or redundancy above 0.85 correlation.
- A later performance result cannot override a failed data-admission rule.

## Historical-use warning

No current valuation, estimate, revision, recommendation, sector or `Ticker.info` field may be used as a past observation. Statement-history exploration remains non-point-in-time and cannot approve live deployment.
