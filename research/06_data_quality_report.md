# Data-quality report — zero-cost prototype stack

**Version:** 0.3 final best-effort report  
**As of:** 2026-06-21  
**Data decision:** Approved for prototype infrastructure and benchmark diagnostics only; rejected for definitive strategy conclusions in its current form

## Executive conclusion

The user chose a zero-cost constraint and later authorized a best-effort completion. The free stack successfully validated ingestion, contribution accounting, benchmark mechanics, price-factor experiments and forward-paper infrastructure. It cannot support a pass or conditional-pass investment conclusion because it fails historical-universe, delisting-return, permanent-identifier and point-in-time fundamental gates. Phase One therefore ends with a **FAIL** decision.

No free-data result may be presented as institutional-quality evidence or used to relax the frozen research standard.

## Sources selected

| Layer | Zero-cost source | Status | Valid use | Critical limitation |
|---|---|---|---|---|
| Fundamentals | SEC EDGAR Financial Statement Data Sets / Company Facts | Design approved; ingestion pending | As-filed facts and filing/accession dates from 2009 onward | No market data, listing history, delisting returns, or security master; taxonomy normalization required |
| Current universe seed | Official iShares OEF holdings workbook | Ingested: 2026-06-18 snapshot | Bounded 100-issuer liquid mega-cap prototype | Current holdings projected backward create survivorship and membership bias |
| Nasdaq-100 benchmark | FRED `NASDAQXNDX` | Ingested and checksum-validated | Theoretical total-return reference | Copyrighted index; not investable proxy |
| Nasdaq Composite | FRED `NASDAQXCMP` | Ingested and checksum-validated | Additional total-return reference | Copyrighted index; not investable proxy |
| S&P 500 diagnostic | FRED `SP500` | Ingested and checksum-validated | Price-index reconciliation only | Only ten years and explicitly excludes dividends; fails primary benchmark rule |
| Individual/ETF EOD prices | Yahoo Finance via yfinance 1.4.0 | SPY/QQQ ingested and validated | Prototype OHLCV, adjusted close, dividends, splits, ETF benchmark ledgers, and forward tracking | Unofficial client/personal-use context; no complete historical universe, inactive/delisted coverage, terminal returns, permanent IDs, or point-in-time fundamentals |
| Secondary price source | Tiingo free plan | Deferred fallback; free token required | Independent prototype price/action comparison if needed | Free usage limits; historical inactive/delisted coverage and terminal returns unproven |
| Price fallback | Stooq free files | Not currently automatable | Browser/manual prototype fallback | Direct automation blocked; adjustment, event, identifier, delisting, and license semantics insufficiently documented |
| Factor diagnostics | Kenneth French Data Library | Approved for later diagnostic use | Factor-return reconciliation and regression sanity checks | No individual-security data |

## Ingested FRED snapshot

Raw files are immutable under `data/raw/fred/2026-06-21/`; full provenance is in `data/metadata/free_sources_manifest.json`.

| Series | Rows | First nonmissing | Last nonmissing | SHA-256 status | Interpretation |
|---|---:|---|---|---|---|
| NASDAQXNDX | 7,121 | 1999-03-04 | 2026-06-18 | Matches manifest | Nasdaq-100 total-return reference |
| NASDAQXCMP | 5,931 | 2003-09-25 | 2026-06-18 | Matches manifest | Nasdaq Composite total-return reference |
| SP500 | 2,609 | 2016-06-20 | 2026-06-18 | Matches manifest | Price-only diagnostic; not valid total-return benchmark |

Automated validation checks headers, checksums, row shape, date parsing, chronological order, duplicate dates, missing-value representation, and numeric values. Results are stored under `outputs/experiment_runs/EXP-0004/`.

## Ingested yfinance snapshot

The immutable raw snapshot is under `data/raw/yfinance/2026-06-21/`. It was retrieved with yfinance 1.4.0 using daily interval, maximum period, `auto_adjust=False`, `actions=True`, `repair=False`, and separate metadata/checksums.

| Ticker | Rows | First date | Last date | Nonzero action rows | Validation |
|---|---:|---|---|---:|---|
| SPY | 8,404 | 1993-01-29 | 2026-06-18 | 135 | PASS |
| QQQ | 6,862 | 1999-03-10 | 2026-06-18 | 89 | PASS |

EXP-0005 passed file checks and recent benchmark reconciliation. From 2021 onward, QQQ adjusted-return correlation with FRED Nasdaq-100 total return was 0.999461 with 0.774% annualized tracking error; SPY unadjusted-close return correlation with FRED S&P 500 price return was 0.997763 with 1.140% annualized tracking error. These are reconciliation results, not evidence of strategy performance or complete historical-data quality.

## Ingested OEF universe and stock histories

The official OEF fund-data workbook is preserved at `data/raw/universe/2026-06-21/OEF_fund_data.xml`. EXP-0007 extracted 101 US USD equity rows and retained 100 issuers after removing the lower-weight duplicate Alphabet share class. EXP-0008 acquired and validated all 100 maximum-history yfinance extracts.

At the 2010 analysis start, 91 names had 252 prior observations; coverage was 97 names by 2015 and 100 by 2026. This is adequate for the frozen 30-name engineering test but does not cure current-membership bias.

## Point-in-time assessment

SEC states that its Financial Statement Data Sets present information without change from the “as filed” reports and cover XBRL filings from 2009 onward. Company Facts and submissions APIs expose filing/accession history without an API key, but programmatic access requires a declared User-Agent and rate discipline. Later filings can contain comparative values that differ from earlier filings, so the pipeline must retain accession-specific facts and query by filing availability rather than choose a single latest value.

This is better than a latest-restated commercial web scrape, but it does not solve security identity, exchange history, or delisting outcomes.

## Survivorship and delisting assessment

The proposed free universe begins with currently listed Nasdaq Trader symbols, so any historical backtest on that seed would be survivorship-biased. SEC bulk filings include inactive filers but identify issuers by CIK, not a complete effective-dated security master, and do not provide terminal security returns. Therefore:

- historical alpha estimates are engineering demonstrations only;
- results cannot satisfy the data-integrity gate;
- current constituents may be used only for forward testing or explicitly biased smoke tests; and
- no final holdout is opened.

## Benchmark assessment

FRED provides free daily Nasdaq-100 and Nasdaq Composite total-return index levels with useful long histories. These support theoretical benchmark accounting. The free FRED S&P 500 series is a price index, excludes dividends, and contains only ten years under the current S&P/FRED agreement. It cannot be compared against a dividend-inclusive stock strategy.

The yfinance SPY and QQQ histories now supply distribution-aware investable proxies for prototype benchmark ledgers. Raw close, adjusted close, dividends, and splits are retained separately so the accounting engine can be tested without silently double-counting distributions. The theoretical FRED indexes remain independent reconciliation references.

## Validity ceiling and permitted experiments

Permitted now:

- deterministic contribution, TWR, XIRR, dividend, split, cost, and cash-ledger tests;
- FRED benchmark ingestion and theoretical Nasdaq benchmark ledgers;
- yfinance SPY/QQQ investable benchmark ledgers and bounded current-symbol price/action pulls;
- SEC as-of extraction and taxonomy mapping tests;
- current-universe factor calculation smoke tests with a prominent survivorship warning;
- forward-only paper snapshots; and
- data coverage/missingness reports.

Not permitted as evidence of strategy success:

- full historical stock-selection comparisons using a current-symbol universe;
- any result that silently treats missing delisting returns as zero;
- comparison with the dividend-excluding FRED S&P 500 series;
- final-holdout evaluation; or
- pass/conditional-pass classification.

## Post-Phase-One technical actions

1. Keep C03-M paper-only; do not automate or trade it as an approved strategy.
2. If forward research continues, add compliant SEC ingestion using an owner-provided contact identity and retain accession-specific facts.
3. Archive effective-dated current-universe snapshots and forward delisting/corporate-action outcomes.
4. Create a new preregistration and unused holdout only after materially better data exist.

## Sources verified 2026-06-21

- SEC EDGAR APIs and bulk files: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC Financial Statement Data Sets: https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets
- Nasdaq Trader symbol directory: https://nasdaqtrader.com/trader.aspx?id=symbollookup
- FRED Nasdaq-100 Total Return: https://fred.stlouisfed.org/series/NASDAQXNDX
- FRED Nasdaq Composite Total Return: https://fred.stlouisfed.org/series/NASDAQXCMP
- FRED S&P 500 price index: https://fred.stlouisfed.org/series/SP500
- yfinance documentation: https://ranaroussi.github.io/yfinance/index.html
- yfinance download API: https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html
- Yahoo Developer API terms: https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html
- Tiingo free EOD information: https://www.tiingo.com/blog/best-stock-price-api/
- Kenneth French Data Library momentum details: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor_daily.html
