# Staging Reconciliation Rehearsal Plan

> **Warning**: This plan is for a staging Supabase project only.
> Never run these steps against production hosted Supabase.
> Never reset production hosted Supabase.
> No production migration changes are generated here.

---

## 1. Create or Identify a Staging Supabase Project

### Option A — Supabase CLI (local staging)
```bash
# Start local Supabase (Docker required)
npx supabase start

# Verify it is running
npx supabase status
```

This creates a local Supabase stack with a fresh database. The schema will be
initialized from `supabase/migrations/` automatically.

### Option B — Separate hosted Supabase project (remote staging)
Create a new Supabase project in the Supabase dashboard:
- Name: `private-investment-dashboard-staging`
- Region: Same as production (for realistic testing)
- Password: Generate and store securely

**Recommendation**: Start with Option A (local) for rapid iteration, then Option B
(remote staging) for production-like validation.

### Staging connection info (do not commit):
```
NEXT_PUBLIC_SUPABASE_URL=<staging-url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<staging-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<staging-service-role-key>
```

---

## 2. Copy Hosted Schema Metadata Safely

### Step 2.1 — Export production hosted schema (read-only)
```bash
# Requires psql access with database password
pg_dump \
  --schema-only \
  --no-owner \
  --no-acl \
  --no-comments \
  --dbname=<production-database-url> \
  > /tmp/production-hosted-schema-backup.sql
```

### Step 2.2 — Restore to staging
```bash
# For local staging (Option A):
psql -d <local-staging-db-url> -f /tmp/production-hosted-schema-backup.sql

# For remote staging (Option B):
psql -d <remote-staging-db-url> -f /tmp/production-hosted-schema-backup.sql
```

### Step 2.3 — Verify staging schema matches production
Run the schema-policy-audit script against staging:
```bash
PG_TEST_URL=<staging-db-url> npx tsx web/scripts/schema-policy-audit.ts
```

Compare output with the production hosted inspection report.

---

## 3. What Data Must Be Backed Up Before Any Rehearsal

Before any migration testing on staging:

- [ ] Export production hosted schema: `pg_dump --schema-only`
- [ ] Export production hosted data (if any exists): `pg_dump --data-only`
- [ ] Export Supabase Auth configuration (dashboard → Authentication → Settings → Export)
- [ ] Document production Supabase project settings:
  - Auth providers enabled
  - Site URL
  - Redirect URLs
  - API settings (JWT expiry, etc.)
  - Storage buckets (if any)

Store all backups in a secure, versioned location outside the repository.

---

## 4. Which Objects Must Be Preserved

| Object | Reason | Preservation Method |
|--------|--------|-------------------|
| `auth.users` | User accounts | Never drop or truncate auth schema |
| `profiles` | User profile data | Created by trigger, preserved by migration |
| `app_settings` | Application configuration | Backup before migration |
| `transactions` | Financial data (if any exists) | Backup before migration |
| `portfolios` | Portfolio definitions | Backup before migration |
| All RLS policies | Access control | Re-apply from migration file after change |
| All functions/triggers | Business logic | Re-apply from migration file after change |

**Production hosted is never modified during staging rehearsal.**

---

## 5. Test the Enum Decision

### Scenario: Adopt hosted `transaction_types` (rename local `transaction_event_type`)

**Test script for staging:**
```sql
-- Verify current enum exists
SELECT typname FROM pg_type WHERE typname IN ('transaction_types', 'transaction_event_type');

-- If hosted uses `transaction_types`, test that local code works with this name
-- by checking that the adapter functions and holdings engine reference the enum
-- by its VALUES, not by the TYPE name (they do — values are the same).

-- Verify enum values match
SELECT enumlabel FROM pg_enum WHERE enumtypid = (
  SELECT oid FROM pg_type WHERE typname = 'transaction_types'
);
-- Expected: DEPOSIT, WITHDRAWAL, BUY, SELL, DIVIDEND, FEE, TAX, INTEREST,
--           SPLIT, SYMBOL_CHANGE, MERGER, SPINOFF, CORRECTION, TRANSFER
```

**Local validation:**
```bash
# Search for enum name references in application code
cd web && grep -r "transaction_event_type" src/ --include="*.ts" --include="*.tsx"
# If no code references the enum name directly (only values), the rename is safe.
```

**Pass condition**: Application compiles and tests pass after enum name alignment.

---

## 6. Test the Column Decision

### Scenario: Adopt hosted `tax` (rename local `tax_amount`)

**Test script for staging:**
```sql
-- Check hosted has `tax` column
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'transactions' AND column_name IN ('tax', 'tax_amount');

-- If both exist, test migration to rename/drop:
-- ALTER TABLE transactions RENAME COLUMN tax_amount TO tax;
-- (or for hosted that already has tax: no action needed, just update local)
```

**Local validation:**
```bash
# Search for tax_amount references in code
grep -r "tax_amount" web/src/ --include="*.ts" --include="*.tsx" --include="*.sql"
# Update all references to `tax` after decision
```

**Pass condition**: After renaming, `npm test` passes and portfolio calculations
remain correct (cash = $80,182.00 from the workflow test).

---

## 7. Test Adoption of 8 Hosted Extra Columns

### Columns to add to local migration:
1. `securities.asset_class` (text)
2. `securities.superseded_by` (uuid → securities.id)
3. `model_snapshot_holdings.prior_rank` (int)
4. `model_snapshot_holdings.change_from_prior` (text)
5. `model_snapshot_holdings.data_quality_flags` (text[])
6. `portfolios.starting_cash` (numeric)
7. `portfolios.benchmark_ticker` (text)
8. `transactions.fx_rate` (numeric)

**Test script for staging:**
```sql
-- For each column, verify it exists on hosted:
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND (table_name, column_name) IN (
    ('securities', 'asset_class'),
    ('securities', 'superseded_by'),
    ('model_snapshot_holdings', 'prior_rank'),
    ('model_snapshot_holdings', 'change_from_prior'),
    ('model_snapshot_holdings', 'data_quality_flags'),
    ('portfolios', 'starting_cash'),
    ('portfolios', 'benchmark_ticker'),
    ('transactions', 'fx_rate')
  )
ORDER BY table_name, column_name;
```

**If any column is missing from hosted**: Add via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.

**Pass condition**: After adding, `schema-policy-audit` script confirms all expected
columns exist on staging.

---

## 8. Test Creation of Local-Only Tables

### Tables to create on hosted:
1. `model_publication_events`
2. `portfolio_valuations`

**Test script for staging:**
```sql
-- Create model_publication_events if not exists
CREATE TABLE IF NOT EXISTS public.model_publication_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_id UUID NOT NULL REFERENCES public.model_snapshots(id),
  from_status TEXT,
  to_status TEXT NOT NULL,
  changed_by UUID REFERENCES auth.users(id),
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Create portfolio_valuations if not exists
CREATE TABLE IF NOT EXISTS public.portfolio_valuations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES public.portfolios(id),
  valuation_date DATE NOT NULL,
  total_value NUMERIC(14,2) NOT NULL,
  cash_balance NUMERIC(14,2) DEFAULT 0,
  total_deposits NUMERIC(14,2) DEFAULT 0,
  total_withdrawals NUMERIC(14,2) DEFAULT 0,
  UNIQUE(portfolio_id, valuation_date)
);

-- Enable RLS
ALTER TABLE public.model_publication_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolio_valuations ENABLE ROW LEVEL SECURITY;
```

**Pass condition**: Tables created, RLS enabled, and `schema-policy-audit` confirms
their presence with correct columns.

---

## 9. Verify RLS, Policies, Functions, Triggers and Indexes

### Direct database queries (requires psql on staging):
```sql
-- Policies
SELECT schemaname, tablename, policyname, cmd
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename;

-- Functions
SELECT proname, lanname, provolatile
FROM pg_proc p
JOIN pg_language l ON p.prolang = l.oid
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
ORDER BY proname;

-- Triggers
SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY trigger_name;

-- Indexes
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

### Automated script:
```bash
PG_TEST_URL=<staging-db-url> npx tsx web/scripts/schema-policy-audit.ts
PG_TEST_URL=<staging-db-url> npx tsx web/scripts/test-auth-rls.ts
```

**Pass condition**: `schema-policy-audit` reports all expected objects present.
`test-auth-rls` passes all 13+ assertions.

---

## 10. Verify the App Still Works Against Staging

### Set up local `.env.local` to point to staging:
```
NEXT_PUBLIC_SUPABASE_URL=<staging-url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<staging-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<staging-service-role-key>
```

### Run:
```bash
cd web
npm run lint
npm test
npm run build
```

**Pass condition**: All 49 tests pass, lint exits 0, build exits 0.

---

## 11. Smoke-Test Steps Against Staging

Start the local dev server pointing to staging:
```bash
cd web && npm run dev
```

Then manually test:

- [ ] Login page loads and sign-in works (create a test user via Supabase dashboard first)
- [ ] Model page loads without error
- [ ] Model history page shows data or empty state
- [ ] Portfolio detail page loads
- [ ] Holdings page calculates correctly (test with inserted transactions)
- [ ] Transactions page shows list or empty state
- [ ] Add transaction form submits and refreshes
- [ ] Performance page loads without error
- [ ] Rebalance page shows comparison or empty state
- [ ] Error states render correctly (navigate to non-existent IDs)
- [ ] Empty states render correctly (new portfolio)
- [ ] Sign out clears session

---

## 12. Rollback/Restore Plan

| Scenario | Action |
|----------|--------|
| Staging migration fails | Drop and recreate staging from production backup |
| Staging migration succeeds but app breaks | Fix migration, reset staging, retry |
| Production migration (future) fails | Restore from pre-migration schema + data backup |
| Production migration succeeds but bug found | Create fix migration, apply via CI |
| Staging is no longer needed | Delete staging Supabase project |

### Restore staging from production backup:
```bash
# Drop and recreate public schema on staging
psql -d <staging-db-url> -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Restore from production backup
psql -d <staging-db-url> -f /tmp/production-hosted-schema-backup.sql
```

---

## 13. Stop Conditions

Stop the rehearsal immediately if any of the following occur:

- [ ] Schema-policy-audit reports unexpected differences after migration
- [ ] Auth/RLS tests fail
- [ ] Application tests fail (49 tests must pass)
- [ ] Build fails
- [ ] Smoke tests reveal broken functionality
- [ ] Staging data is inconsistent with production schema
- [ ] Migration script produces unexpected errors
- [ ] Any destructive SQL is accidentally run against production (emergency stop)

If stopped, document the failure, fix the migration script, reset staging,
and restart from step 2.

---

## 14. Explicit Warning: Never Reset Production Hosted Supabase

```
╔══════════════════════════════════════════════════════════════╗
║  NEVER RUN AGAINST PRODUCTION HOSTED SUPABASE:               ║
║                                                             ║
║    supabase db reset                                        ║
║    DROP SCHEMA public CASCADE                               ║
║    ALLOW_DESTRUCTIVE_DB_TESTS=true                          ║
║    pg_dump or psql with production credentials              ║
║      unless explicitly approved in a migration plan         ║
║                                                             ║
║  All destructive operations are FORBIDDEN on production.    ║
║  Use staging only for testing.                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Conclusion

```
╔══════════════════════════════════════════════════════════════╗
║  STAGING REHEARSAL PLAN READY — USER APPROVAL REQUIRED      ║
║  PRODUCTION DEPLOYMENT STILL BLOCKED                         ║
║                                                             ║
║  This plan covers:                                          ║
║    • Staging project setup (local or remote)                ║
║    • Safe schema copy from production                       ║
║    • Testing enum rename (transaction_types)               ║
║    • Testing column rename (tax)                            ║
║    • Adopting 8 extra hosted columns                        ║
║    • Creating 2 local-only tables                           ║
║    • Verifying RLS, policies, functions, triggers           ║
║    • Smoke tests, rollback, stop conditions                 ║
║                                                             ║
║  Production hosted Supabase has NOT been modified.          ║
║  Vercel has NOT been deployed.                              ║
╚══════════════════════════════════════════════════════════════╝
```
