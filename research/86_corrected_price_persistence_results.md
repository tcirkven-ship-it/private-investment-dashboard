# Corrected Price persistence results — fixed exit2 state machine
**Evidence label:** Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.
**Development only (2015–2020), 10bps cost**

| Candidate | Spec | Ann ret | SPY-rel | QQQ-rel | TO | Max DD | DD vs SPY | SPY wins | QQQ wins | Fold dep |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A3 | exit2 | +27.2511% | +14.5808% | +5.8272% | 4.32 | -44.2601% | -15.5029% | 5/6 | 4/6 | 0.66 |
| A3 | combined | +26.2063% | +13.5361% | +4.7824% | 3.89 | -44.4322% | -13.5074% | 4/6 | 3/6 | 0.70 |
| B2 | exit2 | +29.0027% | +16.3325% | +7.5788% | 4.22 | -44.9200% | -11.8770% | 6/6 | 4/6 | 0.53 |
| B2 | combined | +25.1788% | +12.5085% | +3.7549% | 3.91 | -48.1476% | -14.6798% | 4/6 | 3/6 | 0.51 |
| D1 | exit2 | +83.1398% | +70.4695% | +61.7159% | 2.86 | -48.2706% | -19.7417% | 4/6 | 4/6 | 0.95 |
| D1 | combined | +38.8215% | +26.1512% | +17.3976% | 2.22 | -48.7336% | -19.6502% | 4/6 | 4/6 | 0.73 |

## Development gates

| Gate | Threshold |
|---|---|
| Turnover | < 250% |
| Median vs SPY | > 0% |
| Median vs QQQ | > 0% |
| Fold wins vs SPY | >= 4/6 |
| Fold wins vs QQQ | >= 3/6 |
| Absolute max DD | < 40% |
| DD vs SPY per fold | > -15pp |
| Fold dependence | < 60% |

## Gate results

| Candidate | Spec | TO pass | Med SPY | Med QQQ | SPY wins | QQQ wins | Max DD | DD vs SPY | Fold dep | ALL PASS |
|---|---|:---|:---|:---|:---|:---|:---|:---|:---|:---:|
| A3 | exit2 | FAIL | PASS | PASS | 5/6 | 4/6 | FAIL | FAIL | FAIL | FAIL |
| A3 | combined | FAIL | PASS | PASS | 4/6 | 3/6 | FAIL | PASS | FAIL | FAIL |
| B2 | exit2 | FAIL | PASS | PASS | 6/6 | 4/6 | FAIL | PASS | PASS | FAIL |
| B2 | combined | FAIL | PASS | PASS | 4/6 | 3/6 | FAIL | PASS | PASS | FAIL |
| D1 | exit2 | FAIL | PASS | PASS | 4/6 | 4/6 | FAIL | FAIL | FAIL | FAIL |
| D1 | combined | PASS | PASS | PASS | 4/6 | 4/6 | FAIL | FAIL | FAIL | FAIL |

## Decision

**No specification passes all development gates.**

PRICE PERSISTENCE PATH CLOSED UNDER CURRENT YFINANCE DATASET.

The corrected exit2 state machine causes turnover to explode
above the 250% ceiling for all candidates. The exit2 confirmation
mechanism does not control turnover when it actually functions.