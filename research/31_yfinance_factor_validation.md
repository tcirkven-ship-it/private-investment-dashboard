# Phase 1B factor validation and admission

**Formula version:** `YF-FACTOR-1.0.0`  
**Evidence used:** current cross-section only; no investment returns were examined

## Full-universe coverage

Price factors have 100% coverage. Primary fundamental-factor coverage ranges from 96.99% to 100% overall. In the smaller-cap groups, representative coverage remains strong: FCF margin is 95.5% in USD 2B–5B and 98.0% in USD 5B–10B; gross profitability is 93.5% and 98.0%; revenue growth and margin change are each at least 95.0%. Full overall, sector, industry, and market-cap reports are stored beside the factor output.

Sparse or guarded factors remain less suitable: shareholder yield 25.07%, FCF growth 76.50%, and net-income growth 74.50%. Five-quarter aligned earnings stability is implemented at 99.28% coverage but remains diagnostic because it was not in the preregistered primary set.

## Frozen primary sets

These sets are frozen for current scoring and the inactive prospective proposal, before any return analysis:

| Category | Fixed primary factors |
|---|---|
| Price | `M12_1`, `M6_1`, `TREND200`, inverse `VOL252` |
| Quality | `ROA`, `GPA`, `FCF_MARGIN`, inverse `DEBT_ASSETS` |
| Value | `FCF_YIELD`, `SALES_EV`, `BOOK_MARKET` |
| Growth | `REV_GROWTH`, `MARGIN_CHANGE` |

A company receives a primary category score only when every factor in that category's fixed common set exists. Thus two companies never receive nominally identical category scores built from materially different inputs. Any future relaxed missing-factor score is a sensitivity, not the primary score.

Diagnostics include relative strength, downside volatility, drawdown, liquidity, approximate ROIC, operating margin, cash conversion, net debt/EBITDA, interest cover, earnings stability, dilution, earnings yield, EBIT/EV, sign-sensitive growth factors, asset growth, and current estimate/revision fields. Expectations coverage is 99.86% for revision breadth, 90.11% for EPS trend, and 97.99% for both revenue-estimate growth and four-event surprise. `SHAREHOLDER_YIELD` is rejected. `REC_CHANGE` is also rejected because `get_recommendations()` returned period-level consensus counts rather than the upgrade/downgrade events required by its formula; it is explicitly missing for all names.

## Correlation and redundancy

The current cross-section has an estimated 11.05 effective independent signals across the implemented candidate-factor matrix, including current expectations diagnostics. `RS252_SEC` and `M12_1` are redundant at Spearman 0.958; the simpler `M12_1` is retained and sector-relative strength remains diagnostic. No pair inside a frozen primary category breached the absolute 0.85 rule. Approximate ROIC and ROA reached 0.843, below but near the threshold; approximate ROIC remains diagnostic on reliability grounds.

Current primary category correlations are Price/Quality −0.038, Price/Value −0.308, Price/Growth 0.017, Quality/Value 0.105, Quality/Growth 0.033, and Value/Growth −0.383. These are descriptive current-cross-sectional relationships, not evidence of alpha.

## Implementation artifacts

`factor_level_current.csv` contains ticker, snapshot timestamp, raw inputs, raw value, missing reason, winsorized value, comparison group, percentile, formula version, and input-file checksums. Sector ranks use 2.5%/97.5% winsorization with a market fallback below 20 valid sector names; primary price ranks use the market cross-section. Invalid denominators produce missing values.

The tested implementation is `src/validation/run_yfinance_checkpoint2.py`; 22 repository tests pass.
