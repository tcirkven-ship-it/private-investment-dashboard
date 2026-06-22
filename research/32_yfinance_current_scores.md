# Phase 1B current research scores

**Purpose:** inspection of current factor mechanics only  
**Not:** a portfolio, recommendation, order list, or performance result

## Score availability

The strict common-factor rule produced scores for 698 names in `YF-P`, 676 in `YF-QP`, 674 in `YF-QVP`, and 672 in `YF-QVGP`. Missing required factors explain the differences; no median imputation was used.

The highest five current research scores are:

| Candidate | Highest current scores |
|---|---|
| `YF-P` | KGS, MSGS, ARW, INSW, CSCO |
| `YF-QP` | FIX, MLI, ALAB, MNST, NVDA |
| `YF-QVP` | NTCT, CRUS, EIX, MLI, DINO |
| `YF-QVGP` | CALM, EXE, EIX, MLI, INCY |

The lowest five are:

| Candidate | Lowest current scores |
|---|---|
| `YF-P` | KD, LCID, KVYO, HUBS, DUOL |
| `YF-QP` | LCID, FOUR, KD, LEU, MSTR |
| `YF-QVP` | LCID, LEU, JOBY, INSM, ACHR |
| `YF-QVGP` | GPGI, CORZ, LEU, EL, BEPC |

These names are shown solely to make the scoring layer inspectable. They are not approved holdings.

## Disagreements and exposures

MSGS has the largest candidate percentile spread: 99.86th percentile in `YF-P` and 5.51st in `YF-QVGP`. DUOL moves in the opposite direction, from 0.72nd in `YF-P` to 90.77th in `YF-QVGP`. Other large disagreements include AXTI, FRSH, CSX, LRN, BE, LSCC, CORZ, and BW. This confirms that fundamentals materially change current rankings without saying whether the changes improve returns.

The current `YF-P` top-30 research cut is 43.3% Technology. The equivalent largest-sector shares are 33.3% for `YF-QP`, 26.7% for `YF-QVP`, and 20.0% for `YF-QVGP`. Top-decile sector HHI declines from 0.281 for `YF-P` to 0.149 for `YF-QVP` and 0.145 for `YF-QVGP`. These are unconstrained rank diagnostics, not portfolio exposures; the proposed portfolio caps were not applied and no orders were generated.

## Files

The output directory contains factor-level, category, composite, eligibility, top/bottom, disagreement, sector/market-cap exposure, concentration, correlation, distribution, and outlier-ready tables. `analysis_manifest.json` records their checksums.

