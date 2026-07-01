# Private Investment Tracker

## Register
Product. Design serves the task.

## Primary User
Owner/investor reviewing portfolio holdings, quarterly Top 30 model, and manual comparison. Single private owner — no multi-user, no public registration.

## Core Tasks
- Record manual transactions (deposit, withdrawal, buy, sell) in the portfolio ledger
- View portfolio value, cash balance, holdings, and unrealized/realized P/L at a glance
- Load a notebook-generated quarterly Top 30 model via CSV upload
- Compare portfolio holdings against the Top 30 to decide what to keep, buy, or sell
- Review instructions for the quarterly generator workflow
- Reset app data when needed (visible destructive action)

## Voice & Feeling
Calm, precise, serious, premium, analytical, private. The user is reviewing their own money — no hype, no gamification, no "congratulations" for a trade. Numbers are truthful and unembellished.

## Anti-References
- Toy dashboard / crypto app visuals
- Robinhood or fintech-startup flash
- Gradient text, glassmorphism, fake terminal
- Over-rounded UI, giant border-radius
- Generic SaaS card grids
- Hype copy, celebratory microcopy, confetti
- Dashboard home page (this app has no dashboard — Portfolio is the primary page)
- Cloud generation claims (generator is offline/local)

## Current Stack
- Next.js 15 (App Router)
- Tailwind CSS v4 (`@import "tailwindcss"`)
- Inter (sans) + JetBrains Mono (tabular numbers)
- Supabase (Postgres + auth)
- Dark theme only
