# Working Baseline — Private Investment Tracker

Status: Freeze. No more UI changes.

## App URL

Official:
https://private-investment-dashboard-tcirkven-projects.vercel.app

Do not use `https://private-investment-dashboard.vercel.app` — it belongs to another Vercel team and points to an old/wrong deployment.

## CI/CD

- GitHub Actions are disabled (all workflows set to `workflow_dispatch` only).

## Core Features (Working)

- **Login** — English, email/password, private owner-only.
- **Portfolio** — holdings table, transaction ledger, price refresh, portfolio rename, hierarchical metric cards.
- **Top 30** — CSV upload, metadata card with validation, snapshot history selector.
- **Compare** — Keep / Consider Buying / Consider Selling, snapshot selector on same page.
- **Instructions** — quarterly workflow, CSV format, strategy explanation (M1_B2_QUALITY_VETO_N30).
- **Settings** — Reset App Data with dry-run counts and typed confirmation.
- **Local Generator** — 4-stage launcher (`Run Quarterly Top30 Generator.command`), offline Python pipeline.
- **Mobile** — usable on iPhone portrait (sidebar auto-collapses, tables scroll horizontally, 1-column metrics).

## Known Future Ideas (Not Implemented)

- Performance page with time-series charts.
- Benchmark against S&P 500 and QQQ.
- Richer portfolio analytics (sector allocation, concentration, attribution).

## Rule

Do not change working flows without a specific task and verification.
