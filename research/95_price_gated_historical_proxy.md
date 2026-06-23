# QVP Integration — corrected historical P100 baselines

## Simulator audit result

The historical P100 simulator was corrected:
- Immediate rank-60 exit (no state machine).
- Holding period tracking implemented (was showing NaN/0).
- Turnover matches corrected Price persistence results.

| Backbone | Period | Ann ret | SPY-rel | QQQ-rel | Vol | Max DD | TO | Avg hold (days) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A3 | dev2015_2020 | +25.0666% | +12.3963% | +3.6427% | +28.0717% | -45.5314% | 6.18 | 94 |
| A3 | eval2021_2025 | +39.1942% | +24.7981% | +24.0575% | +42.4713% | -36.4221% | 6.36 | 87 |
| B2 | dev2015_2020 | +26.4017% | +13.7314% | +4.9778% | +27.2820% | -43.0568% | 5.52 | 101 |
| B2 | eval2021_2025 | +40.6053% | +26.2091% | +25.4686% | +41.4443% | -36.3017% | 5.25 | 101 |

## Historical QVP proxy

NOT COMPUTED — requires dedicated statement-extraction infrastructure.
The gated overlay model definitions are frozen and ready for historical
computation in a follow-up task. The current comparison is cross-sectional only.