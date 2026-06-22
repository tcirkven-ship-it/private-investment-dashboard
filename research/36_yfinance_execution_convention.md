# Yfinance paper execution convention

> **Superseded without activation.** This intraday convention is retained for audit history only. The active broker-agnostic daily convention is `research/42_simplified_daily_execution.md`.

**Version:** `YF-EXEC-1.0.0` / `YF-COST-1.0.0`  
**Status:** frozen for rehearsal, not activated

## Intraday feasibility smoke test

Six securities—SPY, QQQ, NTCT, CRUS, EIX, and CALM—were retrieved through yfinance without examining strategy returns. The immutable corrected snapshot is `data/raw/yfinance_phase1b_checkpoint3/intraday_smoke/2026-06-22T_readiness_v2Z`.

| Interval | Observed sessions | 15:45–15:55 window | Missing OHLC in window | Size, six tickers | Decision |
|---|---:|---:|---:|---:|---|
| 1 minute | 7 | Present | 11 rows | 1.66 MB | Reject: short retention and window gaps |
| 5 minutes | 60 | Three bars/session | 0 rows | 3.32 MB | **Select** |
| 15 minutes | 60 | One bar/session | 0 rows | 1.12 MB | Reject: cannot resolve a ten-minute order lifecycle |

Five-minute data are not assumed permanent. Each decision-day window must be archived immediately; missing data mean unfilled, not reconstructed from daily or adjusted prices.

## Frozen order convention

- Submit a paper fractional limit order at 15:45 America/New_York during the next eligible regular session.
- Reference price is raw `Close` of the first complete 5-minute bar at or after 15:45.
- Buy limit = reference × 1.001; sell limit = reference × 0.999, rounded to four decimals.
- The limit must be crossed by an archived 5-minute bar through 15:55 inclusive.
- On the first crossed bar, fill at most 1% of that archived 5-minute bar's volume; expire and cancel the remainder at 15:55. Missing bar volume means unfilled. Never assume the remainder fills.
- Missing, stale, duplicate, timezone-ambiguous, or incomplete window data produce an unfilled flag.
- One new next-session retry is allowed only for a mandatory exit or a previously approved contribution order. It requires a new order ID; no retrospective fill.
- Raw Close values position holdings. Adjusted Close is prohibited for orders and valuation.
- Expected adverse-price allowance is 5 bps; stressed is 15 bps. A fill may not be worse than the limit.

## Commission convention and blocker

The planning model uses IBKR Pro Tiered US pricing: USD 0.0035 per whole share, USD 0.35 minimum and 1% trade-value cap. The official page states fractional trades use the same schedule unless noted and charges fractional trades the greater of 1% of trade value or USD 0.01. [Interactive Brokers official commission schedule](https://www.interactivebrokers.com/en/pricing/commissions-stocks.php?re=amer).

The same official schedule says Tiered pricing also has exchange, clearing, regulatory, and pass-through fees. Those venue-dependent fees are not yet frozen in the ledger. This is an activation blocker, even though the rehearsal uses the explicit base-commission and adverse-price model consistently.
