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

### Step 5 — Run Smoke Tests
Against the preview URL, verify:
- [ ] App loads without errors
- [ ] Login page renders
- [ ] Sign in works (test user)
- [ ] Dashboard loads
- [ ] Model page loads
- [ ] Model history page loads
- [ ] Portfolio detail shows empty state
- [ ] Holdings shows empty state
- [ ] Transactions shows empty state
- [ ] Add transaction form is safe (validates)
- [ ] Performance page loads
- [ ] Rebalance page loads (empty state)
- [ ] Error states do not leak secrets
- [ ] Sign out works

---

## Conclusion

```
╔══════════════════════════════════════════════════════════════════╗
║  VERCEL PREVIEW NOT YET EXECUTED                                ║
║  PRODUCTION PROMOTION STILL BLOCKED                             ║
║                                                                  ║
║  Vercel is not yet connected to this repository.                ║
║  vercel.json has been created.                                  ║
║  No Supabase schema changes were made.                          ║
║  Vercel production was not deployed.                            ║
╚══════════════════════════════════════════════════════════════════╝
```
