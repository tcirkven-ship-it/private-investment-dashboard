# Private Investment Dashboard — Architecture

## Technology stack

| Layer | Choice |
|---|---|
| Framework | Next.js 14+ App Router |
| Language | TypeScript |
| Database | Supabase PostgreSQL |
| Auth | Supabase Auth (email/password, magic link, TOTP MFA) |
| RLS | Supabase Row Level Security |
| Hosting | Vercel |
| PWA | Next.js PWA support + manifest |
| Charts | Lightweight financial chart library (e.g., lightweight-charts, recharts) |
| Backend | Python + existing research engine (separate from web app) |
| Version control | Private GitHub repository |

## System architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Browser (PWA)                             │
│  Next.js App Router / React Server Components                │
│  Mobile-responsive / Offline-read cache                      │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼───────────────────────────────────┐
│                     Vercel (Node.js)                          │
│  Server Actions / API Routes                                 │
│  RLS-authenticated Supabase queries                          │
│  Input validation / Rate limiting / CSP headers              │
└──────────────────────────┬───────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
┌─────────────▼──────────┐  ┌──────────▼──────────────────┐
│    Supabase Postgres   │  │  Python Research Engine      │
│    - Auth              │  │  (separate GitHub repo)      │
│    - RLS               │  │  - Daily scanner             │
│    - Transaction data  │  │  - Model snapshot generation │
│    - Portfolio data    │  │  - Integrity checks          │
│    - Model snapshots   │  │  - Historical backtests      │
│    - Price observations│  │                              │
└────────────────────────┘  │  Output: JSON snapshot files │
                             │  Imported via admin workflow │
                             └──────────────────────────────┘
```

## Data flow

1. Python engine generates quarterly model snapshot → integrity manifest → JSON file
2. Owner uploads or server imports the snapshot into Supabase
3. Snapshot imported as DRAFT → owner reviews → APPROVED → PUBLISHED
4. Frontend queries published snapshots via authenticated RLS
5. User records transactions → holdings derived by database views or application logic
6. Daily prices imported via market-data abstraction layer
7. Performance calculated server-side; cached for dashboard views

## Market data abstraction

```typescript
interface MarketDataProvider {
  getHistoricalPrices(symbol: string, start: Date, end: Date): Promise<PriceBar[]>;
  getLatestPrice(symbol: string): Promise<PriceBar>;
  getDividends(symbol: string, start: Date, end: Date): Promise<DividendEvent[]>;
  getCorporateActions(symbol: string, start: Date, end: Date): Promise<CorporateAction[]>;
}
```

Initial implementation wraps existing yfinance workflows. The interface allows swapping the data source without changing application logic.

## Scoring engine isolation

The Python research code is a separate system. The application never calls yfinance or runs scoring code directly. All model data arrives through the imported snapshot contract.

## Security boundaries

- Supabase service-role key never reaches the browser
- All private rows have owner_id with RLS enforcing `owner_id = auth.uid()`
- Published model snapshots are read-only
- Transaction deletion is replaced by correction events
- CSV import validated client-side and server-side
- Idempotency keys prevent duplicate imports
- CSP headers restrict resource loading
- Rate limiting on auth endpoints
