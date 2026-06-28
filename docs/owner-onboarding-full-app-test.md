# Owner Onboarding — Full App Acceptance Test

## Starting from Empty Database

After signing in as the owner (first user), the dashboard shows:

- Empty state with **Getting Started** actions
- **Create Portfolio** button → `/portfolios/new`
- **View Model** button → `/model`
- **Seed Test Data** button (owner-only) → creates a full acceptance test dataset

## Creating Test Data

### Option A — Seed Button (Recommended)

Click **Seed Test Data** on the dashboard. This creates:

| Object | Details |
|--------|---------|
| Portfolio | `[TEST] Acceptance Portfolio` with $100,000 starting cash |
| Securities | 30 stocks (AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, JPM, V, WMT, JNJ, PG, MA, UNH, HD, DIS, BAC, PFE, CSCO, XOM, ABNB, ADBE, NFLX, CRM, INTC, AMD, BA, GE, CAT, IBM) |
| Transactions | DEPOSIT $100,000 + 10 BUY transactions |
| Price observations | Latest close prices for all 30 securities |
| Benchmark observations | SPY and QQQ weekly data (60 weeks) |
| Model snapshot | Published `[TEST] Acceptance test model` with 30 equal-weight holdings |
| Warnings | All test data includes `acceptance-test` or `[TEST]` labels |

**Idempotent**: Safe to run once. A second call returns "Test data already exists."

### Option B — Manual

1. Create portfolio at `/portfolios/new`
2. Add deposit transaction on portfolio's Transactions tab
3. Add buy transactions with ticker symbols
4. Import a model snapshot JSON at `/admin/model-import`
5. Review and publish at `/admin/model-review`

## Running the Full Smoke Test

After seeding test data, verify the following pages:

### Expected Results

| Page | Expected Result |
|------|----------------|
| `/dashboard` | Shows portfolio count (1), model status (Published). No fake values. |
| `/portfolios` | Shows `[TEST] Acceptance Portfolio` with test label |
| `/portfolios/[id]` | Portfolio detail with name, dates, notes |
| `/portfolios/[id]/holdings` | Holdings list from 10 buy transactions |
| `/portfolios/[id]/transactions` | 11 transactions (1 deposit + 10 buys) |
| `/portfolios/[id]/performance` | Page loads (may show empty if no valuation data) |
| `/portfolios/[id]/rebalance` | Comparison between portfolio holdings and model targets |
| `/model` | Published model with 30 holdings, ranked with weights |
| `/model/history` | Model snapshot history with dates and status |

### Identifying Test Data

All test data is clearly labeled:
- Portfolio name: `[TEST] Acceptance Portfolio`
- Model version description: `[TEST] Acceptance test model — not an investment recommendation`
- Model snapshot ID: `acceptance-test-*`
- Price observation source: `acceptance-test`
- Inclusion reason: `[TEST] Acceptance test`

**This is not real investment data. Do not make investment decisions based on this data.**

## What Is Still Not Production-Ready

- Performance page: requires portfolio_valuations data
- Full real-time price data: requires external data feed connection
- Broker connection: not implemented
- Order execution: not implemented
- Multi-currency support: USD only
- Real model snapshots: require Python research engine output

## Owner-Only Safety

All seed/creation actions verify `profiles.is_owner = true`:
- Anonymous users are redirected to login via middleware
- Non-owner authenticated users see access-denied states
- Admin pages check owner status on the server
- RLS policies enforce owner-level data isolation

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Seed button not visible | Only the owner (first user) can see it |
| "Test data already exists" | Delete the test portfolio or rename |
| Holdings show zero | Add price observations for the securities |
| Rebalance shows no comparison | Both portfolio and model must exist |
| Model page shows empty | Run seed or import/publish a model |
