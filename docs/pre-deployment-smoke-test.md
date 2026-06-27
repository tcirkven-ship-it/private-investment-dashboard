# Pre-Deployment Smoke Test Checklist

Run against a **local Supabase stack** only.
Do not run against hosted Supabase.

## Prerequisites

- [ ] `npx supabase start` is running
- [ ] Database migrations have been applied
- [ ] `npm run build` exits 0
- [ ] `npm test` passes
- [ ] `npm run lint` exits 0 (warnings allowed)

## Test Cases

### 1. Login / Auth

- [ ] Navigate to `/login`
- [ ] Sign in with valid email/password
- [ ] Redirected to `/dashboard` after login
- [ ] Sign out clears session and redirects to `/login`
- [ ] Visiting any protected route while signed out redirects to `/login`

### 2. Model Page

- [ ] Navigate to `/model`
- [ ] Page loads without error
- [ ] If model snapshot exists: holdings list rendered with rank, ticker, weight
- [ ] If no model snapshot: empty state displayed
- [ ] Loading state shown during data fetch (if applicable)

### 3. Model History

- [ ] Navigate to `/model/history`
- [ ] Page loads without error
- [ ] Previous snapshots listed with date and status
- [ ] Each snapshot shows holdings or drill-down link

### 4. Portfolio Detail

- [ ] Navigate to `/portfolios/[id]`
- [ ] Portfolio name and summary rendered
- [ ] Navigation links to holdings, transactions, performance, rebalance
- [ ] Error card shown if portfolio not found

### 5. Holdings

- [ ] Navigate to `/portfolios/[id]/holdings`
- [ ] Holdings list shows ticker, quantity, avg cost, market value, weight, P&L
- [ ] Cash balance displayed
- [ ] NAV displayed
- [ ] Price-unavailable notice shown for tickers without price observations
- [ ] Empty state shown when no transactions exist
- [ ] Loading state during fetch

### 6. Transactions

- [ ] Navigate to `/portfolios/[id]/transactions`
- [ ] Transactions listed with date, type, ticker, amount
- [ ] Sorted by date (descending)
- [ ] Empty state shown when no transactions

### 7. Add Transaction and Refresh

- [ ] Navigate to transaction form
- [ ] Submit a DEPOSIT transaction
- [ ] Form shows success confirmation
- [ ] Page refreshes and transaction appears in list
- [ ] Submit a BUY transaction with ticker
- [ ] Submit a SELL transaction
- [ ] Missing required fields shows validation error
- [ ] Error displayed if Supabase insert fails

### 8. Performance

- [ ] Navigate to `/portfolios/[id]/performance`
- [ ] Page loads without error
- [ ] Performance chart or summary rendered if data available
- [ ] Empty state handled gracefully

### 9. Rebalance

- [ ] Navigate to `/portfolios/[id]/rebalance`
- [ ] Current vs target weight comparison rendered
- [ ] Action column shows Add/Remove/Reduce/Increase/Keep
- [ ] Model date displayed
- [ ] Has-prices indicator shown
- [ ] Empty state when no published model exists
- [ ] Error card on query failure

### 10. Error State

- [ ] Navigate to a non-existent portfolio ID
- [ ] Error card or not-found state displayed
- [ ] Console shows no unhandled errors

### 11. Empty State

- [ ] Create a new portfolio
- [ ] Navigate to holdings: empty state shown
- [ ] Navigate to transactions: empty state shown
- [ ] Navigate to rebalance: empty state shown
- [ ] Navigate to performance: empty state shown

### 12. Second-User Isolation

- [ ] Sign in as a second user
- [ ] Navigate to `/portfolios`: no portfolios visible
- [ ] Navigate to `/model`: no model data visible (RLS-gated)
- [ ] Cannot access another user's portfolio via URL manipulation

### 13. Sign Out

- [ ] Click sign out
- [ ] Session cleared
- [ ] Redirected to `/login`
- [ ] Cannot access protected routes via back button
