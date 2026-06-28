# Impeccable Simplified MVP Audit

> Applied: Route-by-route product/UX audit for simplified single-portfolio MVP.

---

## Remaining Screens

### Dashboard (`/dashboard`)

| Attribute | Assessment |
|-----------|-----------|
| Purpose | Show model status, portfolio summary, next action |
| Primary action | Generate Quarterly Top 30 / Create portfolio / View rebalance |
| Empty state | "Generate this quarter's Top 30" or "Create your portfolio" |
| Data state | Model card (M1_B2, status, date, 30 holdings) + portfolio card |
| Error state | Error card with message |
| Navigation | Sidebar → Dashboard |
| Generic features removed | ✅ No sample portfolios, no fake values |
| Verdict | **KEEP** |

### Quarterly Top 30 (`/model`)

| Attribute | Assessment |
|-----------|-----------|
| Purpose | Display the M1_B2_QUALITY_VETO_N30 model with 30 holdings |
| Primary action | Generate/refresh model |
| Empty state | "No model generated yet. Click Generate to create the Quarterly Top 30." |
| Data state | 30 holdings table with rank, ticker, target weight, sector, score |
| Owner-only action | Generate/Refresh Quarterly Top 30 button |
| Verdict | **KEEP** |

### My Portfolio (`/portfolios`)

| Attribute | Assessment |
|-----------|-----------|
| Purpose | Show one active portfolio, or create one |
| Primary action | View portfolio detail / Create portfolio |
| Verdict | **KEEP** — simplified to single portfolio |

### Create Portfolio (`/portfolios/new`)

| Attribute | Assessment |
|-----------|-----------|
| Fields | Name + base currency only (no starting cash) |
| Verdict | **KEEP** — simplified |

### Portfolio Detail (`/portfolios/[id]`)

| Attribute | Assessment |
|-----------|-----------|
| Purpose | Portfolio overview with links to transactions, rebalance, performance |
| Verdict | **KEEP** |

### Transactions (`/portfolios/[id]/transactions`)

| Attribute | Assessment |
|-----------|-----------|
| Purpose | Manual ledger entries |
| Verdict | **KEEP** |

### Rebalance Instructions (`/portfolios/[id]/rebalance`)

| Attribute | Assessment |
|-----------|-----------|
| Purpose | Compare portfolio vs Top 30 model, show buy/sell/add/reduce/hold |
| Verdict | **KEEP** — core feature |

### Performance (`/portfolios/[id]/performance`)

| Attribute | Assessment |
|-----------|-----------|
| Purpose | Show returns from real data |
| Empty state | "Performance unavailable until prices are added." |
| Verdict | **KEEP** |

---

## Removed/Hidden

| Route | Reason |
|-------|--------|
| `/admin/model-import` | Hidden — generic import replaced by Generate button |
| `/admin/model-review` | Hidden — status flow simplified |
| `/model/history` | Hidden — not needed for MVP |
| `/settings` | Hidden — not useful for MVP |
| `/analytics` | Hidden — not useful for MVP |

## Generic Features Removed

| Feature | Location | Action |
|---------|----------|--------|
| Starting cash field | Portfolio creation | Removed |
| `Retirement`, `Main Brokerage`, `Paper Account` | Not in code | Confirmed absent |
| Settings page | Sidebar | Removed from nav |
| Model history nav item | Sidebar | Removed |
| Official Model label | Sidebar | Renamed to "Quarterly Top 30" |
| Generic import UI | Admin | Replaced by Generate button |
| Multiple portfolio complexity | UX | Simplified to single portfolio focus |
