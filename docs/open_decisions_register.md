# Private Investment Dashboard — Open Decisions Register

| ID | Question | Options | Recommendation | Status |
|---|---|---|---|---|
| DEC-APP-001 | Chart library | lightweight-charts, recharts, d3, trading-vue | lightweight-charts (financial-native, responsive, maintained) | OPEN |
| DEC-APP-002 | Hosting region | US East, EU West, auto | EU West (owner is in Europe) | OPEN |
| DEC-APP-003 | Price data source | yfinance (existing), Polygon.io, Twelve Data, manual CSV | Start with yfinance via existing engine; abstract behind interface | OPEN |
| DEC-APP-004 | Offline cache strategy | IndexedDB, Cache API, both | Cache API for read-only dashboard data; IndexedDB for transaction drafts | OPEN |
| DEC-APP-005 | Mobile push notifications | Not supported, email only, third-party service | Email only in v1 (Supabase pg_notify → email) | OPEN |
| DEC-APP-006 | Decimal library | number with cent conversion, decimal.js, postgres numeric | decimal.js in TypeScript; NUMERIC in Postgres | OPEN |
| DEC-APP-007 | Dark mode default | System preference, light, dark | System preference with manual override | OPEN |
| DEC-APP-008 | Backup frequency | Daily, weekly, manual | Weekly automated + on-demand | OPEN |
| DEC-APP-009 | Model snapshot storage | Database only, S3 + database, local files | Database + local JSON backup for portability | OPEN |
| DEC-APP-010 | Mobile app wrapper | PWA only, Capacitor, React Native | PWA only (no native distribution) | DECIDED |
| DEC-APP-011 | Multi-currency support | USD only, any fiat, crypto | USD only in v1 | OPEN |
| DEC-APP-012 | Tax lot identification | FIFO, Specific ID, HIFO | FIFO in v1; Specific ID later | OPEN |
| DEC-APP-013 | Email notifications | Supabase pg_notify, SendGrid, Resend | Resend (developer-friendly, generous free tier) | OPEN |
| DEC-APP-014 | Performance aggregation | Real-time computation, daily cache, both | Daily cache with on-demand refresh | OPEN |
| DEC-APP-015 | Supabase project | Existing or new | New project (clean separation from any existing Supabase usage) | OPEN |
