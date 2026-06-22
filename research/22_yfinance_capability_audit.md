# Phase 1B yfinance capability audit

**Experiment:** EXP-0012  
**Snapshot:** `data/raw/yfinance_phase1b/2026-06-21T204918Z/`  
**Retrieval completed:** 2026-06-21 21:01:40 UTC  
**Installed package:** yfinance 1.4.0  
**Data source:** Yahoo Finance accessed exclusively through yfinance  
**Classification:** Current capability/feasibility evidence, not point-in-time historical fundamentals

## Audit design

The sample was created without an external constituent list. `yf.screen(EquityQuery)` queried each of Yahoo's eleven equity sectors separately, restricted to region `us`, Nasdaq Global Select/NYSE/NYSE American exchange codes, current price of at least USD 5, market capitalization of at least USD 1 billion and three-month average volume of at least 200,000 shares. Each sector was sorted by current market capitalization; the first ten names produced a 110-stock sample.

This is a deliberately balanced capability sample, not the final investable universe and not a historical universe. Yahoo's `region=us` includes foreign issuers listed in the United States: only 84 of 110 sample companies reported `country=United States`.

Every raw screener response, ticker response, error, CSV, retrieval timestamp, package version and checksum was archived. The raw manifest SHA-256 is `f76313258c9bd11c768833bba5ad5753598f442dc540e64660d3fffc72cf2f91`.

The immutable inventory contains 2,324 raw files totaling 142,856,913 bytes. All 110 ticker manifests were present and all 2,200 registered endpoint-file hashes matched. Validation status: PASS.

## Methods actually called

- `yf.screen(EquityQuery)`;
- `Ticker.get_info()` and `Ticker.fast_info`;
- `Ticker.history(period="max", interval="1d", auto_adjust=False, actions=True, repair=False, keepna=True)`;
- `Ticker.get_income_stmt(freq="yearly"|"quarterly"|"trailing")`;
- `Ticker.get_balance_sheet(freq="yearly"|"quarterly")`;
- `Ticker.get_cash_flow(freq="yearly"|"quarterly"|"trailing")`;
- `Ticker.get_shares_full(start="2000-01-01")`;
- `Ticker.get_earnings_history()`;
- `Ticker.get_eps_revisions()` and `Ticker.get_eps_trend()`;
- `Ticker.get_revenue_estimate()` and `Ticker.get_earnings_estimate()`; and
- `Ticker.get_recommendations()` and `Ticker.get_recommendations_summary()`.

## High-level result

- Sample: 110 stocks, exactly ten from each Yahoo sector.
- Transport/parsing endpoint exceptions: **0**.
- Annual income, balance and cash-flow frames nonempty: **110/110**.
- Trailing income and cash-flow frames nonempty: **110/110**.
- Quarterly income nonempty: **105/110**; quarterly cash flow: **103/110**; quarterly balance: **110/110**.
- Full share-count series nonempty: **110/110**.
- Current EPS revisions, EPS trend, revenue estimates, earnings estimates and recommendations nonempty: **110/110**.
- Earnings history nonempty: **105/110**.
- Maximum daily history nonempty: **110/110**.

Successful requests do not imply uniform data. Missing cells and row schemas vary substantially.

## Statement coverage

| Endpoint | Tickers nonempty | Median periods/columns | Cell missingness | Union rows | Rows common to all | Unique row schemas |
|---|---:|---:|---:|---:|---:|---:|
| Annual income | 110 (100%) | 5 | 19.15% | 79 | 19 | 108 |
| Quarterly income | 105 (95.45%) | 6 | 20.37% | 79 | 0 | 104 |
| Trailing income | 110 (100%) | 1 | 2.49% | 78 | 19 | 107 |
| Annual balance sheet | 110 (100%) | 5 | 21.27% | 139 | 14 | 108 |
| Quarterly balance sheet | 110 (100%) | 6 | 30.09% | 137 | 16 | 108 |
| Annual cash flow | 110 (100%) | 5 | 21.07% | 104 | 8 | 108 |
| Quarterly cash flow | 103 (93.64%) | 6 | 28.13% | 104 | 0 | 102 |
| Trailing cash flow | 110 (100%) | 1 | 4.12% | 104 | 9 | 108 |

Annual income history ranged from 3 to 8 periods, with median 5. Quarterly income ranged from 0 to 7 periods, with median 6. Period ends in the snapshot ranged from 2021-06-30 to 2026-03-31 annually and from 2024-09-30 to 2026-05-31 quarterly, reflecting different fiscal calendars.

The five tickers without quarterly income/earnings-history frames were BTI, UL, BHP, RIO and NGG; BUD and HSBC also lacked quarterly cash flow. These are foreign issuers. The proposed primary US nonfinancial subset had much stronger input coverage.

Schema variability is the central engineering issue: 108 distinct annual-income, balance and cash-flow row sets appeared among 110 tickers. Raw row names therefore require an alias/version layer and explicit missingness; positional or fixed-schema assumptions are unsafe.

## Metadata, currencies and valuation

Current sector, industry, country, exchange, quote type, trading currency, financial currency, market capitalization, enterprise value and shares outstanding were present for all 110 names.

| Current valuation field | Coverage |
|---|---:|
| Market capitalization | 110/110 |
| Enterprise value | 110/110 |
| Forward P/E | 110/110 |
| Price/book | 110/110 |
| Enterprise value/revenue | 110/110 |
| Trailing P/E | 108/110 |
| Enterprise value/EBITDA | 103/110 |

Financial currencies were USD for 97 names; the remaining 13 used BRL, CAD, CNY, DKK, EUR, GBP, JPY or TWD. The primary fundamental strategy therefore requires current country and USD financial/trading currency rather than relying on `region=us` alone.

These metadata and valuation values are current observations. They cannot be joined to past statement dates as if historically known.

## Shares, estimates and analyst data

`get_shares_full()` returned data for all tickers, but the number of observations ranged from 7 to 1,911 (median 649), showing heterogeneous update frequency and history. `sharesOutstanding` was also present in current info for all names. Share-dilution research should prefer comparable annual `OrdinarySharesNumber` periods and treat the full share series as a prospective reconciliation source.

Current estimate/revision tables had high apparent coverage:

| Endpoint | Nonempty coverage | Typical rows |
|---|---:|---:|
| EPS revisions | 110/110 | 4 |
| EPS trend | 110/110 | 4 |
| Revenue estimate | 110/110 | 4 |
| Earnings estimate | 110/110 | 4 |
| Recommendations | 110/110 | approximately 4 |
| Earnings history | 105/110 | approximately 4 |

These are current/prospective signals only. No historical retrieval snapshots exist before Phase 1B.

## Prices, dividends and splits

Maximum daily histories were nonempty for all tickers, with a median of 10,546 rows. Raw and adjusted prices, volume, dividends and stock splits were archived separately.

- 101 names had at least one nonzero dividend event.
- 92 had at least one split event.
- SPCX, APP and SPOT had neither in their available history; an empty action table is not automatically a retrieval failure.

Yfinance does not provide a complete historical universe, delisting-return table or full complex-action/terminal-proceeds ledger. Long price tests using this current sample remain survivor-biased.

## Raw factor-input feasibility

After restricting the audit to 66 current US, nonfinancial, non-Real-Estate names, the raw inputs for most proposed quality, value and growth formulas were present in at least 98.48% of names and at least 87.5% of every included sector. Shareholder-yield inputs were present for only 26/66 (39.39%), with a worst-sector coverage of 14.29%; shareholder yield is rejected for the primary composite.

This is **input presence**, not final factor validity. It does not test positive denominators, aligned periods, sign conventions, economic comparability, factor correlation or score stability. Those checks remain gates before calculation code or performance testing.

## Capability decision

The audit supports the following narrow conclusion:

> A practical current/prospective yfinance price-plus-fundamental research process appears buildable for a restricted US nonfinancial universe. Statement and current analyst coverage are broad enough to proceed to deterministic factor calculation and semantic QA, but the histories are short, heterogeneous and potentially restated.

It does not support a definitive historical fundamental backtest. The next checkpoint may implement factors admitted in `research/23_yfinance_factor_dictionary.md`, but must preserve the evidence tiers and common-support comparisons in `research/25_yfinance_strategy_specification.md`.

## Machine-readable outputs

- `outputs/experiment_runs/EXP-0012/yfinance_capability_summary.json`
- `outputs/experiment_runs/EXP-0012/yfinance_capability_ticker_coverage.csv`
- `outputs/experiment_runs/EXP-0012/yfinance_endpoint_coverage_matrix.csv`
- `outputs/experiment_runs/EXP-0012/yfinance_capability_endpoint_coverage_by_ticker.csv`
- `outputs/experiment_runs/EXP-0012/yfinance_statement_field_coverage_matrix.csv`
- `outputs/experiment_runs/EXP-0012/yfinance_factor_input_coverage_matrix.csv`
- `outputs/experiment_runs/EXP-0012/yfinance_factor_sector_coverage_matrix.csv`
- `outputs/experiment_runs/EXP-0012/yfinance_snapshot_validation.json`
