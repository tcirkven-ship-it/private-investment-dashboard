# Data requirements and vendor decision matrix

**Audit date:** 2026-06-21  
**Decision rule:** Marketing feature lists are screening evidence only. A provider is approved only after contractual-use review and sample time-travel/terminal-event tests.

## Vendor-neutral minimum specification

### Indispensable

| Data block | Required fields and behavior | Acceptance test |
|---|---|---|
| Stable identity | Permanent security and issuer IDs; share class; effective-dated ticker/name mapping | Reused tickers, share-class changes and mergers join without ambiguity |
| Listing/universe history | Listing/delisting dates, security type, exchange/status history, active/inactive flags | Reconstruct every eligible security on arbitrary historical dates without current-survivor filtering |
| Raw daily market data | Unadjusted OHLC, volume, trading calendar and status | No silent forward fills; missing/suspended days reason-coded |
| Return inputs | Split factors, regular/special dividends, return of capital, spin-offs and other distributions | Independently reconstruct total returns without double counting |
| Terminal events | Mergers/acquisitions, bankruptcies, liquidations, delistings, last trade, proceeds and delisting return when available | Every portfolio exit has an attainable terminal treatment; missing outcomes explicitly flagged and sensitized |
| Historical eligibility | Point-in-time price, volume, exchange, security type, shares and market cap | Universe rule reproducible using only information then available |
| Fundamental facts | Quarterly/annual as-reported statements, units/currency, period dates, form and accession/source | Every ratio maps to auditable raw facts and fiscal semantics |
| Availability time | Filing/acceptance/publication timestamp with timezone; amendment timestamp | No fact appears before `available_at`; after-close rule deterministic |
| Vintages/restatements | Original value, revisions, amendment/restatement links and effective dates | Arbitrary as-of snapshots reconstruct what was known then; later restatement cannot leak backward |
| Shares/market value | Point-in-time basic/diluted shares and security-level market capitalization | Denominators align to the correct listing/share class/date |
| Classification history | Effective-dated sector and industry | No current classifications projected backward |
| Reproducibility | API/bulk access, schema/data dictionary, snapshot/version, correction history, checksums | Raw extracts can be frozen and deterministic reruns performed within licensed rights |
| License | Written permission for personal research, local retention, derived analytics and aggregate reporting | Retention/use after subscription termination understood before purchase |

### Strongly preferred

- Bid/ask quotes or a validated historical spread proxy.
- Provider ingestion timestamps in addition to SEC acceptance times.
- Original filings/XBRL tags alongside standardized fields.
- Amendment and restatement reason/type metadata.
- Historical index membership with effective announcement/add/remove dates.
- Point-in-time free float, shares and corporate hierarchy.
- SIC/NAICS/GICS-like classification history with documented methodology.
- Exchange condition codes, halts and official-close indicators.
- Delisting-payment updates when proceeds arrive after the last trading date.
- Bulk snapshots and correction vintages rather than API-only mutable responses.
- At least 15–20 overlapping years spanning multiple regimes.

### Optional

- Intraday bars/quotes for execution research.
- Analyst-estimate/revision vintages.
- Earnings-announcement timestamps and call/event calendars.
- Short interest, institutional ownership and insider transactions.
- Fundamentals normalized specifically for banks, insurers and REITs.
- International listings, FX history and tax-lot/account reporting.
- News/sentiment and alternative data.

Optional data cannot compensate for a missing historical universe, terminal outcomes, or filing-vintage control.

## Mandatory vendor pilot

Before accepting any vendor, run a fixed gold-set audit containing:

1. at least twenty delistings across bankruptcy, cash merger, stock merger, going-private and ordinary exchange removal;
2. ticker reuse and name/share-class changes;
3. large splits, reverse splits, special dividends, spin-offs and return-of-capital events;
4. original and amended 10-Q/10-K filings with known restatements;
5. arbitrary historical dates where the active universe is known independently;
6. statement values queried before filing, immediately after filing, and after amendment;
7. raw-to-total-return reconciliation; and
8. written confirmation of local retention and derived-output rights.

A failed time-travel test makes a source prototype-only even if its current ratios look accurate.

## Source-approach matrix

_Current official-source findings and prices are dated 2026-06-21. “Potentially definitive” still requires the pilot above._

| Approach | PIT/as-reported fundamentals | Historical universe/delistings | Actions/access/depth | Cost and licensing | Suitability |
|---|---|---|---|---|---|
| **A. Institutional reference: CRSP US Stock + S&P Compustat PIT/as-reported + CCM/WRDS; SEC verification** | S&P advertises standardized history, PIT snapshots from 1987 and as-reported history from 1993; exact entitlement/timestamps must be confirmed | CRSP documents active/inactive securities, permanent IDs, actions and delisting information; missing delisting returns still require treatment | Research/bulk delivery and long history; institutional schema/licensing complexity | Public price not posted; written institutional quote, retention and publication rights required | **Potentially supports the original standard** after field/license pilot. Best reference architecture. |
| **B. Serious individual: Sharadar Core US Equities (SF1/SEP/TICKERS/ACTIONS)** | Official material describes AR dimensions indexed to filing date and MR restated dimensions, with history roughly from 1997. Amendment replay and immutable-vintage behavior still require a gold-set test | SEP includes active/delisted US stocks from 1998; public docs do not establish CRSP-equivalent terminal delisting returns/post-delisting distributions | REST/table API and downloads; integrated statements, prices, identifiers and actions | Current self-checkout price was not publicly verifiable in the audit; obtain a current quote and written retention/derived-output terms | **Best serious-individual candidate; conditionally definitive at most** until vintage, terminal-event, correction and license tests pass. |
| **C. Lower-cost mixed: Norgate Platinum/Diamond market/constituent layer + SEC EDGAR as-filed pipeline** | Norgate fundamentals are latest-report only and fail PIT alone; SEC can supply authoritative filing timestamps/raw filings but requires substantial normalization | Norgate advertises delisted stocks and historical constituents from 1990; terminal-value semantics and plugin/export constraints need testing | Windows local database/plugins plus SEC API/bulk; strong price/constituent history but two-source identity integration | Project review recorded US Platinum **$630/year** and Diamond **$787.50/year**; confirm the current calculator/checkout. Proprietary store access ends with subscription | **Potentially credible reduced-scope research**; not equivalent to the original standard unless the integrated vintage, terminal-event and retention pilot passes. |
| **D. Lower-cost/API mixed: Massive (Polygon) market/reference/actions + SEC EDGAR as-filed pipeline** | Massive financial statements are available on selected paid tiers, but current endpoint docs expose filing dates without clearly documented accession-vintage/restatement time travel. SEC supplies authoritative filing acceptance and raw facts from the modern filing era | Massive supports historical `date`, inactive/delisted tickers and `delisted_utc`; it does not supply historical OEF membership or prove CRSP-like delisting returns/terminal distributions | REST/flat files, adjusted/unadjusted aggregates, splits/dividends and ticker changes. Ticker Events currently documents ticker changes; full merger/acquisition/spin-off event coverage is not established. Advertised history: 2/5/10/all-history tiers | Stocks Basic $0, Starter $29/mo, Developer $79/mo, Advanced $199/mo; docs also show a $29 Financials & Ratios expansion. Terms/retention require written confirmation | **Free tier: prototype only. Paid + SEC: promising reduced-scope candidate**, not definitive until vintage, identifiers, terminal outcomes and license pass. |
| **E. Free prototype: yfinance + SEC EDGAR + FRED + dated fund/symbol snapshots** | SEC filings/timestamps are authoritative but require a large normalization/vintage pipeline; yfinance statements are not accepted PIT evidence | No integrated historical security master, complete delisted universe, historical constituents or terminal returns | Convenient prices/benchmarks and forward snapshots; mutable unofficial market-data access | $0 monetary cost; high engineering cost and uncertain market-data retention/terms | **Forward paper/prototype only. Cannot support the original historical conclusion.** |

Institutional sources:

- [CRSP US Stock Databases](https://www.crsp.org/research/crsp-us-stock-databases/)
- [CRSP/Compustat Merged Database Guide](https://www.crsp.org/wp-content/uploads/guides/CRSP_Compustat_Merged_Database_Guide.pdf)
- [S&P Global fundamental data](https://www.spglobal.com/market-intelligence/en/solutions/products/fundamental-data)

Individual/mixed sources:

- [Norgate stock packages](https://norgatedata.com/stockmarketpackages.php)
- [Norgate pricing](https://norgatedata.com/index.php/pricing/)
- [Norgate package FAQ](https://norgatedata.com/data-package-faq.php)
- [Nasdaq Data Link/Sharadar field definitions](https://help.data.nasdaq.com/article/533-what-are-the-column-definitions-for-the-sharadar-data-feeds)
- [Sharadar official data fact sheet](https://resources.quandl.com/a/res-hub/Sharadar_Datasheet_final.pdf)
- [Nasdaq Data Link delisted-stock coverage](https://help.data.nasdaq.com/article/508-do-you-cover-delisted-stocks)
- [SEC EDGAR API documentation](https://www.sec.gov/edgar/sec-api-documentation)
- [SEC Financial Statement Data Sets](https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets)

## What Polygon/Massive would and would not change

Massive's historical ticker endpoint supports an as-of `date`, active/inactive filtering, stable identifiers such as CIK/FIGI, and a delisted date. Its documentation states that delisted tickers remain in the data, and its split/dividend/aggregate endpoints are materially stronger than yfinance for reconstructing a broad historical listing universe. However, the reviewed Ticker Events documentation currently covers ticker changes rather than complete merger, acquisition and spin-off life cycles, and a delisted flag/date is not the same as a CRSP-style terminal return or proceeds record.

That can directly improve the largest **price-universe** defect if the strategy is redefined around a reproducible broad US common-stock universe. It does not by itself provide historical OEF membership. More importantly, “point-in-time balance sheet” may mean a balance sheet measured at a period end; it does not automatically prove preservation of every as-filed statement vintage, amendment/restatement history, or the exact public-availability time required by this protocol. Those semantics must be tested.

The current free Stocks Basic plan advertises only two years of history, which cannot support the 2010–2026 test. Paid plans advertise five, ten and all available history at progressively higher tiers. The reviewed individual market-data terms also raise restrictions around strategy/non-display/derived use and deletion/retention on termination; written authorization is a hard gate. Therefore free Massive/Polygon can support an API/schema pilot and prospective archiving, not the original long historical mandate, and paid use is not approved until license scope is confirmed.

Official references:

- [Massive Stocks pricing](https://massive.com/pricing?product=stocks)
- [Historical/all tickers endpoint](https://massive.com/docs/rest/stocks/tickers)
- [Delisted-ticker policy](https://massive.com/knowledge-base/article/what-does-massive-do-with-delisted-tickers)
- [Stocks REST overview](https://massive.com/docs/rest/stocks)
- [Stocks flat-file overview](https://massive.com/docs/flat-files/stocks/overview)
- [Massive market-data terms](https://massive.com/terms/market_data_terms.pdf)

## Decision rule by evidence tier

- A stack may support **definitive original-mandate conclusions** only if it passes every indispensable field, legal-use, time-travel and terminal-outcome test.
- A stack may support **reduced-scope credible conclusions** when its limitations are eliminated by narrowing the universe, period or factors before preregistration.
- A free or latest-restated/current-survivor stack supports **prototype engineering and forward paper evidence only**.
