# Private Investment Dashboard — Test Strategy

## Unit tests

- Transaction ledger: buy/sell/dividend/deposit/withdrawal accounting
- Holdings derivation from transaction events
- Average cost calculation (FIFO, specific identification)
- Cash balance tracking
- XIRR calculation
- TWR calculation across contribution events
- Benchmark cash-flow matching
- Decimal/money arithmetic (no floating-point drift)

## Integration tests

- Model snapshot import from JSON
- Integrity hash verification
- Status state machine transitions
- RLS policies (authenticated vs service-role vs anonymous)
- CSV import validation
- Idempotency key enforcement
- Price observation import
- Rebalance comparison calculation

## Fixtures

### Transaction fixture 1: Buys and sells
- 10 buy events for 3 tickers over 6 months
- 2 partial sells
- 1 complete sell
- Expected: correct remaining quantities, average cost, realized gains

### Transaction fixture 2: Dividends and fees
- 3 dividend events
- 2 fee events (annual account fee, wire fee)
- Expected: correct cash balance, income tracking

### Transaction fixture 3: Deposits and withdrawals
- Initial deposit
- Monthly contributions
- One withdrawal
- Expected: correct cash balance, XIRR, contribution history

### Transaction fixture 4: Stock splits
- 2:1 split
- 1:5 reverse split
- Expected: correct quantity adjustment, cost basis unchanged

### Transaction fixture 5: Complete liquidation
- Full portfolio sold
- All cash withdrawn
- Expected: final balance zero, all gains realized

### Transaction fixture 6: Multiple portfolios
- 3 portfolios with different transaction histories
- Expected: correct isolation between portfolios

### Transaction fixture 7: Quarter-end model changes
- Model snapshot imported
- Rebalance comparison generated
- Illustrative trades calculated
- Expected: correct alignment

## Frontend tests

- Responsive layout tests (desktop, tablet, mobile)
- PWA manifest validation
- Offline caching behavior
- Chart rendering with fixture data
- Navigation smoke tests
- Form validation

## E2E tests

- Authentication flow
- Portfolio creation → add transactions → view holdings
- Model import → review → publish
- Quarterly rebalance workflow
- Data export
- Backup and restore

## Test data

All tests use deterministic synthetic data. No live API calls in tests. Price data generated programmatically with known return characteristics. Benchmark data generated to match expected test scenarios.
