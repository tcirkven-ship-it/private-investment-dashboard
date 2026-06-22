# Data-source requirements and assessment protocol

**Version:** 0.1 requirements freeze candidate  
**Verified:** 2026-06-21  
**Decision:** No provider selected; all candidates remain pending Checkpoint 2 pilot  
**Result status:** Requirements and current official facts only, not a definitive vendor comparison

## 1. Non-compensable hard gates

A provider or integrated stack is **prototype-only or rejected** for final conclusions if any of these fails:

1. includes inactive and delisted securities rather than a current-survivor universe;
2. provides actual filing/public-availability dates for every fundamental value used;
3. preserves as-reported/restatement vintages or can reconstruct what was known at each decision date;
4. provides unambiguous cash/special dividends, splits, corporate actions, and delisting treatment;
5. supplies effective-dated permanent identifiers and a defensible historical universe;
6. provides at least 20 reliable overlapping years for pass-capable evidence, or the shortened history is explicitly downgraded under the walk-forward protocol; and
7. has written terms permitting intended research, immutable raw preservation, deterministic reruns, and aggregate reporting.

An attractive aggregate score cannot rescue a failed hard gate.

## 2. Requirements and acceptance matrix

| Area | Required fields/control | Checkpoint 2 acceptance criterion | Failure class |
|---|---|---|---|
| Security master | Permanent security/issuer IDs; ticker, name, exchange, security type, share class, ADR/REIT/LP/ETF/SPAC flags, effective dates; CUSIP/ISIN where licensed | At least 99.9% of eligible security-days join one-to-one; all ticker-reuse/name-change gold cases resolve; no unexplained overlap | Hard gate |
| Universe/history | Active and inactive US listings, listing/delisting dates, venue history, common-stock eligibility | No current-constituent reconstruction; continuous overlap supports protocol evidence tier; universe counts reconcile by date | Hard gate |
| Daily market data | Unadjusted OHLC, official close, volume, shares/market cap, return with/without distributions, calendar; bid/ask or documented spread proxy | At least 99.5% of expected eligible security-days present or reason-coded; zero duplicate keys; no silent price forward-fill | Critical score |
| Delistings | Date, reason/status, last tradable value, delisting return/proceeds/payment when known, merger/acquirer link, missing flag | Every gold delisting represented; terminal treatment attainable; missing returns never zeroed silently; coverage and reason-code sensitivity reported | Hard gate |
| Corporate actions/distributions | Splits/reverse splits, regular/special dividends, return of capital, rights/spin-offs, mergers/exchanges, announcement/ex/record/pay dates and factors | All gold events represented; reconstructed daily total return agrees within 1 bp on at least 99.9% of audited days and 5 bp cumulatively per audited year; no double counting | Hard gate |
| Fundamentals | Annual/quarterly as-reported and standardized facts, currency/units, period dates, fiscal labels, form/accession/source | Every used fact has entity, period, units, fiscal/source provenance; field completeness reported by date/sector; no future backfill | Hard gate |
| Filing availability | SEC acceptance/filing timestamp, provider ingest timestamp if different, timezone, amendment/form type | Every used fact has `available_at`; zero `available_at > signal_cutoff`; after-close filings wait until next eligible session absent proof of earlier use | Hard gate |
| Restatements/vintages | Original values and revisions, version/effective dates, amendment/accession link, restatement flag | Arbitrary historical as-of snapshots reconstructable; later revision cannot appear earlier. Latest-restated-only data is prototype-only | Hard gate |
| Fiscal alignment/staleness | Reporting dates, fiscal mapping, TTM inputs, last publication, missing/stale flags | No duplicated quarter in TTM; balance vs flow semantics tested; maximum age deterministic; every included observation passes | Critical score |
| Historical membership/benchmarks | Effective add/remove dates; total-return series; investable-proxy distributions and expense history | Membership gold sample exact; zero current-constituent leakage; identical contribution/cash/fill convention across ledgers | Hard gate |
| Access/reproducibility | Bulk/API, schema, dictionary, release notes, limits, version/snapshot, retrieval time, query/config, checksums | Immutable raw extracts; rerunnable during license; every input has lineage; corrections create new vintages | Hard gate |
| License/cost/retention | Authorized use/storage/retention, aggregate publication, redistribution, API/bulk rights, quote, renewal, tax/VAT | Written terms allow research, local reproducibility, and aggregate reporting; first-year/renewal costs recorded; post-lapse loss explicit | Hard gate |

The machine-readable version is `research/data_source_requirements.csv`.

## 3. Weighted comparison after hard gates

Score only candidates that pass every hard gate:

| Block | Weight |
|---|---:|
| Point-in-time fundamentals and restatements | 25 |
| Survivorship and delistings | 20 |
| Returns, distributions, and corporate actions | 15 |
| Identifiers and historical universe | 10 |
| Coverage and field completeness | 10 |
| Access and reproducibility | 10 |
| Licensing and total cost | 5 |
| Documentation, support, and correction policy | 5 |

Approval requires at least 80/100 overall and at least 70% of available points in each of the first three blocks. Score definitions and evidence links are frozen before samples are graded.

## 4. Gold-sample audit

Use 250 securities stratified by decade, exchange, size, and security type, including at least:

- 50 delistings, including 25 bankruptcy/distress removals;
- 25 mergers;
- 20 ticker/name/share-class changes;
- 30 special-dividend, split, or spin-off events; and
- 100 10-K/10-Q filings containing amendments or restatements where possible.

Cover the 2001–02, 2008–09, 2020, and recent periods. Compare filing/accession timestamps with SEC EDGAR, events with filings/exchange notices, and prices/returns with an independent source. Archive samples, queries, schemas, hashes, and failures.

Required tests: schema/key/null tests; time-travel/restatement reconstruction; ticker reuse; return identities; membership-as-of; stale-data and fiscal/TTM rules; delisting terminal values; universe-count drift; and license/retention review.

## 5. Candidate categories and official facts

### Research-grade reference stack

**CRSP US Stock + S&P Compustat point-in-time/as-reported data + CRSP/Compustat link history**, with SEC EDGAR timestamp verification and licensed index membership where needed.

CRSP’s official materials describe more than 32,000 active and inactive US securities, survivor-bias-free history, corporate actions, delisting information, and permanent PERMNO/PERMCO identifiers. Its exchange coverage begins in 1925 for NYSE, 1962 for NYSE American, and 1972 for Nasdaq. S&P’s official product page describes more than 3,000 standardized fields, financial history from 1950, point-in-time snapshots from 1987, and as-reported history from 1993.

This is a **reference candidate**, not an approval. Entitlements, exact Compustat tables/snapshots, delivery, ingest timing, corrections, price, WRDS access, and license terms require written confirmation and a field-level pilot.

Official sources:

- https://www.crsp.org/research/crsp-us-stock-databases/
- https://www.crsp.org/crsp_pdf/crsp-us-stock-indexes-databases-calculations-index-methodologies-guide-flat-file-format-2-0/
- https://www.crsp.org/wp-content/uploads/guides/CRSP_Compustat_Merged_Database_Guide.pdf
- https://www.spglobal.com/market-intelligence/en/solutions/products/fundamental-data

### Realistic lower-cost candidate stack

**Norgate Platinum/Diamond market and constituent data + a separately audited point-in-time fundamental source**, with Nasdaq Data Link Sharadar SF1/SEP or a purpose-built EDGAR pipeline as candidates.

Norgate’s official pages list US Platinum at USD 630/year, with history/delistings/constituents from 1990, and Diamond at USD 787.50/year, with longer market history. Its own FAQ says fundamental data are latest-report only; historical constituents are queried through supported plugins rather than exported as ordinary constituent lists, and the proprietary local store becomes inaccessible when the subscription lapses. Norgate alone therefore fails the historical-fundamental gate.

Nasdaq Data Link materials state that Sharadar SEP includes active and delisted US stocks from 1998 and that the Core US Equities bundle includes SF1, TICKERS, DAILY, SP500, ACTIONS, EVENTS, and SEP. The accessible official documentation reviewed did not establish complete historical-vintage/restatement reconstruction or exact availability timestamps. Sharadar remains a pilot candidate, not approved definitive data.

Official sources:

- https://norgatedata.com/stockmarketpackages.php
- https://norgatedata.com/index.php/pricing/
- https://norgatedata.com/data-package-faq.php
- https://help.data.nasdaq.com/article/533-what-are-the-column-definitions-for-the-sharadar-data-feeds
- https://docs.data.nasdaq.com/docs/data-organization

### Free/prototype category

SEC EDGAR is the authoritative free source for filing timestamps and raw filing/XBRL documents. Its official APIs need no key, update throughout the day, and provide nightly bulk files; broad XBRL coverage follows the 2009 mandate. EDGAR does not provide market prices, delisting returns, normalized total returns, historical benchmark membership, or a ready-made security master. Entity/taxonomy normalization is a substantial research pipeline.

Nasdaq states that the free WIKI price feed ended in 2018, is unreliable, and has no free replacement. A free-only integrated stack therefore remains prototype-only unless an independently validated market, event, and security-master layer passes every hard gate.

Official sources:

- https://www.sec.gov/edgar/sec-api-documentation
- https://help.data.nasdaq.com/article/506-why-does-wiki-prices-only-go-up-to-march-2018

## 6. Known uncertainties and contradictions

- CRSP notes that delisting returns can be missing when post-delisting information is insufficient. Missing-return coverage and sensitivity remain required even for research-grade data.
- Public S&P material proves that point-in-time products exist, not that a specific subscription includes the exact snapshots, timestamps, and corrections this project needs.
- “Suitable for backtesting” on a vendor page may refer to market data, not point-in-time fundamental research.
- Sharadar’s field breadth appears promising, but restatement/vintage and availability semantics remain unproven against this protocol.
- Combining an already total-return-adjusted price with a separately posted dividend can double count distributions.
- Retention restrictions can make a reproducible method irreproducible after a subscription ends.

## 7. Checkpoint 2 action

Send a common request-for-information and gold-sample specification to CRSP/S&P/WRDS, Nasdaq/Sharadar, and Norgate. Obtain samples, dictionaries, current quotes, and written license/retention answers. Run the identical audit on the research-grade and lower-cost stacks. No large-scale factor optimization begins until one integrated stack passes the hard gates.
