# Current daily YF-QVP decision-support report

**Run:** `2026-07-01T053352Z`  
**Retrieval start:** 2026-07-01T05:33:52.980988+00:00  
**Retrieval finish:** 2026-07-01T07:21:20.090043+00:00  
**Latest completed score session:** 2026-06-30  
**Source snapshot:** `data/prospective/daily_qvp/snapshots/2026-07-01T053352Z/raw`  
**Universe:** 2232 screened; 1081 eligible; 1043 fully scored for YF-QVP.  
**Code commit:** `144e01281e848a2a4c711cb0058eddc75099bb40`  
**Configuration SHA-256:** `d3881a1328862a39dc4af32e15c4826237a09adca2da7038eafb5659ddb68bb4`  
**Output manifest identity SHA-256:** `8bda06ce0251beedd6a5f2cd61a08ef37682841102d3b9d86a1ab602640baf4e`  
**Classification:** current decision-support research; not prospective performance evidence and not a trade instruction.

## Universe reconciliation

Old eligible: 698; corrected current eligible: 1081; fully QVP-scored: 1043; overlap: 690; additions: 391; removed: 8.

| stage | count |
| --- | --- |
| screened_market_cap_at_least_2b | 1899 |
| exchange | 1899 |
| quote_type | 1899 |
| country | 1529 |
| currency | 1522 |
| market_cap | 1522 |
| price | 1522 |
| history | 1446 |
| liquidity | 1441 |
| sector_present | 1441 |
| financials_exclusion | 1202 |
| real_estate_exclusion | 1102 |
| nonordinary | 1092 |
| issuer_share_class_dedup | 1081 |

## Model

YF-QVP averages frozen Quality, Value and Price category percentiles. The model portfolio contains 30 equal-target names subject to 25% sector and 15% industry caps. Scores can run on demand; review and transaction timing remain user choices.

## Constrained top 30

| portfolio_rank | ticker | company_name | sector | industry | unconstrained_rank | qvp_score | target_weight | selection_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | NTCT | NetScout Systems, Inc. | Technology | Software - Infrastructure | 1.0000 | 0.7755 | 0.0333 | unconstrained_top_30 |
| 2 | CRUS | Cirrus Logic, Inc. | Technology | Semiconductors | 2.0000 | 0.7370 | 0.0333 | unconstrained_top_30 |
| 3 | VISN | Vistance Networks, Inc. | Technology | Communication Equipment | 3.0000 | 0.7356 | 0.0333 | unconstrained_top_30 |
| 4 | RAMP | LiveRamp Holdings, Inc. | Technology | Software - Infrastructure | 4.0000 | 0.7327 | 0.0333 | unconstrained_top_30 |
| 5 | UGI | UGI Corporation | Utilities | Utilities - Regulated Gas | 5.0000 | 0.7290 | 0.0333 | unconstrained_top_30 |
| 6 | DINO | HF Sinclair Corporation | Energy | Oil & Gas Refining & Marketing | 6.0000 | 0.7258 | 0.0333 | unconstrained_top_30 |
| 7 | INCY | Incyte Corporation | Healthcare | Biotechnology | 7.0000 | 0.7247 | 0.0333 | unconstrained_top_30 |
| 8 | KFY | Korn Ferry | Industrials | Staffing & Employment Services | 8.0000 | 0.7236 | 0.0333 | unconstrained_top_30 |
| 9 | POR | Portland General Electric Company | Utilities | Utilities - Regulated Electric | 9.0000 | 0.7214 | 0.0333 | unconstrained_top_30 |
| 10 | TDC | Teradata Corporation | Technology | Software - Infrastructure | 10.0000 | 0.7190 | 0.0333 | unconstrained_top_30 |
| 11 | EIX | Edison International | Utilities | Utilities - Regulated Electric | 11.0000 | 0.7187 | 0.0333 | unconstrained_top_30 |
| 12 | APA | APA Corporation | Energy | Oil & Gas E&P | 12.0000 | 0.7144 | 0.0333 | unconstrained_top_30 |
| 13 | AZZ | AZZ Inc. | Industrials | Specialty Business Services | 13.0000 | 0.7135 | 0.0333 | unconstrained_top_30 |
| 14 | ZM | Zoom Communications, Inc. | Technology | Software - Application | 14.0000 | 0.7007 | 0.0333 | unconstrained_top_30 |
| 15 | ED | Consolidated Edison, Inc. | Utilities | Utilities - Regulated Electric | 15.0000 | 0.6983 | 0.0333 | unconstrained_top_30 |
| 16 | M | Macy's, Inc. | Consumer Cyclical | Department Stores | 16.0000 | 0.6957 | 0.0333 | unconstrained_top_30 |
| 17 | SNA | Snap-on Incorporated | Industrials | Tools & Accessories | 17.0000 | 0.6950 | 0.0333 | unconstrained_top_30 |
| 18 | AVA | Avista Corporation | Utilities | Utilities - Diversified | 18.0000 | 0.6941 | 0.0333 | unconstrained_top_30 |
| 19 | PARR | Par Pacific Holdings, Inc. | Energy | Oil & Gas Refining & Marketing | 19.0000 | 0.6911 | 0.0333 | unconstrained_top_30 |
| 20 | CALM | Cal-Maine Foods, Inc. | Consumer Defensive | Farm Products | 20.0000 | 0.6908 | 0.0333 | unconstrained_top_30 |
| 21 | ENS | EnerSys | Industrials | Electrical Equipment & Parts | 21.0000 | 0.6893 | 0.0333 | unconstrained_top_30 |
| 22 | BIIB | Biogen Inc. | Healthcare | Drug Manufacturers - General | 22.0000 | 0.6892 | 0.0333 | unconstrained_top_30 |
| 23 | TTC | The Toro Company | Industrials | Tools & Accessories | 23.0000 | 0.6885 | 0.0333 | unconstrained_top_30 |
| 24 | OGE | OGE Energy Corp. | Utilities | Utilities - Regulated Electric | 24.0000 | 0.6851 | 0.0333 | unconstrained_top_30 |
| 25 | BRC | Brady Corporation | Industrials | Security & Protection Services | 25.0000 | 0.6834 | 0.0333 | unconstrained_top_30 |
| 26 | NBIX | Neurocrine Biosciences, Inc. | Healthcare | Drug Manufacturers - Specialty & Generic | 26.0000 | 0.6832 | 0.0333 | unconstrained_top_30 |
| 27 | PRDO | Perdoceo Education Corporation | Consumer Defensive | Education & Training Services | 27.0000 | 0.6821 | 0.0333 | unconstrained_top_30 |
| 28 | EXEL | Exelixis, Inc. | Healthcare | Biotechnology | 28.0000 | 0.6819 | 0.0333 | unconstrained_top_30 |
| 29 | WLY | John Wiley & Sons, Inc. | Communication Services | Publishing | 29.0000 | 0.6803 | 0.0333 | unconstrained_top_30 |
| 30 | SIRI | Sirius XM Holdings Inc. | Communication Services | Entertainment | 30.0000 | 0.6789 | 0.0333 | unconstrained_top_30 |

## Portfolio-constraint effects

No score-leading name was excluded by a portfolio cap.

## Exposure

| dimension | label | names | target_weight |
| --- | --- | --- | --- |
| sector | Communication Services | 2 | 0.0667 |
| sector | Consumer Cyclical | 1 | 0.0333 |
| sector | Consumer Defensive | 2 | 0.0667 |
| sector | Energy | 3 | 0.1000 |
| sector | Healthcare | 4 | 0.1333 |
| sector | Industrials | 6 | 0.2000 |
| sector | Technology | 6 | 0.2000 |
| sector | Utilities | 6 | 0.2000 |
| industry | Biotechnology | 2 | 0.0667 |
| industry | Communication Equipment | 1 | 0.0333 |
| industry | Department Stores | 1 | 0.0333 |
| industry | Drug Manufacturers - General | 1 | 0.0333 |
| industry | Drug Manufacturers - Specialty & Generic | 1 | 0.0333 |
| industry | Education & Training Services | 1 | 0.0333 |
| industry | Electrical Equipment & Parts | 1 | 0.0333 |
| industry | Entertainment | 1 | 0.0333 |
| industry | Farm Products | 1 | 0.0333 |
| industry | Oil & Gas E&P | 1 | 0.0333 |
| industry | Oil & Gas Refining & Marketing | 2 | 0.0667 |
| industry | Publishing | 1 | 0.0333 |
| industry | Security & Protection Services | 1 | 0.0333 |
| industry | Semiconductors | 1 | 0.0333 |
| industry | Software - Application | 1 | 0.0333 |
| industry | Software - Infrastructure | 3 | 0.1000 |
| industry | Specialty Business Services | 1 | 0.0333 |
| industry | Staffing & Employment Services | 1 | 0.0333 |
| industry | Tools & Accessories | 2 | 0.0667 |
| industry | Utilities - Diversified | 1 | 0.0333 |
| industry | Utilities - Regulated Electric | 4 | 0.1333 |
| industry | Utilities - Regulated Gas | 1 | 0.0333 |

## Comparison with YF-P

The constrained YF-QVP portfolio overlaps the unconstrained YF-P top 30 in 2 names. This is a current cross-sectional comparison, not a return result.

## Change from previous daily run

First daily-scanner run; no prior daily snapshot was substituted.

## Contribution illustrations

- USD 0: no allocation; contribution is zero; residual cash $0.00
- USD 250: NTCT $83.33 (1.9135 shares), CRUS $83.33 (0.5611 shares), VISN $83.33 (6.5206 shares); residual cash $-0.00
- USD 500: NTCT $166.67 (3.8270 shares), CRUS $166.67 (1.1221 shares), VISN $166.67 (13.0412 shares); residual cash $-0.00
- USD 1,000: NTCT $333.33 (7.6540 shares), CRUS $333.33 (2.2442 shares), VISN $333.33 (26.0824 shares); residual cash $-0.00
- USD 5,000: NTCT $1,666.67 (38.2702 shares), CRUS $1,666.67 (11.2211 shares), VISN $1,666.67 (130.4121 shares); residual cash $0.00

## Holdings analysis

No holdings file was supplied; no personal holdings classification was generated.

## Data-quality warnings

- 39 eligible stocks have at least one score or price-freshness flag.
- 38 eligible stocks lack a complete YF-QVP score and are not ranked for selection.
- Fundamental and valuation fields are current retrieval-time observations, not historical point-in-time vintages.
- Yahoo classifications and active security coverage can change and do not include a reliable delisting history.

## Limitations

The complete QVP model cannot receive a reliable long historical backtest from yfinance alone because point-in-time market capitalization, enterprise value and valuation vintages are unavailable. Current fundamentals may be restated; the current universe is not a historical universe and excludes inactive/delisted names.

This model portfolio is not proven to outperform SPY or QQQ and is not personalized investment advice. The user decides whether and when to trade.
