# Current daily YF-QVP decision-support report

**Run:** `2026-06-24T080500Z`  
**Retrieval start:** 2026-06-24T08:05:00.833985+00:00  
**Retrieval finish:** 2026-06-24T08:56:01.277223+00:00  
**Latest completed score session:** 2026-06-23  
**Source snapshot:** `data/prospective/daily_qvp/snapshots/2026-06-24T080500Z/raw`  
**Universe:** 2205 screened; 1070 eligible; 1034 fully scored for YF-QVP.  
**Code commit:** `33ff41b93a92e74b56415b879829d3f69fa59acb`  
**Configuration SHA-256:** `d3881a1328862a39dc4af32e15c4826237a09adca2da7038eafb5659ddb68bb4`  
**Output manifest identity SHA-256:** `80cd62661f1ec4a4bd867430747f99e1dd0a12810f4e682ce2b18eaee15f67ef`  
**Classification:** current decision-support research; not prospective performance evidence and not a trade instruction.

## Universe reconciliation

Old eligible: 698; corrected current eligible: 1070; fully QVP-scored: 1034; overlap: 692; additions: 378; removed: 6.

| stage | count |
| --- | --- |
| screened_market_cap_at_least_2b | 1879 |
| exchange | 1879 |
| quote_type | 1879 |
| country | 1509 |
| currency | 1500 |
| market_cap | 1500 |
| price | 1500 |
| history | 1429 |
| liquidity | 1423 |
| sector_present | 1423 |
| financials_exclusion | 1188 |
| real_estate_exclusion | 1090 |
| nonordinary | 1080 |
| issuer_share_class_dedup | 1070 |

## Model

YF-QVP averages frozen Quality, Value and Price category percentiles. The model portfolio contains 30 equal-target names subject to 25% sector and 15% industry caps. Scores can run on demand; review and transaction timing remain user choices.

## Constrained top 30

| portfolio_rank | ticker | company_name | sector | industry | unconstrained_rank | qvp_score | target_weight | selection_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | NTCT | NetScout Systems, Inc. | Technology | Software - Infrastructure | 1.0000 | 0.7740 | 0.0333 | unconstrained_top_30 |
| 2 | CRUS | Cirrus Logic, Inc. | Technology | Semiconductors | 2.0000 | 0.7410 | 0.0333 | unconstrained_top_30 |
| 3 | VISN | Vistance Networks, Inc. | Technology | Communication Equipment | 3.0000 | 0.7389 | 0.0333 | unconstrained_top_30 |
| 4 | RAMP | LiveRamp Holdings, Inc. | Technology | Software - Infrastructure | 4.0000 | 0.7387 | 0.0333 | unconstrained_top_30 |
| 5 | UGI | UGI Corporation | Utilities | Utilities - Regulated Gas | 5.0000 | 0.7369 | 0.0333 | unconstrained_top_30 |
| 6 | DINO | HF Sinclair Corporation | Energy | Oil & Gas Refining & Marketing | 6.0000 | 0.7344 | 0.0333 | unconstrained_top_30 |
| 7 | INCY | Incyte Corporation | Healthcare | Biotechnology | 7.0000 | 0.7299 | 0.0333 | unconstrained_top_30 |
| 8 | MLI | Mueller Industries, Inc. | Industrials | Metal Fabrication | 8.0000 | 0.7289 | 0.0333 | unconstrained_top_30 |
| 9 | EIX | Edison International | Utilities | Utilities - Regulated Electric | 9.0000 | 0.7261 | 0.0333 | unconstrained_top_30 |
| 10 | APA | APA Corporation | Energy | Oil & Gas E&P | 10.0000 | 0.7248 | 0.0333 | unconstrained_top_30 |
| 11 | AZZ | AZZ Inc. | Industrials | Specialty Business Services | 11.0000 | 0.7216 | 0.0333 | unconstrained_top_30 |
| 12 | KFY | Korn Ferry | Industrials | Staffing & Employment Services | 12.0000 | 0.7194 | 0.0333 | unconstrained_top_30 |
| 13 | POR | Portland General Electric Company | Utilities | Utilities - Regulated Electric | 13.0000 | 0.7180 | 0.0333 | unconstrained_top_30 |
| 14 | TDC | Teradata Corporation | Technology | Software - Infrastructure | 14.0000 | 0.7123 | 0.0333 | unconstrained_top_30 |
| 15 | ED | Consolidated Edison, Inc. | Utilities | Utilities - Regulated Electric | 15.0000 | 0.7075 | 0.0333 | unconstrained_top_30 |
| 16 | PRDO | Perdoceo Education Corporation | Consumer Defensive | Education & Training Services | 16.0000 | 0.7031 | 0.0333 | unconstrained_top_30 |
| 17 | ENS | EnerSys | Industrials | Electrical Equipment & Parts | 17.0000 | 0.7002 | 0.0333 | unconstrained_top_30 |
| 18 | EXEL | Exelixis, Inc. | Healthcare | Biotechnology | 18.0000 | 0.6966 | 0.0333 | unconstrained_top_30 |
| 19 | SNA | Snap-on Incorporated | Industrials | Tools & Accessories | 19.0000 | 0.6938 | 0.0333 | unconstrained_top_30 |
| 20 | M | Macy's, Inc. | Consumer Cyclical | Department Stores | 20.0000 | 0.6936 | 0.0333 | unconstrained_top_30 |
| 21 | OGE | OGE Energy Corp. | Utilities | Utilities - Regulated Electric | 21.0000 | 0.6922 | 0.0333 | unconstrained_top_30 |
| 22 | AVA | Avista Corporation | Utilities | Utilities - Diversified | 22.0000 | 0.6919 | 0.0333 | unconstrained_top_30 |
| 23 | CALM | Cal-Maine Foods, Inc. | Consumer Defensive | Farm Products | 23.0000 | 0.6903 | 0.0333 | unconstrained_top_30 |
| 24 | BIIB | Biogen Inc. | Healthcare | Drug Manufacturers - General | 24.0000 | 0.6878 | 0.0333 | unconstrained_top_30 |
| 25 | TTC | The Toro Company | Industrials | Tools & Accessories | 25.0000 | 0.6877 | 0.0333 | unconstrained_top_30 |
| 26 | ZM | Zoom Communications, Inc. | Technology | Software - Application | 26.0000 | 0.6876 | 0.0333 | unconstrained_top_30 |
| 27 | PARR | Par Pacific Holdings, Inc. | Energy | Oil & Gas Refining & Marketing | 27.0000 | 0.6872 | 0.0333 | unconstrained_top_30 |
| 28 | NOV | NOV Inc. | Energy | Oil & Gas Equipment & Services | 28.0000 | 0.6863 | 0.0333 | unconstrained_top_30 |
| 29 | EXE | Expand Energy Corporation | Energy | Oil & Gas E&P | 29.0000 | 0.6810 | 0.0333 | unconstrained_top_30 |
| 30 | BRC | Brady Corporation | Industrials | Security & Protection Services | 30.0000 | 0.6803 | 0.0333 | unconstrained_top_30 |

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

The constrained YF-QVP portfolio overlaps the unconstrained YF-P top 30 in 2 names. This is a current cross-sectional comparison, not a return result.

## Change from previous daily run

Entrants to top 30: none. Departures: none. Rank-60 downward crosses: MYRG, RRC. Largest improvements: RL +114, ALGT +102, PRIM +90, LUV +88, CROX +84. Largest deteriorations: DD -106, AMR -75, AVGO -66, HAS -64, RBA -64. Largest QVP score changes: QBTS +0.0564, IONQ +0.0443, JBLU +0.0305, SMCI +0.0303, RL +0.0291. Newly missing: none.

## Contribution illustrations

- USD 0: no allocation; contribution is zero; residual cash $0.00
- USD 250: NTCT $83.33 (2.0505 shares), CRUS $83.33 (0.5282 shares), VISN $83.33 (6.6667 shares); residual cash $-0.00
- USD 500: NTCT $166.67 (4.1010 shares), CRUS $166.67 (1.0563 shares), VISN $166.67 (13.3333 shares); residual cash $-0.00
- USD 1,000: NTCT $333.33 (8.2021 shares), CRUS $333.33 (2.1126 shares), VISN $333.33 (26.6667 shares); residual cash $-0.00
- USD 5,000: NTCT $1,666.67 (41.0105 shares), CRUS $1,666.67 (10.5632 shares), VISN $1,666.67 (133.3333 shares); residual cash $0.00

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
