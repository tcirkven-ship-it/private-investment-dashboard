# Current daily YF-QVP decision-support report

**Run:** `2026-10-06T142958Z`  
**Retrieval start:** 2026-10-06T17:18:00.923876+00:00  
**Retrieval finish:** 2026-10-06T17:24:47.586158+00:00  
**Latest completed score session:** 2026-10-05  
**Source snapshot:** `data/prospective/daily_qvp/snapshots/2026-10-06T142958Z/raw`  
**Universe:** 2157 screened; 1049 eligible; 1014 fully scored for YF-QVP.  
**Code commit:** `476a0536c46a788a7630fa9f3e94f5d730de1f8c`  
**Configuration SHA-256:** `d3881a1328862a39dc4af32e15c4826237a09adca2da7038eafb5659ddb68bb4`  
**Output manifest identity SHA-256:** `7194e4af2e31dac8fc23edad49491676d7b802278c45a341c3257fc8203aed7a`  
**Classification:** current decision-support research; not prospective performance evidence and not a trade instruction.

## Universe reconciliation

Old eligible: 698; corrected current eligible: 1049; fully QVP-scored: 1014; overlap: 660; additions: 389; removed: 38.

| stage | count |
| --- | --- |
| screened_market_cap_at_least_2b | 1828 |
| exchange | 1828 |
| quote_type | 1828 |
| country | 1467 |
| currency | 1465 |
| market_cap | 1464 |
| price | 1464 |
| history | 1388 |
| liquidity | 1383 |
| sector_present | 1383 |
| financials_exclusion | 1159 |
| real_estate_exclusion | 1066 |
| nonordinary | 1056 |
| issuer_share_class_dedup | 1049 |

## Model

YF-QVP averages frozen Quality, Value and Price category percentiles. The model portfolio contains 30 equal-target names subject to 25% sector and 15% industry caps. Scores can run on demand; review and transaction timing remain user choices.

## Constrained top 30

| portfolio_rank | ticker | company_name | sector | industry | unconstrained_rank | qvp_score | target_weight | selection_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | INCY | Incyte Corporation | Healthcare | Biotechnology | 1.0000 | 0.7998 | 0.0333 | unconstrained_top_30 |
| 2 | RAMP | LiveRamp Holdings, Inc. | Technology | Software - Infrastructure | 2.0000 | 0.7856 | 0.0333 | unconstrained_top_30 |
| 3 | DINO | HF Sinclair Corporation | Energy | Oil & Gas Refining & Marketing | 3.0000 | 0.7706 | 0.0333 | unconstrained_top_30 |
| 4 | RELY | Remitly Global, Inc. | Technology | Software - Infrastructure | 4.0000 | 0.7705 | 0.0333 | unconstrained_top_30 |
| 5 | KFY | Korn Ferry | Industrials | Staffing & Employment Services | 5.0000 | 0.7608 | 0.0333 | unconstrained_top_30 |
| 6 | UGI | UGI Corporation | Utilities | Utilities - Regulated Gas | 6.0000 | 0.7606 | 0.0333 | unconstrained_top_30 |
| 7 | EXEL | Exelixis, Inc. | Healthcare | Biotechnology | 7.0000 | 0.7536 | 0.0333 | unconstrained_top_30 |
| 8 | NTCT | NetScout Systems, Inc. | Technology | Software - Infrastructure | 8.0000 | 0.7535 | 0.0333 | unconstrained_top_30 |
| 9 | PARR | Par Pacific Holdings, Inc. | Energy | Oil & Gas Refining & Marketing | 9.0000 | 0.7302 | 0.0333 | unconstrained_top_30 |
| 10 | TDC | Teradata Corporation | Technology | Software - Infrastructure | 10.0000 | 0.7275 | 0.0333 | unconstrained_top_30 |
| 11 | ADUS | Addus HomeCare Corporation | Healthcare | Medical Care Facilities | 11.0000 | 0.7246 | 0.0333 | unconstrained_top_30 |
| 12 | FRSH | Freshworks Inc. | Technology | Software - Application | 12.0000 | 0.7238 | 0.0333 | unconstrained_top_30 |
| 13 | CHRD | Chord Energy Corporation | Energy | Oil & Gas E&P | 13.0000 | 0.7194 | 0.0333 | unconstrained_top_30 |
| 14 | ZM | Zoom Communications, Inc. | Technology | Software - Application | 15.0000 | 0.7144 | 0.0333 | unconstrained_top_30 |
| 15 | VLO | Valero Energy Corporation | Energy | Oil & Gas Refining & Marketing | 16.0000 | 0.7128 | 0.0333 | unconstrained_top_30 |
| 16 | ANF | Abercrombie & Fitch Co. | Consumer Cyclical | Apparel Retail | 17.0000 | 0.7122 | 0.0333 | unconstrained_top_30 |
| 17 | CART | Maplebear Inc. | Consumer Cyclical | Internet Retail | 18.0000 | 0.7075 | 0.0333 | unconstrained_top_30 |
| 18 | DV | DoubleVerify Holdings, Inc. | Communication Services | Advertising Agencies | 19.0000 | 0.7062 | 0.0333 | unconstrained_top_30 |
| 19 | M | Macy's, Inc. | Consumer Cyclical | Department Stores | 20.0000 | 0.7042 | 0.0333 | unconstrained_top_30 |
| 20 | MD | Pediatrix Medical Group, Inc. | Healthcare | Medical Care Facilities | 21.0000 | 0.7033 | 0.0333 | unconstrained_top_30 |
| 21 | APA | APA Corporation | Energy | Oil & Gas E&P | 22.0000 | 0.7032 | 0.0333 | unconstrained_top_30 |
| 22 | CNC | Centene Corporation | Healthcare | Healthcare Plans | 23.0000 | 0.7029 | 0.0333 | unconstrained_top_30 |
| 23 | THC | Tenet Healthcare Corporation | Healthcare | Medical Care Facilities | 24.0000 | 0.7028 | 0.0333 | unconstrained_top_30 |
| 24 | OVV | Ovintiv Inc. | Energy | Oil & Gas E&P | 25.0000 | 0.6973 | 0.0333 | unconstrained_top_30 |
| 25 | EOG | EOG Resources, Inc. | Energy | Oil & Gas E&P | 26.0000 | 0.6970 | 0.0333 | unconstrained_top_30 |
| 26 | SWK | Stanley Black & Decker, Inc. | Industrials | Tools & Accessories | 27.0000 | 0.6925 | 0.0333 | unconstrained_top_30 |
| 27 | BIIB | Biogen Inc. | Healthcare | Drug Manufacturers - General | 28.0000 | 0.6913 | 0.0333 | unconstrained_top_30 |
| 28 | ED | Consolidated Edison, Inc. | Utilities | Utilities - Regulated Electric | 29.0000 | 0.6892 | 0.0333 | unconstrained_top_30 |
| 29 | RHI | Robert Half Inc. | Industrials | Staffing & Employment Services | 30.0000 | 0.6886 | 0.0333 | unconstrained_top_30 |
| 30 | AVA | Avista Corporation | Utilities | Utilities - Diversified | 32.0000 | 0.6840 | 0.0333 | constraint_replacement |

## Portfolio-constraint effects

| ticker | unconstrained_rank | reason | sector | industry | would_be_unconstrained_top30 |
| --- | --- | --- | --- | --- | --- |
| FLYW | 14 | industry_cap | Technology | Software - Infrastructure | True |

## Exposure

| dimension | label | names | target_weight |
| --- | --- | --- | --- |
| sector | Communication Services | 1 | 0.0333 |
| sector | Consumer Cyclical | 3 | 0.1000 |
| sector | Energy | 7 | 0.2333 |
| sector | Healthcare | 7 | 0.2333 |
| sector | Industrials | 3 | 0.1000 |
| sector | Technology | 6 | 0.2000 |
| sector | Utilities | 3 | 0.1000 |
| industry | Advertising Agencies | 1 | 0.0333 |
| industry | Apparel Retail | 1 | 0.0333 |
| industry | Biotechnology | 2 | 0.0667 |
| industry | Department Stores | 1 | 0.0333 |
| industry | Drug Manufacturers - General | 1 | 0.0333 |
| industry | Healthcare Plans | 1 | 0.0333 |
| industry | Internet Retail | 1 | 0.0333 |
| industry | Medical Care Facilities | 3 | 0.1000 |
| industry | Oil & Gas E&P | 4 | 0.1333 |
| industry | Oil & Gas Refining & Marketing | 3 | 0.1000 |
| industry | Software - Application | 2 | 0.0667 |
| industry | Software - Infrastructure | 4 | 0.1333 |
| industry | Staffing & Employment Services | 2 | 0.0667 |
| industry | Tools & Accessories | 1 | 0.0333 |
| industry | Utilities - Diversified | 1 | 0.0333 |
| industry | Utilities - Regulated Electric | 1 | 0.0333 |
| industry | Utilities - Regulated Gas | 1 | 0.0333 |

## Comparison with YF-P

The constrained YF-QVP portfolio overlaps the unconstrained YF-P top 30 in 2 names. This is a current cross-sectional comparison, not a return result.

## Change from previous daily run

Entrants to top 30: ADUS, ANF, CART, CHRD, CNC, DV, EOG, FLYW, FRSH, MD, OVV, RELY, RHI, SWK, THC, VLO. Departures: AVA, AZZ, BRC, CALM, CRUS, EIX, ENS, NBIX, OGE, POR, PRDO, SIRI, SNA, TTC, VISN, WLY. Rank-60 downward crosses: ADM, AIT, AZZ, BWA, CALM, CBT, CF, CRC, CRUS, DAL, EIX, ENS, ES, FDX, FFIV, GNTX, KEX, LEA, MATX, NJR, NOV, NYT, OGE, POR, RS, RUSHA, TTC, UTHR, WLY. Largest improvements: MGNI +681, QTWO +626, TNET +564, NTNX +534, DNOW +524. Largest deteriorations: RRX -541, HII -515, RMBS -487, CW -438, NXT -426. Largest QVP score changes: PL -0.1986, MGNI +0.1938, PRIM -0.1740, QTWO +0.1701, MTZ -0.1696. Newly missing: UEC.

## Contribution illustrations

- USD 0: no allocation; contribution is zero; residual cash $0.00
- USD 250: INCY $83.33 (0.7302 shares), RAMP $83.33 (2.2098 shares), DINO $83.33 (0.7233 shares); residual cash $-0.00
- USD 500: INCY $166.67 (1.4603 shares), RAMP $166.67 (4.4197 shares), DINO $166.67 (1.4465 shares); residual cash $-0.00
- USD 1,000: INCY $333.33 (2.9206 shares), RAMP $333.33 (8.8394 shares), DINO $333.33 (2.8930 shares); residual cash $-0.00
- USD 5,000: INCY $1,666.67 (14.6032 shares), RAMP $1,666.67 (44.1969 shares), DINO $1,666.67 (14.4651 shares); residual cash $0.00

## Holdings analysis

No holdings file was supplied; no personal holdings classification was generated.

## Data-quality warnings

- 35 eligible stocks have at least one score or price-freshness flag.
- 35 eligible stocks lack a complete YF-QVP score and are not ranked for selection.
- Fundamental and valuation fields are current retrieval-time observations, not historical point-in-time vintages.
- Yahoo classifications and active security coverage can change and do not include a reliable delisting history.

## Limitations

The complete QVP model cannot receive a reliable long historical backtest from yfinance alone because point-in-time market capitalization, enterprise value and valuation vintages are unavailable. Current fundamentals may be restated; the current universe is not a historical universe and excludes inactive/delisted names.

This model portfolio is not proven to outperform SPY or QQQ and is not personalized investment advice. The user decides whether and when to trade.
