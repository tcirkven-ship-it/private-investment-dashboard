# Deployment Environment Checklist

This document lists all environment variables required for deployment.
**No actual values are included.**

## Supabase

| Variable | Required | Scope | Notes |
|----------|----------|-------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Client + Server | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | Client + Server | Public anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Server/admin only | Server | Used only by admin scripts and CI tests |

## Database

| Variable | Required | Scope | Notes |
|----------|----------|-------|-------|
| `PG_TEST_URL` | CI only | CI | Direct Postgres connection for migration/RLS verification |

## Vercel

| Variable | Required | Scope | Notes |
|----------|----------|-------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Production + Preview | Same as Supabase URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | Production + Preview | Same as Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Optional | Production (if admin scripts deployed) | Required if server-side admin endpoints call service role |

## Authentication

| Setting | Required | Notes |
|---------|----------|-------|
| Site URL | Yes | Vercel deployment URL (e.g. `https://*.vercel.app`) |
| Redirect URLs | Yes | `https://*.vercel.app/auth/callback` |
| `NEXT_PUBLIC_SITE_URL` | Yes | Must match Site URL in Supabase Auth settings |

## Local-Only Variables (never committed)

| Variable | Notes |
|----------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | Local Supabase URL from `supabase status -o env` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Local Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Local Supabase service role key |
| `PG_TEST_URL` | Local database URL for CI/migration tests |

## Verification Steps

- [ ] All `NEXT_PUBLIC_*` variables are set in Vercel project settings
- [ ] `SUPABASE_SERVICE_ROLE_KEY` is set only if needed
- [ ] `NEXT_PUBLIC_SITE_URL` matches the Vercel deployment domain
- [ ] Supabase Auth redirect URLs include all Vercel preview URLs
- [ ] No secrets are hardcoded or committed
- [ ] `.env.local` is in `.gitignore`
