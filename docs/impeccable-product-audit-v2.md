# Impeccable Product Audit — v2

**Generated:** 2026-06-28
**Scope:** All actual routes present in `web/src/app/`, verified from source code

---

## Route Audit

| Route | Purpose | Primary Action | Empty State | Data State | Error State | Real Supabase | Mock/Fake Data | Owner-only | Navigation Path | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| `/login` | Email/password login form | Sign in with credentials | N/A (form always visible) | Email + password inputs, Sign in button | Red inline error card with Supabase error message | Yes — `signIn` calls Supabase Auth | Placeholder `you@example.com` on email input (cosmetic) | No | Middleware redirects unauthenticated users here | **Keep** |
| `/dashboard` | Main overview: portfolio count, model status, portfolio list | Generate model or create first portfolio | "Getting Started" cards + "No portfolios yet" / "No model imported yet" | Portfolio count, model status, holdings count, portfolio card list | Red error card with detail message | Yes — reads portfolios, model snapshots, model counts | Generate/Refresh button calls `importM1B2Model` which inserts hardcoded tickers (AAPL/MSFT/GOOGL/NVDA/…) with synthetic scores | No | Default route after login | **Keep** |
| `/model` | Current model snapshot with 30-stock holdings table | View/Generate Quarterly Top 30 model | "No model snapshot imported yet." + CTA to generate | Status cards (model ID, effective date, holdings count, status) + ranked holdings table with ticker, company, sector, target weight, B2 score, quality percentile | Red error card | Yes — `getLatestModelSnapshot` from Supabase | Generate button calls `importM1B2Model` (seed function); DRAFT status banner shown when not published | No | Sidebar "Quarterly Top 30" | **Keep** |
| `/model/history` | Historical quarterly snapshot list | Browse past snapshots | "No snapshots imported yet." + hint to import | List of snapshots: effective date, status badge, snapshot ID | Red error card | Yes — `loadModelHistory` from Supabase | None | No | Back-link from `/model` page | **Keep** |
| `/portfolios` | List of user's portfolios | Navigate to a portfolio or create new | "No portfolios yet. Create your first one." link | Grid of portfolio cards: name, opening date, archived badge, arrow icon | None explicit (falls through to empty state on error) | Yes — reads portfolios table scoped to `owner_id` | None | No | Sidebar "My Portfolio" | **Keep** |
| `/portfolios/new` | Create portfolio form | Submit name + currency to create portfolio | N/A (form always visible) | Name input, currency select, Create button | Red inline error bar above form | Yes — `createPortfolio` server action inserts into portfolios table | Placeholder `Main Brokerage` on name input (generic artifact) | No | From dashboard or portfolios list | **Keep** (fix placeholder) |
| `/portfolios/[id]` | Portfolio overview hub with tab navigation | Navigate to holdings, transactions, performance, rebalance | Tab bar visible; body shows "Select a tab above to view details." | Portfolio name, opening date, delete button, 5-tab navigation bar | 404 via `notFound()` if portfolio missing | Yes — reads single portfolio row | None | No | From portfolios list card | **Keep** |
| `/portfolios/[id]/holdings` | Current holdings with computed market values and P&L | View position-level weights and unrealized P&L | "No holdings. Add transactions on the Transactions page." | Metric cards (Cash, Invested, Realized P/L, Dividends) + holdings table (ticker, qty, avg cost, price, mkt value, unrealized, weight) | Red error card | Yes — reads transactions + price_observations, client-side derivation via `deriveHoldings` | None derived at page level; prices from Supabase (may be missing) | No | Tab from portfolio detail | **Keep** |
| `/portfolios/[id]/transactions` | Transaction ledger form + table | Add a new transaction | "No transactions yet. Add your first deposit or trade below." | Transaction table (date, type, ticker, qty, amount, fee) + transaction form at bottom | Red error card | Yes — reads/writes transactions via `loadTransactions` and `insertTransaction` server action | Placeholder `AAPL` on ticker input (cosmetic artifact) | No | Tab from portfolio detail | **Keep** (fix placeholder) |
| `/portfolios/[id]/performance` | Portfolio return metrics vs SPY/QQQ benchmarks | View simple return and benchmark comparison | Always renders; shows zeros if no data | Returns panel (Simple Return, SPY, QQQ) + Account panel (NAV, Deposits, Realized P/L, Dividends) + note about TWR/XIRR unavailability | Red error card | Yes — `loadHoldings` + `loadBenchmarkReturns` from Supabase | None; falls back to null/0 when no benchmark data | No | Tab from portfolio detail | **Keep** |
| `/portfolios/[id]/rebalance` | Compare current holdings to published model target weights | View buy/sell/add/reduce/hold instructions | "No Quarterly Top 30 generated yet" or "No portfolio holdings yet." | Comparison table: ticker, current %, target %, action badge; amber banner if prices unavailable | Red error card | Yes — reads published model snapshot + holdings/transactions | None; purely computational from real data | No | Tab from portfolio detail | **Keep** |
| `/admin/model-import` | Upload a model JSON snapshot file | Select and import a JSON file | Drop zone for file selection | File name shown in drop zone; preview card with snapshot ID, effective date, holdings count, model ID; "Import as Draft" button | None explicit | **No** — import is simulated via `setTimeout(resolve, 1000)` with hardcoded success message | **Entire import flow is fake** — no Supabase insert, no validation, no reviewer assignment | Not guarded (route exists but not in sidebar) | Orphan — no navigation link | **Redesign** — implement real Supabase insert or remove |
| `/admin/model-review` | Review and approve/reject draft model snapshots | Validate or approve a draft | "No draft snapshots to review. Import one first." | Draft list (clickable cards) → review detail (snapshot ID, effective date, eligible count, integrity hash, schema/integrity/holdings checks, Validate/Approve/Reject buttons) | None explicit; action result shown as green success card | **No** — uses `useState` with hardcoded draft data | **Completely fake** — hardcoded `{ id: "draft-1", snapshot_id: "2026-09-30T160000Z", status: "DRAFT", ... }`; all state transitions are local-only, no Supabase writes | Yes — sidebar shows "Model Review" only if `isOwner === true` from profiles table | Sidebar "Model Review" (owner only) | **Redesign** — connect to real Supabase model_snapshots table |
| `/settings` | Account info, preferences, data management, admin tools | View settings (all buttons are non-functional shells) | N/A (always shows cards) | Account card ("owner@example.com", MFA not enabled), Preferences (currency/benchmark selects), Data Management (export/import/refresh buttons), Admin (backup/restore buttons) | None | **No** — pure client-side `useState` with hardcoded defaults | Hardcoded email `owner@example.com`; all buttons are no-op; preferences are state-only | No | Not in sidebar (orphan route) | **Redesign** — connect to real auth/user data, implement button actions, add to sidebar |
| `/analytics` | Cross-portfolio analytics (stub) | None — automatic redirect to /dashboard | N/A | N/A | N/A | No | None | No | Orphan — no navigation link | **Hide** — remove route or implement |
| `/api/dashboard` | JSON API endpoint for dashboard data | Return portfolio count + model published status | Returns `{ portfolioCount: 0, modelPublished: false, totalValue: null, cash: null }` | Returns `{ portfolioCount, modelPublished, totalValue, cash }` | Returns `401 { error: "Not authenticated" }` | Yes — reads portfolios and model_snapshots | None (always returns null for totalValue/cash) | No | API route (not user-facing) | **Keep** |
| `/` (root) | Redirect router | Redirects to /dashboard (authenticated) or /login (unauthenticated) | N/A | N/A | N/A | Yes — checks Supabase auth | None | No | Root URL | **Keep** |

---

## Generic Artifacts Report

The following search strings were checked across the entire codebase (excluding `node_modules`, `.git`, `outputs`, `research`, `data`):

| Search Term | Occurrences | File(s) & Line(s) | Verdict |
|---|---|---|---|
| `Retirement` | 0 | — | Clean |
| `Main Brokerage` | 1 | `web/src/app/(app)/portfolios/new/page.tsx:50` — placeholder text on name input | **Remove** — replace with generic placeholder like "My Portfolio" |
| `Paper Account` | 0 | — | Clean |
| `Test Name` | 0 | — | Clean |
| `SSSS` | 0 | — | Clean |
| `\bTT\b` (word boundary) | 0 | — | Clean |
| `MOCK_DATA` | 0 | — | Clean |
| `owner@example.com` | 1 | `web/src/app/(app)/settings/page.tsx:20` — hardcoded email in Account card | **Remove** — fetch real email from Supabase auth session |
| `AAPL`/`MSFT`/`GOOGL` in model seed/hardcoded data | Multiple | `web/src/lib/actions.ts:18-19` — hardcoded 30-ticker array in `importM1B2Model`; `web/src/lib/actions.ts:219` — hardcoded list in `seedAcceptanceData`; `web/src/lib/actions.ts:257-259` — hardcoded BUY transactions (AAPL/MSFT/GOOGL) in `seedAcceptanceData`; `web/src/components/portfolios/TransactionForm.tsx:87` — placeholder "AAPL" | **Cosmetic fix** for TransactionForm placeholder. The seed functions (`importM1B2Model`, `seedAcceptanceData`) are intentional test/demo helpers and are labelled as such — keep but consider gating behind owner-only or environment flag |
| `sample`/`hardcoded` in fake-value context | Multiple | `web/src/app/(app)/admin/model-review/page.tsx:19-21` — hardcoded draft snapshot data; `web/src/app/(app)/admin/model-import/page.tsx:33-34` — simulated import with setTimeout | **Redesign both admin routes** — replace fake data with real Supabase queries |
| `mock`/`fake` in test infrastructure | 38 | `web/src/lib/__tests__/route-loaders.test.ts` — `fakeDb`/`mockDb` test helpers; `web/src/lib/adapters.test.ts` + `web/src/lib/holdings.test.ts` — test data | **Acceptable** — test infrastructure, not visible to users |
| `starting_cash` / `starting cash` in UI form field | 0 | No UI form fields contain starting_cash input | Clean — starting_cash is only read from DB (`dashboard/page.tsx:23`, `DashboardClient.tsx:102,183`) or set in seed functions (`actions.ts:249`) or Python backtest (`shadow_system.py:102,129,140`) |

### Summary of items needing action

1. **`owner@example.com`** in `settings/page.tsx:20` — hardcoded email, must fetch from auth
2. **`Main Brokerage`** placeholder in `portfolios/new/page.tsx:50` — generic artifact, replace
3. **`AAPL`** placeholder in `TransactionForm.tsx:87` — generic artifact, replace with "e.g. AAPL" or remove
4. **`admin/model-import`** and **`admin/model-review`** — fully fake/mock, need redesign with real Supabase integration
5. **`settings`** page — all no-op buttons, needs real functionality
6. **`analytics`** route — empty redirect stub, remove or implement

---

## Route Status Summary

| Status | Count | Routes |
|---|---|---|
| **Keep** — fully functional with real Supabase | 12 | `/login`, `/dashboard`, `/model`, `/model/history`, `/portfolios`, `/portfolios/new`, `/portfolios/[id]`, `/portfolios/[id]/holdings`, `/portfolios/[id]/transactions`, `/portfolios/[id]/performance`, `/portfolios/[id]/rebalance`, `/` |
| **Redesign** — fake/mock data, no real Supabase | 3 | `/admin/model-import`, `/admin/model-review`, `/settings` |
| **Hide** — stub with no implementation | 1 | `/analytics` |
| **Keep** — API route | 1 | `/api/dashboard` |

**Total routes audited:** 17 (16 pages + 1 API)
