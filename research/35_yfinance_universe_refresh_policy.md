# Yfinance prospective universe-refresh policy

**Version:** `YF-REFRESH-1.0.0`  
**Active use:** broker-agnostic simplified forward protocol

The Checkpoint 3 reason-coded state machine remains valid and has no broker/execution dependency.

| Event | Policy |
|---|---|
| Newly eligible | Eligible for the next monthly selection only |
| Screen disappearance; market-cap, price or liquidity failure | Block new purchases after first complete failure; exit after two consecutive complete monthly failures |
| Required statement/category unavailable | Technical endpoint failure pauses new purchases without consuming grace; genuine absence twice requires exit |
| Sector/industry change | Verify and immediately recalculate concentration; correct through contributions or scheduled quarterly review |
| Ticker change/acquisition/stale price/apparent delisting | Immediate manual-review suspension; preserve shares and cash; no fabricated transaction |
| Duplicate issuer/share class | Retain highest market cap, then liquidity, then ticker; archive every decision |
| Verified nonordinary/foreign/non-USD/excluded-sector security | Permanent exclusion and next-valid-session raw-Close exit unless a corporate-action exception controls |

Rank 61 or worse is a normal monthly exit. Eligibility decisions and ranks use only the completed snapshot. Archive before/observation/after/change tables, raw queries, deduplication decisions and checksums every month. A correction creates a new immutable snapshot.

> The paper results exclude commissions, spreads, slippage, taxes, currency conversion, and broker-specific charges.
