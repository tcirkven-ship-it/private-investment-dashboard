# Private Investment Dashboard — Implementation Backlog

## Phase 0 — Architecture and contracts
- [x] Product specification
- [x] Architecture document
- [x] Database schema design
- [x] RLS matrix
- [x] Data contracts
- [x] Route map
- [x] Security model
- [x] Test strategy
- [ ] SQL migration scripts
- [ ] TypeScript type definitions from contracts
- [ ] Model snapshot JSON schema (versioned)

## Phase 1 — Application foundation
- [ ] Initialize Next.js App Router project with TypeScript
- [ ] Set up Supabase project, configure auth (email/password + magic link)
- [ ] Create database migration files
- [ ] Apply migrations
- [ ] Configure RLS policies
- [ ] Build login page (/login)
- [ ] Build MFA challenge page (/login/mfa)
- [ ] Build app shell with responsive navigation
- [ ] Implement PWA manifest and service worker
- [ ] Create design system (CSS variables, typography, spacing grid)
- [ ] Create shared components: Card, Table, Chart, MetricTile
- [ ] Implement dark/light mode toggle
- [ ] Set up Vercel deployment pipeline
- [ ] Configure CSP headers
- [ ] Add audit logging infrastructure

## Phase 2 — Model portfolio
- [ ] Create securities reference table (import universe)
- [ ] Build model snapshot import endpoint
- [ ] Implement integrity hash verification on import
- [ ] Build DRAFT → VALIDATED → APPROVED → PUBLISHED → SUPERSEDED workflow
- [ ] Build model current view (/model)
- [ ] Build model history view (/model/history)
- [ ] Build single snapshot view (/model/[snapshotId])
- [ ] Create model comparison component (current vs previous)
- [ ] Add plain-language inclusion reasons for each holding
- [ ] Add quality-component detail view

## Phase 3 — Transaction ledger
- [ ] Build portfolio CRUD (/portfolios, /portfolios/new)
- [ ] Build portfolio detail view (/portfolios/[id])
- [ ] Build transaction entry form
- [ ] Build transaction ledger view (/portfolios/[id]/transactions)
- [ ] Implement holdings derivation logic (from transactions)
- [ ] Build holdings view (/portfolios/[id]/holdings)
- [ ] Implement corporate action handling (split, symbol change)
- [ ] Implement transaction correction workflow
- [ ] Add CSV import for transactions
- [ ] Add CSV export for transactions and holdings
- [ ] Implement idempotency key enforcement

## Phase 4 — Performance
- [ ] Build price observation import pipeline
- [ ] Build benchmark observation import pipeline (SPY, QQQ)
- [ ] Implement portfolio valuation calculation
- [ ] Implement TWR calculation
- [ ] Implement XIRR calculation
- [ ] Implement volatility and drawdown calculation
- [ ] Build performance view (/portfolios/[id]/performance)
- [ ] Build benchmark comparison chart
- [ ] Build multi-timeframe return display (MTD/QTD/YTD/1yr/SI)
- [ ] Build dashboard view (/dashboard)
- [ ] Implement daily NAV caching

## Phase 5 — Quarterly rebalance
- [ ] Build model comparison engine
- [ ] Build rebalance comparison view (/portfolios/[id]/rebalance)
- [ ] Implement illustrative buy/sell calculation
- [ ] Implement cost estimation
- [ ] Build fill-entry workflow
- [ ] Add completion tracking
- [ ] Build rebalance history view
- [ ] Add quarterly review reminder notifications

## Phase 6 — Hardening
- [ ] Implement full backup/restore
- [ ] Implement encrypted data export
- [ ] Add price-staleness warnings
- [ ] Add model integrity failure warnings
- [ ] Security testing (RLS bypass attempts, SQL injection, XSS)
- [ ] Performance optimization (query caching, pagination)
- [ ] Mobile responsive polish
- [ ] Offline read-only cache verification
- [ ] E2E test suite
- [ ] Production deployment checklist
- [ ] Documentation review

## Milestone plan

| Milestone | Phases | Estimated effort |
|---|---|---|
| M0: Foundation | 0, 1 | 2 weeks |
| M1: Model portal | 2 | 1 week |
| M2: Transaction ledger | 3 | 2 weeks |
| M3: Performance analytics | 4 | 2 weeks |
| M4: Quarterly rebalance | 5 | 1 week |
| M5: Production readiness | 6 | 1 week |

Total estimated: 9 weeks for a single developer working full-time.
