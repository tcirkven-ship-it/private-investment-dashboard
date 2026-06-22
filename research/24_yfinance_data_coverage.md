# Phase 1B yfinance field and factor coverage decision

**Source snapshot:** `data/raw/yfinance_phase1b/2026-06-21T204918Z/`  
**Sample:** 110 current stocks; admission subset: 66 current US, nonfinancial, non-Real-Estate names  
**Measurement:** Nonmissing raw input presence only unless stated otherwise

## Coverage thresholds

- Core candidate: at least 80% of the eligible subset and 70% of every included sector.
- Supplemental only: 60–79.9% overall or one remediable sector weakness.
- Reject as sparse: below 60%.
- A coverage pass does not override semantic, denominator, currency, alignment, outlier or redundancy failures.

## Endpoint field-coverage matrix

| Data family | Coverage result | Principal limitation |
|---|---|---|
| Annual statements | 100% nonempty; median 5 periods | 19–21% cell missingness; nearly every ticker has a different row schema |
| Quarterly income | 95.45% nonempty; median 6 periods | Foreign issuers account for empty frames; 20.37% cell missingness |
| Quarterly balance | 100% nonempty; median 6 periods | 30.09% cell missingness and heterogeneous rows |
| Quarterly cash flow | 93.64% nonempty; median 6 periods | No common row across all 110; 28.13% missingness |
| Trailing income/cash flow | 100% nonempty, one column | High coverage but still 107–108 unique schemas |
| Full share history | 100% nonempty | 7–1,911 observations; irregular update frequency |
| Current valuation metadata | Core denominators 93.64–100% | Current only, not historical |
| Current estimates/revisions | 100% for EPS/revenue tables | Current/prospective only |
| Earnings-history surprises | 95.45% overall; 100% in primary subset | Short recent event table, not a historical archive |
| Prices/actions | 100% prices; 97.27% nonempty actions | Empty actions may be legitimate; no complete delisting/terminal-event data |

Full row-level matrices are stored under `outputs/experiment_runs/EXP-0012/`.

## Proposed fundamental coverage decisions

| Factor | Primary-subset input coverage | Worst included-sector coverage | Coverage decision | Additional gate |
|---|---:|---:|---|---|
| ROA | 100% | 100% | Core candidate | Align average assets and TTM net income |
| Approximate ROIC | 100% | 100% | Diagnostic initially | Approximate capital definition; exclude nonpositive capital |
| Gross profitability/assets | 98.48% | 87.50% | Core candidate | Gross-profit comparability by industry |
| Operating margin | 100% | 100% | Core candidate | Positive comparable revenue |
| FCF margin | 100% | 100% | Core candidate | Verify FCF construction/sign |
| Cash conversion | 100% | 100% | Diagnostic initially | Positive net-income rule and extreme ratios |
| Debt/assets | 100% | 100% | Core candidate | Sector-neutral, lower is better |
| Net debt/EBITDA | 100% | 100% | Diagnostic initially | Nonpositive EBITDA and cash-rich firms |
| Interest coverage | 100% | 100% | Diagnostic initially | Zero/missing interest and operating leases |
| Share dilution | 100% | 100% | Core candidate | Prefer comparable annual shares; reconcile actions |
| Earnings yield | 100% | 100% | Diagnostic initially | Current market cap only; overlaps value factors |
| FCF yield | 100% | 100% | Core candidate | Current/prospective only |
| EBIT/EV | 100% | 100% | Core candidate | Positive EV; current/prospective only |
| Sales/EV | 100% | 100% | Core candidate | Positive revenue/EV; margin differences |
| Book-to-market | 100% | 100% | Core candidate | Positive common equity |
| Shareholder yield | 39.39% | 14.29% | **Reject sparse** | Issuance/payout rows absent or inconsistent |
| Revenue growth | 100% | 100% | Core candidate | Positive comparable annual bases |
| Operating-income growth | 100% raw inputs | 100% | Supplemental | Sign-changing bases reduce usable coverage |
| Net-income growth | 100% raw inputs | 100% | Supplemental | Sign-changing bases reduce usable coverage |
| FCF growth | 100% raw inputs | 100% | Supplemental | Sign-changing bases reduce usable coverage |
| Asset growth | 100% | 100% | Diagnostic | Interpret as investment/conservatism, not simple growth |

`MARGIN_CHANGE` uses the same fully covered operating-income/revenue inputs as operating margin and remains a core Growth candidate subject to comparable-period validation.

## Current analyst/revision decision

EPS revisions, EPS trend and revenue estimates were nonempty for 110/110; recent earnings surprises were nonempty for 105/110 and 66/66 of the primary subset. They pass current coverage but are **not admitted to the first composite family** because no historical retrieval archive exists. They begin prospective accumulation only.

## Price-factor coverage expectation

All 110 tickers had daily history, but final price eligibility still requires 504 sessions, 252 signal observations and the liquidity gate. M12–1, M6–1, 200-day trend, volatility, downside volatility, drawdown and relative-strength calculations are technically feasible. Their historical interpretation remains survivor-biased because the universe is current.

## Currency and universe effect

The balanced sample contained 84 US-domiciled companies and 97 USD financial reporters. Applying US domicile, USD financial currency, Financial Services exclusion and Real Estate exclusion reduced the fundamental-coverage subset to 66 names across nine sectors. This confirms that Yahoo `region=us` alone is not a sufficient domestic-common-stock rule.

## Initial category admission

- **Price:** M12–1, M6–1, 200-day trend and inverse 252-day volatility.
- **Quality:** ROA, gross profitability/assets, operating margin, FCF margin, inverse debt/assets and inverse dilution.
- **Value:** FCF yield, EBIT/EV, sales/EV and book-to-market.
- **Growth:** revenue growth and operating-margin improvement.
- **Prospective diagnostics:** approximate ROIC, cash conversion, net debt/EBITDA, interest coverage, earnings yield, earnings/FCF growth, asset growth, revisions and surprises.
- **Rejected:** shareholder yield for this generation.

This is a data-admission decision, not a performance selection. Correlation, valid-denominator, sign, unit and score-stability tests remain mandatory before the next checkpoint can freeze calculation code.

## Data artifacts

- [Ticker-level coverage CSV](../outputs/experiment_runs/EXP-0012/yfinance_capability_ticker_coverage.csv)
- [Endpoint matrix CSV](../outputs/experiment_runs/EXP-0012/yfinance_endpoint_coverage_matrix.csv)
- [Statement field matrix CSV](../outputs/experiment_runs/EXP-0012/yfinance_statement_field_coverage_matrix.csv)
- [Factor input matrix CSV](../outputs/experiment_runs/EXP-0012/yfinance_factor_input_coverage_matrix.csv)
- [Factor-by-sector matrix CSV](../outputs/experiment_runs/EXP-0012/yfinance_factor_sector_coverage_matrix.csv)
