# Private Investment Dashboard — Product Specification

## Product

A private, single-user investment operating dashboard for maintaining personal portfolios aligned with a quantitative stock-selection model. Not a public product. No broker integration.

## Owner

One authenticated user. No public registration, subscriptions, payments or organisations.

## Core functions

### Dashboard
- Combined portfolio value, cash, daily/MTD/QTD/YTD/1yr/since-inception return
- Comparison with official model, SPY and QQQ
- Current drawdown, next quarterly review date
- Model-alignment percentage, unresolved actions, latest data timestamp

### Official model (M1 B2 QUALITY VETO N30)
- Current 30 stocks with scores, ranks, Quality, sector, industry
- Historical quarterly snapshots
- Plain-language inclusion reasons

### Personal portfolios
- Multiple portfolios (live brokerage, retirement, paper, etc.)
- Each with name, currency, opening date, starting cash, benchmark, notes
- Active/archived status

### Transaction ledger
- Immutable source events: buy, sell, dividend, deposit, withdrawal, fee, tax, interest, split, symbol change, merger, spin-off, adjustment
- Holdings derived from transactions, not manual entry
- Reversal/correction events instead of deletion

### Portfolio analytics
- Holdings, average cost, current value, weight, realised/unrealised gain
- TWR, XIRR, volatility, max drawdown, exposure

### Model comparison
- Percentage overlap with model
- Model stocks owned vs missing
- User holdings outside model
- Target-weight difference, sector/industry difference
- Estimated trades for alignment, estimated costs

### Quarterly review workspace
- Retained, new, removed positions
- Current quantities vs targets
- Illustrative buys/sells with cost estimates
- Actual fill-entry workflow
- Completion status

### Performance comparison
- Portfolio vs model vs SPY vs QQQ
- Daily/MTD/QTD/YTD/1yr/since-inception/custom range
- Deposit/withdrawal-aware

### Model publication workflow
- DRAFT → VALIDATED → APPROVED → PUBLISHED → SUPERSEDED
- Python engine generates snapshot; integrity checks run; owner approves

### Data exports
- CSV transactions, holdings, JSON model snapshots, full backup
