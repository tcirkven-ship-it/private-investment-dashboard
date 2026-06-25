# Private Investment Dashboard — Route Map

## Routes

| Path | Method | Description | Layout |
|---|---|---|---|
| `/login` | GET | Login page — email/password, magic link, MFA | Minimal, centered |
| `/login/mfa` | GET | TOTP challenge | Minimal |
| `/dashboard` | GET | Main dashboard overview | App shell |
| `/model` | GET | Current official model | App shell |
| `/model/history` | GET | Historical quarterly snapshots | App shell |
| `/model/[snapshotId]` | GET | Single snapshot detail | App shell |
| `/portfolios` | GET | Portfolio list | App shell |
| `/portfolios/new` | GET/POST | Create portfolio | App shell |
| `/portfolios/[id]` | GET | Portfolio overview | App shell |
| `/portfolios/[id]/holdings` | GET | Current holdings | App shell |
| `/portfolios/[id]/transactions` | GET | Transaction ledger | App shell |
| `/portfolios/[id]/transactions/new` | GET/POST | Record transaction | App shell |
| `/portfolios/[id]/performance` | GET | Performance analytics | App shell |
| `/portfolios/[id]/rebalance` | GET | Quarterly review workspace | App shell |
| `/analytics` | GET | Cross-portfolio analytics | App shell |
| `/settings` | GET | User settings, export, backup | App shell |
| `/admin/model-import` | GET/POST | Import new model snapshot | App shell, service role |
| `/admin/model-review` | GET/POST | Review and approve draft | App shell |

## App shell

The authenticated app shell contains:
- Sidebar navigation (collapsible on mobile)
- Header with data timestamp, user menu
- Main content area
- Notification indicator

## Layout specifications

### Desktop (>=1024px)
- Sidebar: 240px fixed width
- Content: remaining width, max-width 1280px centered
- Supporting side panel for contextual information (optional)

### Tablet (768-1023px)
- Sidebar: collapsed to icon-only (64px)
- Content: full remaining width

### Mobile (<768px)
- Bottom navigation bar with 5 icons
- Full-width content
- Slide-out sidebar for navigation

## Dashboard widgets

1. **Portfolio value card** — total value, daily change, % change
2. **Performance mini-chart** — sparkline of recent NAV
3. **Model alignment** — % overlap with official model
4. **Upcoming actions** — next quarterly review countdown
5. **Recent transactions** — last 5 entries
6. **Sector exposure donut** — current sector distribution
7. **Benchmark comparison table** — vs SPY/QQQ across timeframes
8. **Data health indicator** — latest price timestamps

## Design principles

- Calm, precise, trustworthy — no casino-style visuals
- Dark/light mode support
- Monospace font for numbers
- Consistent spacing: 8px grid
- Financial data: right-aligned, monospace
- All monetary values in integer cents internally, displayed to 2 decimal places
- All percentages to 2 decimal places
