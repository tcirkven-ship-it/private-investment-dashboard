# Execution timing and IBKR practicality

**Verified:** 2026-06-21  
**Status:** Practical review; no live orders authorized

## Current official facts

- IBKR Pro tiered US-stock pricing begins at USD 0.0035 per share with a USD 0.35 minimum per order; fixed pricing is USD 0.005 per share with a USD 1.00 minimum. Fractional and whole-share commissions generally follow the same schedule. Source: https://www.interactivebrokers.com/en/pricing/commissions-stocks.php?re=amer
- IBKR advertises fractional ownership in eligible US stocks and ETFs starting at USD 1. Source: https://www.interactivebrokers.com/en/?f=45718
- IBKR's Market-on-Close lesson says fractional shares are not supported for MOC orders and notes Nasdaq and NYSE MOC cutoff times of 3:55 p.m. and 3:50 p.m. ET. Source: https://www.interactivebrokers.com/campus/trading-lessons/ibkr-desktop-market-on-close-order/
- A Limit-on-Close order executes only if the closing price satisfies the limit and otherwise may be cancelled. Source: https://www.interactivebrokers.com/campus/glossary-terms/limit-on-close-order/

IBKR Lite is not assumed because it is restricted by residence/account eligibility. The expected case therefore uses the USD 0.35 IBKR Pro minimum.

## Modeled convention

Signals are calculated after month-end close and filled at the next trading session's adjusted close with adverse price impact. Weekly contributions use the most recent frozen target list. This prevents same-close look-ahead, but adjusted-close fills remain a research proxy rather than a guarantee of attainable execution.

## Practical conclusion

Exact weekday or minute was not treated as alpha. Weekly, biweekly, and monthly contribution schedules produced nearly identical return rates; monthly aggregation reduced modeled costs and manual work.

If this strategy were ever re-researched successfully, fractional trades should use patient regular-hours limit orders or carefully controlled marketable limits, not fractional MOC. Unfilled limits must remain cash and may not be assumed executed retrospectively.

The tested C03-M portfolio generated approximately 6,352 orders/trades over the stitched period and about 178% annualized discretionary turnover. That burden is inconsistent with the intended simple manual strategy.

