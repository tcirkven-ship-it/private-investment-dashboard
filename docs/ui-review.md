# UI Design Review — Private Investment Tracker

## 1. Page-by-Page Critique

### Login (`/login`)
- **Unfinished**: The blue circle with "I" looks like a placeholder, not a product identity. No branding personality.
- **Hierarchy**: The card is vertically centered but the "Owner access" label collapses into the form spacing — no breathing room between label and form.
- **Interaction**: The "Sign in" button has no loading spinner state beyond text change. No global error banner pattern.
- **What should change**: Replace the placeholder logo mark and add a proper error/success notification pattern.

### Portfolio (`/portfolios`)
- **Unfinished**: The page head is a bare `<h1>` with two action buttons floating to its right via `justify-between` — no toolbar, no container, no visual grouping. The "New Transaction" button sits directly under the title with no separation from the page header.
- **Hierarchy**: Five metric cards sit in a `grid-cols-2 md:grid-cols-5` — on mobile they're two columns of identical grey boxes. Every card has the same weight. Nothing signals "this is the total value" vs "this is a supporting metric."
- **Spacing/Alignment**: The metric cards, holdings table, and activity log all share the same `space-y-6` rhythm — no visual differentiation between functional groups.
- **Missing states**: No loading skeleton for price refresh. No explanation of "In Top 30? — Yes/—". The column header "In Top 30?" doesn't explain what yes/no means.
- **What should change**: Toolbar-style action row under a strong page header. Metric cards with distinct hierarchy. Proper table polish. Separated sections.

### Top 30 (`/model`)
- **Unfinished**: The metadata card is a flat list of key-value pairs. The "Validation: Passed/Incomplete" badge has no visual weight.
- **Hierarchy**: The upload button, snapshot selector, warnings, metadata card, and table all stack with no clear separation of concerns. The upload action and the metadata display should feel like distinct sections.
- **Interaction**: The warning banner (amber) and the metadata card have the same visual style. A warning should feel different from informational content.
- **What should change**: Section the page: Upload area, Metadata summary, Table. The metadata card should feel like a status panel. The table needs the same polish as the portfolio table.

### Compare (`/compare`)
- **Unfinished**: Three identical-looking table cards. The section headers are `<h2>` with a count badge. No visual distinction between "Keep" (good), "Consider Buying" (opportunity), and "Consider Selling" (risk).
- **Hierarchy**: All three sections have identical weight and structure. With 0 items in any section, the empty state text is gray on gray — barely visible.
- **Interaction**: No way to act on a "Consider Buying" or "Consider Selling" decision from this page.
- **What should change**: Color-coded section headers. Better empty states. Distinct visual treatment per section.

### Instructions (`/instructions`)
- **Unfinished**: A wall of ordered/unordered lists. No visual rhythm between sections. Code snippets use `bg-neutral-800` which looks like a dark box.
- **Hierarchy**: All sections have identical `<h2>` and list spacing. No scannable structure.
- **What should change**: Two-column layout for code references. Compact, scannable structure. Visual distinction between "tutorial steps" and "reference."

### Settings (`/settings`)
- **Unfinished**: Works functionally but the confirmation flow is cramped. The "Reset App Data" button reads like a normal secondary action until it reveals a destructive panel.
- **Interaction**: The RESET typed confirmation is good. But the initial CTA underplays the danger.
- **What should change**: Visibly dangerous CTA from the start. Clearer visual separation of the destructive area.

---

## 2. Unified Issues Across All Pages

| # | Issue | Severity |
|---|-------|----------|
| 1 | No visual layering: `bg-#0a0a0a` everywhere, cards are `#141414` — only two surfaces exist | P0 |
| 2 | Button system feels like unstyled HTML: solid blue #2563eb, dark gray, light gray — no craft | P0 |
| 3 | Typography scale is flat: all H1s are 1.5rem/24px, no hierarchy between pages | P1 |
| 4 | Containers lack rhythm: everything is `card` with `space-y-6`, pages look the same | P1 |
| 5 | Sidebar is visually detached: no brand mark, minimal active state, no section grouping | P1 |
| 6 | No visual distinction between informational, warning, and destructive cards | P1 |
| 7 | Table headers and row style are bare minimum: no hover, no striped rows, no density control | P2 |
| 8 | Login page has no personality: placeholder branding, no visual system | P2 |

---

## 3. Proposed Visual Direction

### Theme: Precision Dense Dark

A **private investment terminal** aesthetic applied to modern product UI — not a terminal app, but refined dark-mode product design with deliberate visual hierarchy.

**Physical scene**: The owner sits at a desk in a quiet room, ambient desk lamp, reviewing their portfolio at quarter-end. The screen should feel like a premium tool, not a website.

**Color strategy**: Restrained (tinted neutrals + one accent ≤10%). The accent is a sophisticated blue — not Tailwind blue-600, not a gradient. A deeper steel-blue that reads as "analytical" not "SaaS."

**Reference apps**: Linear (density, intentionality), Stripe Dashboard (contrast within dark theme), Bloomberg Terminal (information density, trusted)

### Visual Principles

#### Background System
- **App background**: `#09090b` (zinc-950 — warmer than pure black)
- **Card surface**: `#131315` (zinc-900, subtly lighter)
- **Elevated surface**: `#18181b` (for toolbars, action bars)
- **Input background**: `#18181b`
- The current `#0a0a0a` is too flat — adding one more mid-layer (`#18181b`) creates depth without three+ layers

#### Border System
- **Card border**: `1px solid rgba(255,255,255,0.06)` — the current solid `#1f1f1f` feels heavy
- **Input border**: `1px solid rgba(255,255,255,0.1)`
- **Table row divider**: `1px solid rgba(255,255,255,0.04)` — much lighter than current `#1f1f1f`

#### Button System
- **Primary**: Filled `#1e40af` (blue-800, deeper than 2563eb) with `#fff` text. This is a deliberate blue — darker, more serious. Hover: `#2563eb`.
- **Secondary**: Transparent, `1px solid rgba(255,255,255,0.12)`, `#a3a3a3` text. Hover shifts border to `rgba(255,255,255,0.2)`. Visibly a button but subordinate.
- **Ghost/Destructive**: `#f87171/15` background with `#fca5a5` text for delete actions.
- **All buttons**: 14px base, 500 weight, 36px height (not the current 32px).

#### Table System
- **Header**: Uppercase 11px, `text-neutral-500`, weight 500, sticky, with bottom border (1px, rgba white 0.06)
- **Rows**: 44px height (improves readability and tap targets), clear row separators
- **Hover**: Subtle `rgba(255,255,255,0.03)` background on hover for data rows
- **Ticker column**: Semi-bold, left-aligned, text-white
- **Action column**: Right-aligned, compact

#### Typography Scale
- **Page title**: 18px, weight 600, tracking -0.01em
- **Section header**: 12px, uppercase, weight 500, `text-neutral-500`, letter-spacing 0.05em
- **Body text**: 13px/1.5, `text-neutral-300`
- **Financial numbers**: JetBrains Mono, tabular-nums, weight 500, `text-neutral-200`
- **Metadata**: 12px, `text-neutral-500`, weight 400

#### Number Formatting
- All financial values: monospace tabular-nums
- Positive values: `text-emerald-400` with `+` prefix
- Negative values: `text-red-400` with `−` prefix
- Zero: `text-neutral-500`, no sign

### Component Plan

| Component | Current State | Proposed |
|-----------|---------------|----------|
| AppShell | Sidebar + scroll main | Same structure, better sidebar |
| Sidebar | 5 items, no sections | Add brand logo, small sections, improved active state |
| PageHeader | Inline h1 + buttons | h1 left, action toolbar right, delimited by bottom border |
| Button | 3 variants (.btn-primary/secondary/ghost) | 3 variants, refined colors + sizing |
| MetricCard | Identical grey cards in grid | Total Value: primary emphasis. Cash/Holdings/P&L: secondary. Visual hierarchy by sizing/color |
| DataTable | Bare header + rows | Polished: sticky header, hover, better borders, density |
| Form/Dialog | Inline form card | Compact form, better labels, consistent input style |
| Alert/Warning | Same card style as info | Distinct visual: colored left accent + different bg tint |
| SnapshotSelector | Card with select dropdown | Inline toolbar element |
| EmptyState | Grey text in card | Subtle icon + guidance text |
| LoginCard | Centered card | Same structure, better brand mark + spacing |
| MetricCard variant | None | Primary metric card (larger, different bg treatment) |

### Proposed Portfolio Page Layout

```
┌─────────────────────────────────────────────────┐
│ PORTFOLIO: My Portfolio           [Compare] (...) │  ← page header with bottom border
├─────────────────────────────────────────────────┤
│ [New Transaction] [Refresh Prices]               │  ← toolbar row, compact
├─────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐│
│ │ TOTAL    │ │ CASH │ │ HLDGS│ │ UN P/L│ │ R P/L ││
│ │ $42,500  │ │$5,000│ │$37.5K│ │+$1,200│ │ +$450 ││
│ └──────────┘ └──────┘ └──────┘ └──────┘ └──────┘│
├─────────────────────────────────────────────────┤
│ HOLDINGS                          (10 securities)│
│ TICKER  SHARES  AVG COST  PRICE   VALUE    P/L   │
│ AAPL    100...  $185.00  $195.00 $19,500 +$1,000 │
│ ...                                             │
├─────────────────────────────────────────────────┤
│ RECENT ACTIVITY                                  │
│ DATE     TYPE      TICKER   DETAILS    ACTIONS   │
│ Jul 01   BUY       MU       50@$XX    [edit]     │
└─────────────────────────────────────────────────┘
```

---

## 4. Files Likely to Change

| File | Change |
|------|--------|
| `web/src/app/globals.css` | Complete rewrite of design tokens, component classes |
| `web/src/components/layout/Sidebar.tsx` | Refined styling |
| `web/src/app/(app)/layout.tsx` | App shell styling |
| `web/src/app/login/page.tsx` | Brand presence, spacing |
| `web/src/app/(app)/portfolios/page.tsx` | Page header structure |
| `web/src/components/portfolios/HoldingsManager.tsx` | Toolbar, cards, table |
| `web/src/components/portfolios/PortfolioActivity.tsx` | Table polish |
| `web/src/components/portfolios/ActivityRow.tsx` | Row styling |
| `web/src/app/(app)/model/page.tsx` | Section structure, table |
| `web/src/app/(app)/compare/page.tsx` | Section headers, tables |
| `web/src/app/(app)/instructions/page.tsx` | Layout, code blocks |
| `web/src/app/(app)/settings/page.tsx` | Destructive area styling |

## 5. Risks

- **Button color change**: Users may prefer the original blue. Mitigated by approval step.
- **Multi-file changes**: Risk of merge conflicts if other changes exist. Mitigated by doing one coherent pass.
- **Accessibility**: Border color changes must maintain contrast. All new colors will be verified.
- **Functionality**: Dozens of components touched. Heavy testing required.

## 6. What I Will Not Touch

- Portfolio transaction logic (HoldingsManager.tsx business logic, not styling)
- CSV loader (loader.ts)
- Supabase queries
- Auth flow
- Route handlers / server actions
- SnapshotSelector navigation logic
- Delete/Reset confirmation flows
- GitHub Actions
- Vercel config
- Generator scripts

---

`UI DESIGN REVIEW READY — WAITING FOR APPROVAL`
