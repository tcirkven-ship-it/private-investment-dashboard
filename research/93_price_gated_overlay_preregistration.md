# Price-gated overlay — preregistration

## Models

| ID | Name | Description |
|---|---|---|
| G0 | P100 control | Select top 30 by Price only |
| G1 | Price top-60, Q/V rerank | Restrict to Price top 60; select 30 by 50%P/25%Q/25%V |
| G2 | Price top-90, Q/V rerank | Restrict to Price top 90; select 30 by 50%P/25%Q/25%V |
| G3 | Quality veto | Exclude bottom-10% Quality; select top 30 by Price |
| G4 | Q&V veto | Exclude bottom-10% Q and V; select top 30 by Price |
| G5 | Q/V tie-break | Sort by Price rank; Q/V breaks ties within 10-rank bands |

All use immediate rank-60 exit (no confirmation state), quarterly corrective
rebalance, next-session-close execution, 10bps cost, SPY and QQQ benchmarks.