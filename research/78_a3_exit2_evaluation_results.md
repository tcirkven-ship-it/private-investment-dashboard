# A3 exit2 — confirmatory evaluation results (Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.)

## Development reproduction (2015–2020)

Reproduction status: PASS
| Metric | Published | Reproduced |
|---|---:|--:|
| Annualized return | 24.69% | +24.6861% |
| Annual gross turnover | 63.88% | 0.64 |
| Max drawdown | -36.61% | -36.6085% |
| SPY fold wins | 6/6 | 6/6 |
| QQQ fold wins | 3/6 | 3/6 |
| Worst DD vs SPY per fold | -15.09pp | -15.0875% |

## Evaluation results (2021–2025)

### Aggregate

| Metric | A3 exit2 (zero cost) | A3 exit2 (10bps) | SPY | QQQ |
|---|---:|---:|---:|---:|
| Annualized return | +23.1160% | +23.0385% | +14.3961% | +15.1367% |
| Active vs SPY | +8.7199% | +8.6423% | — | — |
| Active vs QQQ | +7.9793% | +7.9018% | — | — |
| Volatility | +23.7104% | +23.7099% | — | — |
| Max drawdown | -28.4165% | -28.4418% | — | — |
| Annual gross turnover | 0.63 | 0.63 | — | — |

### Annual breakdown

| Year | Return | SPY-rel | QQQ-rel | Vol | Max DD | TO |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | +39.0773% | +10.3486% | +11.6576% | +26.0703% | -15.3372% | 0.62 |
| 2022 | -5.6398% | +12.6010% | +27.0430% | +30.0073% | -26.0130% | 0.68 |
| 2023 | +22.2491% | -4.1616% | -33.1492% | +17.9459% | -15.9175% | 0.56 |
| 2024 | +21.4343% | -3.4522% | -4.1440% | +18.7730% | -10.9109% | 0.59 |
| 2025 | +45.2202% | +27.3474% | +24.2651% | +23.6744% | -24.3570% | 0.71 |

### N-size sensitivity

| N | Ann ret | SPY-rel | QQQ-rel | TO |
|---:|---:|---:|---:|---:|
| 20 | +28.7861% | +14.3900% | +13.6494% | 0.68 |
| 30 | +23.1160% | +8.7199% | +7.9793% | 0.63 |
| 40 | +18.3937% | +3.9975% | +3.2570% | 0.59 |

### Sensitivity

| Sensitivity | Ann ret | SPY-rel |
|---|---:|---:|
| Base | +23.1160% | +8.7199% |
| Remove best stock (ILMN) | +23.8853% | +9.4891% |
| Remove best year (2025) | +94.8195% (4yr) | +28.6651% |
| 10bps cost | +23.0385% | +8.6423% |
