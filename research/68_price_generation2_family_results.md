# Price Generation 2 — family results (Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.)

| Candidate | Family | Dev TO | Dev ann ret | Median vs SPY | Median vs QQQ | Fold wins SPY/6 | Pass gates |
|---|---:|---:|---:|---:|---:|---:|
| A1 | Family A — momentum | 4.63 | +22.1462% | +2.2443% | -4.0866% | 4/6 | FAIL |
| A2 | Family A — momentum | 7.75 | +33.3620% | +16.9901% | +10.7076% | 6/6 | FAIL |
| A3 | Family A — momentum | 6.18 | +25.8415% | +12.2418% | +4.4179% | 6/6 | FAIL |
| A4 | Family A — momentum | 5.89 | +24.7205% | +10.1245% | +2.3883% | 6/6 | FAIL |
| B1 | Family B — trend | 5.52 | +27.1012% | +9.7089% | +3.9668% | 6/6 | FAIL |
| B2 | Family B — trend | 5.48 | +30.7328% | +15.6851% | +8.3364% | 6/6 | FAIL |
| B3 | Family B — trend | 5.01 | +27.8215% | +13.9203% | +4.9758% | 6/6 | FAIL |
| B4 | Family B — trend | 6.15 | +21.5702% | +11.5631% | -3.6261% | 5/6 | FAIL |
| C1 | Family C — relative strength | 18.63 | +12.8836% | +0.1073% | -10.1530% | 3/6 | FAIL |
| C2 | Family C — relative strength | 12.20 | +13.4358% | +1.8084% | -4.5224% | 4/6 | FAIL |
| C3 | Family C — relative strength | 5.46 | +23.5721% | +6.5271% | +0.6878% | 6/6 | FAIL |
| C4 | Family C — relative strength | 5.24 | +24.7861% | +9.6490% | +2.9636% | 6/6 | FAIL |
| D1 | Family D — risk adjustment | 3.11 | +42.5302% | +16.2304% | +10.2792% | 5/6 | FAIL |
| D2 | Family D — risk adjustment | 7.33 | +11.9716% | +5.0734% | -0.8126% | 4/6 | FAIL |
| D3 | Family D — risk adjustment | 6.70 | +23.5126% | +9.8385% | +2.6796% | 5/6 | FAIL |
| D4 | Family D — risk adjustment | 5.52 | +9.8716% | +0.1187% | -7.2703% | 3/6 | FAIL |
| E1 | Family E — trend quality | 5.97 | +19.2691% | +11.5145% | +3.8604% | 5/6 | FAIL |
| E2 | Family E — trend quality | 4.91 | +13.9554% | -1.0223% | -6.7663% | 3/6 | FAIL |
| E3 | Family E — trend quality | 1.00 | +78.2460% | +25.3951% | +16.0201% | 5/6 | FAIL |
| E4 | Family E — trend quality | 12.35 | +26.1159% | +16.1138% | -0.6064% | 5/6 | FAIL |

Note: D3 (vol decile exclusion), D4 (vol cap), E3 (drawdown stability), E4 (consistency) are assessed with their respective availability screens.

**No candidate passed every development gate.**
