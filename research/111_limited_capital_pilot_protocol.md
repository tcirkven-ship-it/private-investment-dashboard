# Limited-capital pilot protocol

**Model:** M1 B2 Quality veto
**Status:** ELIGIBLE FOR LIMITED-CAPITAL PILOT WITH TURNOVER-GATE OVERRIDE

## Mechanics

- N=30 equal target weights
- Quarterly reconstruction: last session of March, June, September, December
- Score using data available at that session's close
- Execute at the next valid session close
- Sector cap: 25%, Industry cap: 15%
- Between quarterly rebuilds: trade only for hard eligibility failure
  or corporate-action handling
- No monthly rank-based replacement
- Survivors drift between scheduled reconstructions
- No leverage, no short positions, no options
- 10bps one-way cost estimate

## Capital

The user chooses the initial capital amount and cash reserve.
Target positions are equal-weighted: 1/N of investable capital.

## Data and execution

- Universe: YF-CURRENT-US-NONFINANCIAL-RULE-1.0.0 (1,069 eligible names)
- Price data: yfinance daily adjusted close
- Quality data: annual statements with 3-month publication lag
- Bottom 10% of valid composite Quality scores are excluded from selection
- Stocks with missing Quality remain eligible but are flagged

## Ledgers

Separate immutable live and research ledgers are maintained.
No historical backfilling. No broker connection. No order submission.

## Review

Pilot status should be reviewed after 12 months of operation.