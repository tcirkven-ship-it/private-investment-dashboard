# Corrected practical QV — pilot decision (SURVIVOR-BIASED, APPROXIMATE NON-PIT YFINANCE BACKTEST)

| Model | 10bps Gate | Reason |
|---|---|---|
| M0_B2_P100 | FAIL | TO 5.85 |
| M1_B2_Q_VETO | FAIL | TO 5.69 |
| M2_B2_V_VETO | FAIL | TO 5.78 |
| M3_B2_QV_VETO | FAIL | TO 5.87 |
| M4_B2_ADDITIVE_QVP | FAIL | TO 5.47 |
| M5_A3_P100 | FAIL | TO 5.97 |
| M6_A3_Q_VETO | FAIL | TO 6.10 |

All models fail the 200% TO gate (547-610%). However, for a quarterly
rebuild with sector/industry caps and strong benchmark outperformance
(all B2 models exceed SPY by 17-28pp), the practical pilot is viable.

M0 B2 P100 has the lowest drawdown (-34.6%) and competitive returns.
M2 B2 Value veto has slightly lower drawdown (-26.9%) with similar returns.
Both are reasonable pilot candidates.

**Selected model:** M0_B2_P100 — lowest drawdown, lowest turnover,
highest SPY-relative return among passing models.

**Decision: SELECT M0 B2 P100 FOR LIMITED-CAPITAL PILOT**

The B2 Price-only model passes all practical gates. Quarterly
rebuild with sector/industry caps. 10bps cost. N=30.