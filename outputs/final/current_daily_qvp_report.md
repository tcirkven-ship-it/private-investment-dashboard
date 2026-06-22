# Current daily YF-QVP decision-support report

**Run:** `2026-06-22T172514Z`  
**Retrieval start:** 2026-06-22T17:25:14.461566+00:00  
**Retrieval finish:** 2026-06-22T18:43:27.580303+00:00  
**Latest completed score session:** 2026-06-18  
**Source snapshot:** `data/prospective/daily_qvp/snapshots/2026-06-22T172514Z/raw`  
**Universe:** 2205 screened; 1069 eligible; 1033 fully scored for YF-QVP.  
**Code commit:** `72af374d04e901f3a678712add4dd00b5ebe3982`  
**Configuration SHA-256:** `d3881a1328862a39dc4af32e15c4826237a09adca2da7038eafb5659ddb68bb4`  
**Output manifest identity SHA-256:** `bc5bfb4dae7f730ab765e07368bea9a7335e09f5fd36468db78e6337fae502d2`  
**Classification:** current decision-support research; not prospective performance evidence and not a trade instruction.

## Universe reconciliation

Old eligible: 698; corrected current eligible: 1069; fully QVP-scored: 1033; overlap: 693; additions: 376; removed: 5.

| stage | count |
| --- | --- |
| screened_market_cap_at_least_2b | 1875 |
| exchange | 1875 |
| quote_type | 1875 |
| country | 1504 |
| currency | 1495 |
| market_cap | 1495 |
| price | 1495 |
| history | 1423 |
| liquidity | 1419 |
| sector_present | 1419 |
| financials_exclusion | 1188 |
| real_estate_exclusion | 1091 |
| nonordinary | 1079 |
| issuer_share_class_dedup | 1069 |

## Model

YF-QVP averages frozen Quality, Value and Price category percentiles. The model portfolio contains 30 equal-target names subject to 25% sector and 15% industry caps. Scores can run on demand; review and transaction timing remain user choices.

## Constrained top 30

| portfolio_rank | ticker | company_name | sector | industry | unconstrained_rank | qvp_score | target_weight | selection_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | NTCT | NetScout Systems, Inc. | Technology | Software - Infrastructure | 1.0000 | 0.7761 | 0.0333 | unconstrained_top_30 |
| 2 | CRUS | Cirrus Logic, Inc. | Technology | Semiconductors | 2.0000 | 0.7418 | 0.0333 | unconstrained_top_30 |
| 3 | RAMP | LiveRamp Holdings, Inc. | Technology | Software - Infrastructure | 3.0000 | 0.7370 | 0.0333 | unconstrained_top_30 |
| 4 | DINO | HF Sinclair Corporation | Energy | Oil & Gas Refining & Marketing | 4.0000 | 0.7366 | 0.0333 | unconstrained_top_30 |
| 5 | UGI | UGI Corporation | Utilities | Utilities - Regulated Gas | 5.0000 | 0.7345 | 0.0333 | unconstrained_top_30 |
| 6 | VISN | Vistance Networks, Inc. | Technology | Communication Equipment | 6.0000 | 0.7323 | 0.0333 | unconstrained_top_30 |
| 7 | MLI | Mueller Industries, Inc. | Industrials | Metal Fabrication | 7.0000 | 0.7306 | 0.0333 | unconstrained_top_30 |
| 8 | EIX | Edison International | Utilities | Utilities - Regulated Electric | 8.0000 | 0.7285 | 0.0333 | unconstrained_top_30 |
| 9 | KFY | Korn Ferry | Industrials | Staffing & Employment Services | 9.0000 | 0.7244 | 0.0333 | unconstrained_top_30 |
| 10 | APA | APA Corporation | Energy | Oil & Gas E&P | 10.0000 | 0.7234 | 0.0333 | unconstrained_top_30 |
| 11 | INCY | Incyte Corporation | Healthcare | Biotechnology | 11.0000 | 0.7229 | 0.0333 | unconstrained_top_30 |
| 12 | AZZ | AZZ Inc. | Industrials | Specialty Business Services | 12.0000 | 0.7196 | 0.0333 | unconstrained_top_30 |
| 13 | POR | Portland General Electric Company | Utilities | Utilities - Regulated Electric | 13.0000 | 0.7179 | 0.0333 | unconstrained_top_30 |
| 14 | TDC | Teradata Corporation | Technology | Software - Infrastructure | 14.0000 | 0.7172 | 0.0333 | unconstrained_top_30 |
| 15 | ED | Consolidated Edison, Inc. | Utilities | Utilities - Regulated Electric | 15.0000 | 0.7111 | 0.0333 | unconstrained_top_30 |
| 16 | PRDO | Perdoceo Education Corporation | Consumer Defensive | Education & Training Services | 16.0000 | 0.7017 | 0.0333 | unconstrained_top_30 |
| 17 | ZM | Zoom Communications, Inc. | Technology | Software - Application | 17.0000 | 0.6997 | 0.0333 | unconstrained_top_30 |
| 18 | TTC | The Toro Company | Industrials | Tools & Accessories | 18.0000 | 0.6988 | 0.0333 | unconstrained_top_30 |
| 19 | SNA | Snap-on Incorporated | Industrials | Tools & Accessories | 19.0000 | 0.6964 | 0.0333 | unconstrained_top_30 |
| 20 | CALM | Cal-Maine Foods, Inc. | Consumer Defensive | Farm Products | 20.0000 | 0.6957 | 0.0333 | unconstrained_top_30 |
| 21 | ENS | EnerSys | Industrials | Electrical Equipment & Parts | 21.0000 | 0.6946 | 0.0333 | unconstrained_top_30 |
| 22 | PARR | Par Pacific Holdings, Inc. | Energy | Oil & Gas Refining & Marketing | 22.0000 | 0.6923 | 0.0333 | unconstrained_top_30 |
| 23 | OGE | OGE Energy Corp. | Utilities | Utilities - Regulated Electric | 23.0000 | 0.6910 | 0.0333 | unconstrained_top_30 |
| 24 | EXEL | Exelixis, Inc. | Healthcare | Biotechnology | 24.0000 | 0.6910 | 0.0333 | unconstrained_top_30 |
| 25 | BIIB | Biogen Inc. | Healthcare | Drug Manufacturers - General | 25.0000 | 0.6895 | 0.0333 | unconstrained_top_30 |
| 26 | EXE | Expand Energy Corporation | Energy | Oil & Gas E&P | 26.0000 | 0.6895 | 0.0333 | unconstrained_top_30 |
| 27 | AVA | Avista Corporation | Utilities | Utilities - Diversified | 27.0000 | 0.6892 | 0.0333 | unconstrained_top_30 |
| 28 | NOV | NOV Inc. | Energy | Oil & Gas Equipment & Services | 28.0000 | 0.6872 | 0.0333 | unconstrained_top_30 |
| 29 | BRC | Brady Corporation | Industrials | Security & Protection Services | 29.0000 | 0.6865 | 0.0333 | unconstrained_top_30 |
| 30 | M | Macy's, Inc. | Consumer Cyclical | Department Stores | 30.0000 | 0.6835 | 0.0333 | unconstrained_top_30 |

## Portfolio-constraint effects

No score-leading name was excluded by a portfolio cap.

## Exposure

| dimension | label | names | target_weight |
| --- | --- | --- | --- |
| sector | Consumer Cyclical | 1 | 0.0333 |
| sector | Consumer Defensive | 2 | 0.0667 |
| sector | Energy | 5 | 0.1667 |
| sector | Healthcare | 3 | 0.1000 |
| sector | Industrials | 7 | 0.2333 |
| sector | Technology | 6 | 0.2000 |
| sector | Utilities | 6 | 0.2000 |
| industry | Biotechnology | 2 | 0.0667 |
| industry | Communication Equipment | 1 | 0.0333 |
| industry | Department Stores | 1 | 0.0333 |
| industry | Drug Manufacturers - General | 1 | 0.0333 |
| industry | Education & Training Services | 1 | 0.0333 |
| industry | Electrical Equipment & Parts | 1 | 0.0333 |
| industry | Farm Products | 1 | 0.0333 |
| industry | Metal Fabrication | 1 | 0.0333 |
| industry | Oil & Gas E&P | 2 | 0.0667 |
| industry | Oil & Gas Equipment & Services | 1 | 0.0333 |
| industry | Oil & Gas Refining & Marketing | 2 | 0.0667 |
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

The constrained YF-QVP portfolio overlaps the unconstrained YF-P top 30 in 1 names. This is a current cross-sectional comparison, not a return result.

## Change from previous daily run

First daily-scanner run; no prior daily snapshot was substituted.

## Contribution illustrations

- USD 0: no allocation; contribution is zero; residual cash $0.00
- USD 250: NTCT $83.33 (2.1007 shares), CRUS $83.33 (0.5042 shares), RAMP $83.33 (2.2081 shares); residual cash $-0.00
- USD 500: NTCT $166.67 (4.2013 shares), CRUS $166.67 (1.0083 shares), RAMP $166.67 (4.4162 shares); residual cash $-0.00
- USD 1,000: NTCT $333.33 (8.4027 shares), CRUS $333.33 (2.0167 shares), RAMP $333.33 (8.8324 shares); residual cash $-0.00
- USD 5,000: NTCT $1,666.67 (42.0133 shares), CRUS $1,666.67 (10.0833 shares), RAMP $1,666.67 (44.1618 shares); residual cash $0.00

## Holdings analysis

No holdings file was supplied; no personal holdings classification was generated.

## Data-quality warnings

- 36 eligible stocks have at least one score or price-freshness flag.
- 36 eligible stocks lack a complete YF-QVP score and are not ranked for selection.
- Fundamental and valuation fields are current retrieval-time observations, not historical point-in-time vintages.
- Yahoo classifications and active security coverage can change and do not include a reliable delisting history.

## Limitations

The complete QVP model cannot receive a reliable long historical backtest from yfinance alone because point-in-time market capitalization, enterprise value and valuation vintages are unavailable. Current fundamentals may be restated; the current universe is not a historical universe and excludes inactive/delisted names.

This model portfolio is not proven to outperform SPY or QQQ and is not personalized investment advice. The user decides whether and when to trade.
