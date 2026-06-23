# Price robustness results

> Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.

## Prespecified sensitivities

- **Remove best stock:** FTAI was the largest additive contributor. Removing it
  reduced annualized return from 12.85% to 11.66%; deficits widened to −2.73
  points versus SPY and −3.48 points versus QQQ.
- **Remove best calendar year:** removing 2024 left a four-year total return of
  26.92% (6.14% annualized), versus 56.45% (11.84%) for SPY and 60.67% (12.59%)
  for QQQ.
- **Rank weighting:** annualized return fell to 10.54%, lagging SPY by 3.85
  points and QQQ by 4.59 points. Turnover rose to 973.55% and average top-five
  weight to 32.14%.
- **Current-classification constraints:** the constrained sensitivity returned
  10.80%, −3.59 points versus SPY and −4.33 points versus QQQ, with 703.15%
  turnover. Current classifications remain a non-PIT sensitivity only.

The top five positive stock contributors were FTAI, GE, VST, HWM and POWL and
represented 13.09% of positive stock contribution. The five strongest positive
months represented 30.52% of positive monthly return contribution.

## Drawdown and recovery regimes

| Regime | P4 | SPY | QQQ | Interpretation |
|---|---:|---:|---:|---|
| 2020 COVID drawdown | −42.50% | −33.40% | −27.23% | worse than both |
| 2020 recovery | +50.29% | +52.56% | +63.35% | lagged both |
| 2022 bear phase | −16.41% | −24.06% | −33.65% | defensive relative result |
| post-2022 recovery | +21.25% | +35.95% | +57.37% | materially lagged both |

Seven source series contain an isolated adjusted one-day jump above 500%:
AGX, CHRD, DFTX, HUBB, INDV, TDS and WTRG. They are flagged, not silently
deleted post-result. P4's evaluation attribution is not concentrated in those
names, but the issue further weakens interpretation of the high-return P1–P3
ablations.
