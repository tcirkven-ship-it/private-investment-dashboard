# Vercel Deployment Rehearsal Plan

This is a controlled plan for a future Vercel deployment rehearsal.
**Do not promote to production until explicitly approved.**

## Overview

- **Goal**: Verify that the application builds, deploys, and functions on Vercel preview
- **Risk**: Environment misconfiguration or auth redirect issues
- **Requires**: Access to Vercel project settings

## Procedure

### Step 1: Preview Deployment

- [ ] Push branch to GitHub
- [ ] Vercel automatically creates a preview deployment for the branch
- [ ] Wait for build to complete (check Vercel dashboard)
- [ ] Verify build logs show no errors
- [ ] Confirm preview URL is accessible (e.g. `https://<project>-git-<branch>-<hash>.vercel.app`)

### Step 2: Environment Variable Verification

- [ ] Open Vercel project settings → Environment Variables
- [ ] Verify `NEXT_PUBLIC_SUPABASE_URL` is set for Preview
- [ ] Verify `NEXT_PUBLIC_SUPABASE_ANON_KEY` is set for Preview
- [ ] Verify `SUPABASE_SERVICE_ROLE_KEY` is set for Preview (if required)
- [ ] Verify `NEXT_PUBLIC_SITE_URL` matches the preview domain (or is set dynamically)
- [ ] Check that no secrets are exposed in build logs or client bundle

### Step 3: Auth Redirect URL Verification

- [ ] Log into Supabase dashboard → Authentication → URL Configuration
- [ ] Verify `Site URL` includes the Vercel preview domain pattern: `https://<project>-git-*-<scope>.vercel.app`
- [ ] Verify `Redirect URLs` includes: `https://<project>-git-*-<scope>.vercel.app/auth/callback`
- [ ] Test login flow on the preview deployment:
  - [ ] Navigate to preview URL
  - [ ] Click sign in
  - [ ] Complete email/password login
  - [ ] Confirm redirect back to preview URL works
  - [ ] Verify session persists across page navigation

### Step 4: Smoke-Test Checklist

Run the full smoke-test checklist against the preview deployment:

- [ ] Login / Auth
- [ ] Model page
- [ ] Model history
- [ ] Portfolio detail
- [ ] Holdings
- [ ] Transactions
- [ ] Add transaction and refresh
- [ ] Performance
- [ ] Rebalance
- [ ] Error state
- [ ] Empty state
- [ ] Second-user isolation
- [ ] Sign out

See `docs/pre-deployment-smoke-test.md` for detailed test cases.

### Step 5: Rollback Plan

- [ ] If the preview deployment fails: fix the issue on the branch and push again
- [ ] Vercel automatically creates a new preview deployment for each push
- [ ] Previous preview deployments remain accessible for comparison
- [ ] If production is affected: use Vercel dashboard to promote a previous production deployment
- [ ] Vercel retains deployment history — use "Promote to Production" on a known-good deployment

### Step 6: No Production Promotion Without Manual Approval

- [ ] Do not merge the deployment branch into `main` without manual sign-off
- [ ] Do not promote the preview deployment to production without explicit approval
- [ ] Production promotion requires:
  - All CI jobs green
  - Smoke tests passed against preview
  - Auth redirects verified
  - Environment variables confirmed
  - Written approval from project owner

## Safety Checklist

- [ ] Preview deployment builds successfully
- [ ] Environment variables verified in Vercel dashboard
- [ ] Auth redirect URLs configured in Supabase dashboard
- [ ] Login flow works on preview deployment
- [ ] Smoke tests pass against preview deployment
- [ ] Rollback plan understood
- [ ] Explicit approval received before production promotion
