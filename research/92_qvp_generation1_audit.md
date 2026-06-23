# QVP Integration — corrected overlap audit

| Backbone | Model | P wt | Q wt | V wt | Price gate | Overlap w/P100 | P100 retained | P100 removed | Added |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A3 | G0_P100 | 1.00 | 0.00 | 0.00 | 0 | 30 | 30 | 0 | 0 |
| A3 | G1_R60_RERANK | 0.50 | 0.25 | 0.25 | 60 | 11 | 11 | 19 | 19 |
| A3 | G2_R90_RERANK | 0.50 | 0.25 | 0.25 | 90 | 7 | 7 | 23 | 23 |
| A3 | G3_QVETO | 1.00 | 0.00 | 0.00 | 0 | 21 | 21 | 9 | 9 |
| A3 | G4_QV_VETO | 1.00 | 0.00 | 0.00 | 0 | 6 | 6 | 24 | 24 |
| A3 | G5_TIEBREAK | 1.00 | 0.00 | 0.00 | 0 | 30 | 30 | 0 | 0 |
| B2 | G0_P100 | 1.00 | 0.00 | 0.00 | 0 | 30 | 30 | 0 | 0 |
| B2 | G1_R60_RERANK | 0.50 | 0.25 | 0.25 | 60 | 10 | 10 | 20 | 20 |
| B2 | G2_R90_RERANK | 0.50 | 0.25 | 0.25 | 90 | 7 | 7 | 23 | 23 |
| B2 | G3_QVETO | 1.00 | 0.00 | 0.00 | 0 | 22 | 22 | 8 | 8 |
| B2 | G4_QV_VETO | 1.00 | 0.00 | 0.00 | 0 | 7 | 7 | 23 | 23 |
| B2 | G5_TIEBREAK | 1.00 | 0.00 | 0.00 | 0 | 30 | 30 | 0 | 0 |

B2 P100 self-overlap: 30/30 (confirmed by computing P100 control from
the exact same score formula used for overlap comparison).

Cross-backbone: B2 P100 vs A3 P100 overlap computed in separate comparison.