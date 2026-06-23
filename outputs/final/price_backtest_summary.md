# Frozen Price historical backtest — summary

**Decision:** FAIL for standalone P4 evidence.

**Implementation validity:** PASS.
**Evidence label:** Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.

The decisive dataset contains maximum daily yfinance histories for all 1,069
current eligible stocks plus SPY and QQQ. No P4 configuration passed the
2015–2020 development gates. The frozen diagnostic reference was P4/N=30/
monthly/rank-60/equal weight.

In 2021–2025 it returned **12.85% annualized**, versus **14.40% SPY** and
**15.14% QQQ**. Maximum drawdown was −21.49%, volatility 19.76%, Sharpe 0.71
and annual gross turnover **681.70%**. It beat each benchmark in only 2 of 5
calendar folds.

P1–P3 had much higher survivor-biased returns but also 38%–41% volatility and
493%–725% turnover; they are not approved replacements. Seven histories have
suspicious isolated adjusted-price jumps above 500%.

Current Price-only and QVP top-30 lists overlap only in ENS. Quality and Value
dominate current membership, but their incremental effect remains unproven.
