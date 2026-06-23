# QVP integration — current architecture comparison

**Evidence label:** Exploratory survivor-biased historical Price research
**Data source:** scanner run 2026-06-22T172514Z

| Backbone | Architecture | P wt | Q wt | V wt | Overlap w/P100 | P100 retained | P100 removed | New added | Missing comp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A3 | P100 | 1.00 | 0.00 | 0.00 | 30 | 30 | 0 | 0 | 0 |
| A3 | P60_Q20_V20 | 0.60 | 0.20 | 0.20 | 7 | 7 | 23 | 23 | 0 |
| A3 | P50_Q25_V25 | 0.50 | 0.25 | 0.25 | 3 | 3 | 27 | 27 | 0 |
| A3 | P33_Q33_V33 | 0.33 | 0.33 | 0.33 | 0 | 0 | 30 | 30 | 0 |
| A3 | P67_Q33 | 0.67 | 0.33 | 0.00 | 9 | 9 | 21 | 21 | 0 |
| A3 | P67_V33 | 0.67 | 0.00 | 0.33 | 1 | 1 | 29 | 29 | 0 |
| B2 | P100 | 1.00 | 0.00 | 0.00 | 22 | 22 | 8 | 8 | 0 |
| B2 | P60_Q20_V20 | 0.60 | 0.20 | 0.20 | 7 | 7 | 23 | 23 | 0 |
| B2 | P50_Q25_V25 | 0.50 | 0.25 | 0.25 | 4 | 4 | 26 | 26 | 0 |
| B2 | P33_Q33_V33 | 0.33 | 0.33 | 0.33 | 0 | 0 | 30 | 30 | 0 |
| B2 | P67_Q33 | 0.67 | 0.33 | 0.00 | 8 | 8 | 22 | 22 | 0 |
| B2 | P67_V33 | 0.67 | 0.00 | 0.33 | 1 | 1 | 29 | 29 | 0 |

## P50_Q25_V25 top 30 overlap with P100

**A3 P50_Q25_V25:** 3/30 overlap with P100. 27 P100 names removed, 27 new names added.
**B2 P50_Q25_V25:** 4/30 overlap with P100. 26 P100 names removed, 26 new names added.