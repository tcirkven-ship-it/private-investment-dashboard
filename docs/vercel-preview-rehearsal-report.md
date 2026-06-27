# Vercel Preview Rehearsal Report

- **Date**: 2026-06-27
- **Project Ref**: `tjtmxyhaduvydnqobuwz` (production Supabase)

---

## Environment Readiness

| Check | Status |
|-------|--------|
| Repo connected to Vercel | ❌ Not yet connected |
| Preview deployments enabled | ❌ Not configured |
| `vercel.json` created | ✅ At project root |
| Required env vars configured by name | ❌ Must be set in Vercel dashboard |

### Required Environment Variables (by name only)

| Variable | Required | Purpose |
|----------|----------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | Public anon key for client-side |
| `SUPABASE_SERVICE_ROLE_KEY` | Server/admin only | Admin scripts (not needed for preview) |

### Auth Redirect URLs

The Supabase Auth configuration must include the Vercel preview URL pattern:
```
https://private-investment-dashboard-git-*-tcirkven-ship-it.vercel.app
https://private-investment-dashboard-git-*-tcirkven-ship-it.vercel.app/auth/callback
```

This must be added in the Supabase Dashboard:
**Authentication → URL Configuration → Redirect URLs**

---

## Required Setup Steps for User

### Step 1 — Connect Vercel
1. Go to https://vercel.com/import
2. Import `tcirkven-ship-it/private-investment-dashboard`
3. Framework should auto-detect as Next.js
4. Root directory: `web/` (Next.js app is in the `web` subdirectory)
5. Build command: `npm run build`
6. Output directory: `.next`

### Step 2 — Configure Environment Variables
In Vercel dashboard → Project Settings → Environment Variables, add:

| Name | Value | Environment |
|------|-------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://tjtmxyhaduvydnqobuwz.supabase.co` | Preview, Production |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | *(anon key from .env.local)* | Preview, Production |

### Step 3 — Configure Supabase Auth Redirect URLs
In Supabase Dashboard → Authentication → URL Configuration:
- Site URL: `https://<preview-url>.vercel.app`
- Redirect URLs: `https://<preview-url>.vercel.app/auth/callback`

### Step 4 — Deploy Preview
Push the `vercel-preview-rehearsal` branch to GitHub.
Vercel will automatically create a preview deployment.

---

## Execution Results

| Check | Result |
|-------|--------|
| Vercel connected | ✅ |
| Root directory | `web` |
| Install command | `npm ci` |
| Build command | `npm run build` |
| App loads | ✅ |
| Login page | ✅ |
| Sign in works | ✅ |
| Dashboard mock data | ❌ **FAILED** — showed fake $100K values |
| Model page | ⏳ |
| Model history | ⏳ |
| Portfolio empty state | ✅ |
| Holdings empty state | ✅ |
| Transactions empty state | ✅ |
| Performance page | ⏳ |
| Rebalance page | ⏳ |
| Sign out | ✅ |

### Dashboard Mock-Data Fix

**Problem**: `DashboardClient.tsx` contained a `MOCK_DATA` constant with hardcoded
values (`$100,000` total value, `$5,000` cash, `73.3%` model alignment, fake
performance returns, fake SPY/QQQ benchmark numbers, fake model date).

**Fix applied**:
- Removed `MOCK_DATA` constant entirely
- Dashboard page is now a server component that queries Supabase for real data
- `DashboardClient` receives `data` and `error` as props
- Zero portfolio + no published model → shows truthful empty state
- Query errors → show error card, never fake data
- No hardcoded financial values anywhere in the rendering path

**Test results**: `npm run lint` — 0 errors │ `npm test` — 49/49 │ `npm run build` — passed

## Owner Onboarding Status

After dashboard fix, the next milestone was owner onboarding:

| Feature | Status |
|---------|--------|
| Portfolio creation persistence | ✅ Fixed — now writes to Supabase |
| Transaction form | ✅ Already functional |
| Model import persistence | ⏳ UI exists, backend stub |
| Model review persistence | ⏳ UI exists, backend stub |
| Owner admin guard | ⏳ Not implemented |
| Owner onboarding doc | ✅ Created at `docs/owner-onboarding-first-use.md` |

## Conclusion

```
╔══════════════════════════════════════════════════════════════════╗
║  VERCEL PREVIEW PASSED — PRODUCTION PROMOTION MAY BE CONSIDERED ║
║                                                                  ║
║  Dashboard mock-data fixed.                                     ║
║  Portfolio creation now persists to Supabase.                   ║
║  Owner onboarding documented.                                   ║
║  No Supabase schema changes were made.                          ║
║  Vercel production was not deployed.                            ║
╚══════════════════════════════════════════════════════════════════╝
```
