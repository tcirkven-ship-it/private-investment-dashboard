# Product Requirements Reset Report

> Status: `PRODUCT REQUIREMENTS RESET READY — USER REVIEW REQUIRED`

---

## 1. Original Product Goal

Private, single-owner investment dashboard for managing personal portfolios aligned with the **M1_B2_QUALITY_VETO_N30** quantitative stock-selection model. Manual entry only. No broker connection. No automatic orders. No public users.

## 2. Approved Model Mechanics

| Parameter | Value |
|-----------|-------|
| Model ID | `M1_B2_QUALITY_VETO_N30` |
| Holdings | 30 stocks |
| Allocation | Equal weight (3.3333% each) |
| Sector cap | 25% |
| Industry cap | 15% |
| Rebalance | Quarterly, after final sessions of March, June, September, December |
| Execution | Next valid session close, manual only |
| Source engine | Python research scanner |
| Integrity | Model integrity manifest with checksums |
| Classification | Decision support only — not investment advice |

### Official Top 30 (source: `outputs/final/m1_b2_quality_veto_targets.csv`)

| Rank | Ticker | Company (from research data) | Sector | Target % |
|------|--------|---------------------------|--------|----------|
| 1 | MU | Micron Technology | Technology | 3.3333 |
| 2 | DOCN | DigitalOcean | Technology | 3.3333 |
| 3 | BE | Bloom Energy | Industrials | 3.3333 |
| 4 | VICR | Vicor Corp | Technology | 3.3333 |
| 5 | TTMI | TTM Technologies | Technology | 3.3333 |
| 6 | MXL | MaxLinear | Technology | 3.3333 |
| 7 | WDC | Western Digital | Technology | 3.3333 |
| 8 | SYRE | Spyre Therapeutics | Healthcare | 3.3333 |
| 9 | POWL | Powell Industries | Industrials | 3.3333 |
| 10 | STRL | Sterling Infrastructure | Industrials | 3.3333 |
| 11 | AMD | AMD | Technology | 3.3333 |
| 12 | AGX | Argan Inc | Industrials | 3.3333 |
| 13 | GTX | Garrett Motion | Consumer Cyclical | 3.3333 |
| 14 | MYRG | MYR Group | Industrials | 3.3333 |
| 15 | FIX | Comfort Systems USA | Industrials | 3.3333 |
| 16 | MTRN | Materion | Basic Materials | 3.3333 |
| 17 | ELVN | Enliven Therapeutics | Healthcare | 3.3333 |
| 18 | VRT | Vertiv | Industrials | 3.3333 |
| 19 | BTSG | BrightSpring Health | Healthcare | 3.3333 |
| 20 | KGS | Kodiak Gas Services | Energy | 3.3333 |
| 21 | MOD | Modine Manufacturing | Consumer Cyclical | 3.3333 |
| 22 | INSW | International Seaways | Energy | 3.3333 |
| 23 | SPHR | Sphere Entertainment | Communication Services | 3.3333 |
| 24 | IRDM | Iridium Communications | Communication Services | 3.3333 |
| 25 | TXG | 10x Genomics | Healthcare | 3.3333 |
| 26 | TWST | Twist Bioscience | Healthcare | 3.3333 |
| 27 | WTTR | Select Water Solutions | Energy | 3.3333 |
| 28 | EWTX | Edgewise Therapeutics | Healthcare | 3.3333 |
| 29 | COCO | Vita Coco | Consumer Defensive | 3.3333 |
| 30 | KALU | Kaiser Aluminum | Basic Materials | 3.3333 |

**Model status**: The latest snapshot (`2026-06-24T080500Z`) exists in research outputs. It has NOT been imported into the Supabase dashboard. The seed acceptance-test data used 30 wrong tickers (AAPL, MSFT, etc.) that are NOT in this model.

## 3. Source-of-Truth Findings

| Question | Answer |
|----------|--------|
| Accepted official model | `M1_B2_QUALITY_VETO_N30` — confirmed in `docs/private_dashboard_data_contracts.md` and `outputs/final/m1_b2_quality_veto_targets.csv` |
| Top 30 source | `outputs/final/m1_b2_quality_veto_targets.csv` (explicit approved model) — NOT the daily YF-QVP runs |
| Exact 30 tickers | Listed above — includes MU, DOCN, BE, etc. (NOT AAPL, MSFT, GOOGL) |
| Target weights | Equal weight 3.3333% each |
| Model status in dashboard | **Not imported** — seed test data used wrong tickers |

## 4. Route-by-Route Product Audit

### `/dashboard`
- **Purpose**: Overview of portfolio value, model alignment, next review date
- **Current state**: Shows portfolio count and model status. Empty state has CTAs. Portfolio cards show links.
- **Issues**: 
  - Can show `[TEST] Acceptance Portfolio` which uses wrong tickers
  - Does not show model alignment %, unresolved actions, review date
  - No real data from Supabase (zero rows)
- **Fix needed**: Connect to real loaders; show model-first; show actionable quarterly review info

### `/model`
- **Purpose**: Display published M1_B2_QUALITY_VETO_N30 with 30 holdings
- **Current state**: Uses route-loaders which query Supabase `model_snapshots`
- **Issues**: No model data loaded; seed test model used wrong tickers
- **Fix needed**: Load the actual Top 30 from the research output file

### `/model/history`
- **Purpose**: Historical quarterly snapshots
- **Current state**: Uses route-loader, queries Supabase
- **Issues**: No real history loaded
- **Fix needed**: Import historical snapshots

### `/portfolios`
- **Purpose**: List owner's portfolios
- **Current state**: Functional but shows `[TEST] Acceptance Portfolio` if seeded
- **Issues**: Test data needs clear labeling
- **Fix needed**: Ensure test data is clearly marked

### `/portfolios/[id]`
- **Purpose**: Portfolio detail
- **Current state**: Bare-bones; needs real data
- **Issues**: No ownership verification; no real calculated values

### `/portfolios/[id]/holdings`
- **Purpose**: Holdings derived from transactions
- **Current state**: Uses route-loaders
- **Issues**: Zero real data; holdings engine is unit-tested but not integration-tested

### `/portfolios/[id]/transactions`
- **Purpose**: Transaction ledger
- **Current state**: Uses route-loaders
- **Issues**: Functional but no real data

### `/portfolios/[id]/performance`
- **Purpose**: Performance comparison
- **Current state**: Uses route-loaders
- **Issues**: No valuation data → empty state (acceptable)

### `/portfolios/[id]/rebalance`
- **Purpose**: Quarterly review comparison
- **Current state**: Uses route-loaders
- **Issues**: No real data; needs model + holdings + prices to work

### `/admin/model-import`
- **Purpose**: Import model JSON from Python engine
- **Current state**: UI exists, backend persistence needs to be connected
- **Issues**: Stub implementation

### `/admin/model-review`
- **Purpose**: DRAFT → VALIDATED → APPROVED → PUBLISHED workflow
- **Current state**: UI with mock data
- **Issues**: Uses hardcoded sample draft

### `/settings`
- **Purpose**: Account settings
- **Current state**: Placeholder page

### `/login`
- **Purpose**: Auth
- **Current state**: Functional with middleware redirect

## 5. Wrong/Generic Items to Remove

| Item | Location | Action |
|------|----------|--------|
| `[TEST] Acceptance Portfolio` | Seed data / Supabase | Keep but clearly mark as test; add delete ability |
| Wrong seed tickers (AAPL, MSFT, etc.) | `seedAcceptanceData` action | Replace with actual M1_B2 model tickers |
| `SSSS`, `TT`, `Test Name` portfolios | User-created in Supabase | Let user manage — not app-generated |
| `Retirement`, `Growth`, `Income` etc. | N/A — not present | Do not add |
| Model review mock data | `model-review/page.tsx` | Replace with real Supabase queries |
| Default Next.js starter page | `old page.tsx` | Already removed ✅ |
| `MOCK_DATA` in DashboardClient | Removed in PR #13 | Already fixed ✅ |

## 6. New Information Architecture

The app should be organized around these owner tasks in priority order:

1. **Official Model** (`/model`) — Primary screen. Shows current 30 holdings with scores, ranks, target weights, sector/industry, quality flags. Status badge (DRAFT→PUBLISHED). Next review date.

2. **Dashboard** (`/dashboard`) — Summary of portfolio value, cash, model alignment %, next review date, unresolved rebalance actions.

3. **Portfolios** (`/portfolios`) — List of user's portfolios with links to detail/holdings/transactions/rebalance.

4. **Quarterly Review / Rebalance** (`/portfolios/[id]/rebalance`) — Comparison of current holdings vs model targets. Add/reduce suggestions. Manual decision status. Execution tracking.

5. **Transaction Ledger** (`/portfolios/[id]/transactions`) — Immutable event log. Add transaction form.

6. **Holdings** (`/portfolios/[id]/holdings`) — Derived from transactions + prices.

7. **Performance** (`/portfolios/[id]/performance`) — Chart/table of returns vs model vs SPY vs QQQ.

8. **Admin** (`/admin/*`) — Owner-only. Model import, model review, data management.

## 7. Impeccable Checklist

- [ ] Every route has a clear purpose and primary action
- [ ] Empty states are truthful and come from real queries
- [ ] Loading states show skeletons, not spinners
- [ ] Error states show actionable messages, not stack traces
- [ ] Navigation is consistent and predictable
- [ ] Labels are understandable to a nontechnical owner
- [ ] No mock/fake/hardcoded financial values
- [ ] Test data is clearly labeled `[TEST]`
- [ ] Owner-only actions are guarded
- [ ] Responsive layout works on desktop and tablet
- [ ] Dark theme is consistent

## 8. Implementation Plan (Separate PR)

1. **Fix seed data**: Update `seedAcceptanceData` to use the actual M1_B2 Top 30 tickers from `outputs/final/m1_b2_quality_veto_targets.csv`
2. **Add model import from research output**: Create a server action to import the Top 30 CSV into Supabase as a model snapshot
3. **Improve model page**: Show model name, status, effective date, 30 holdings with scores
4. **Improve dashboard**: Show model alignment, next review date, pending actions
5. **Add test data management**: Add delete/clear test data function
6. **Fix admin pages**: Connect to real Supabase data
7. **Route protection**: Add owner verification to admin routes

## 9. Open Questions for User

1. Should the seed test data use the actual M1_B2 model tickers or should I create a separate test-model snapshot?
2. Should the dashboard show the model page as the primary landing page instead of the current dashboard?
3. The portfolio creation page asks for `starting_cash` — should this be linked to an initial DEPOSIT transaction automatically?
4. Performance page needs `portfolio_valuations` — should these be calculated on-demand or stored as snapshots?
5. Should the `/admin` routes be hidden from the sidebar for non-owners?

---

## Conclusion

```
╔══════════════════════════════════════════════════════════════════╗
║  PRODUCT REQUIREMENTS RESET READY — USER REVIEW REQUIRED        ║
║                                                                  ║
║  Official Top 30 found in:                                      ║
║    outputs/final/m1_b2_quality_veto_targets.csv                 ║
║                                                                  ║
║  Key finding: Seed test data used wrong tickers entirely.       ║
║  The M1_B2 model contains stocks like MU, DOCN, BE, VICR —     ║
║  not AAPL, MSFT, GOOGL as the seed data had.                    ║
║                                                                  ║
║  Next: User review of this report, then separate PR for fixes.  ║
╚══════════════════════════════════════════════════════════════════╝
```
