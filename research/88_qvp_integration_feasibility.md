# QVP integration — historical feasibility audit

**Evidence label:** Exploratory survivor-biased historical Price research

## Factor historical availability

| Factor | Category | Data source | Historical available? | Limitation |
|---|---|---|---|---|
| ROA (Net Income / Total Assets) | Q | Annual/quarterly income + balance | YES (approximate PIT) | Requires 2-3mo lag for filing. Uses latest fiscal year data. |
| GPA (Gross Profit / Total Assets) | Q | Annual/quarterly income + balance | YES (approximate PIT) | Requires 2-3mo lag. Gross Profit may be absent for financial/service firms. |
| FCF MARGIN (FCF / Revenue) | Q | Annual/quarterly cash flow + income | YES (approximate PIT) | Requires 2-3mo lag. FCF can be negative. |
| DEBT/ASSETS (inverse) | Q | Annual/quarterly balance sheet | YES (approximate PIT) | Requires 2-3mo lag. Debt may omit off-balance-sheet items. |
| FCF YIELD (FCF / EV) | V | FCF from statements; EV = MktCap + Debt - Cash | **PROXY ONLY** | EV needs historical market cap (= price × shares). Shares history unavailable from yfinance. Can use current shares × historical price as PROXY. |
| SALES/EV (Revenue / EV) | V | Revenue from statements; EV as above | **PROXY ONLY** | Same EV limitation. |
| BOOK/MARKET (Book / MktCap) | V | Book from statements; MktCap from price | **PROXY ONLY** | Same market-cap limitation. Approximate with current shares × historical price. |

## Key limitation: Enterprise Value

Yfinance does not provide historical shares outstanding. Enterprise Value
requires: MktCap (price × shares) + Debt − Cash. Without PIT shares, any
historical EV is an approximation that ignores share buybacks, issuance,
and dilution. This makes historical Value factors (FCF_YIELD, SALES_EV,
BOOK_MARKET) approximate non-PIT proxies only.

## Key limitation: Filing/publication dates

Yfinance statement snapshots do not come with SEC filing dates. The
conservative approach is to use the latest fiscal-year data with a
3-month publication lag (e.g., Dec 2023 annual data becomes usable on
April 1, 2024). This is an approximation that may slightly overstate
information availability.

## Recommendation

Quality factors can be approximately computed historically from annual/
quarterly statements with conservative lag. Value factors are approximate
non-PIT proxies at best. A full historical QVP test with credible PIT
Value requires a paid data source (Sharadar or CRSP/Compustat).

For this task: Quality factors will be computed from trailing annual
data with 3-month publication lag. Value factors will use the same
plus current shares × historical price as MktCap proxy. All results
are labeled as survivor-biased and non-PIT.