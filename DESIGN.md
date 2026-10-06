# Design System — Private Investment Tracker

## Overview
Dark-theme, single-user investment tracking app. Analytical, calm, precise. No brand marketing — design serves the task.

## Color

### Palette (current)
- **Background**: `#0a0a0a` (near-black)
- **Surface/Card**: `#141414`
- **Card border**: `#1f1f1f`
- **Input bg**: `#171717`
- **Input border**: `#404040`
- **Border (general)**: `#262626` / `#1f1f1f` / `#404040`
- **Primary text**: `#e5e5e5`
- **Muted text**: `#737373` / `#a3a3a3`
- **Primary accent**: `#2563eb` (blue-600), hover `#3b82f6`
- **Active nav bg**: `rgba(59, 130, 246, 0.1)`
- **Success**: `#4ade80` (green-400)
- **Danger**: `#f87171` (red-400)

### Issues
- A `#737373` on `#141414` background may fail WCAG AA for small text
- Active nav link uses raw rgba instead of token

## Typography
- **Sans**: Inter (via next/font, CSS variable `--font-sans`)
- **Mono**: JetBrains Mono (via next/font, CSS variable `--font-mono`, used for numeric values)
- **Body**: 0.875rem (14px)
- **Labels**: 0.75rem (12px) uppercase tracked
- **Metric values**: 1.5rem (24px) mono semibold
- **UI text**: font-medium (500) for emphasis

## Layout
- **Shell**: Fixed sidebar + scrollable main area
- **Sidebar**: 224px expanded, 64px collapsed
- **Max content width**: 1280px (`max-w-7xl`), padded 24px each side
- **Card padding**: 1.25rem
- **Nav items**: compact (0.5rem 0.75rem padding)

## Components

### Card
```css
background: #141414;
border: 1px solid #1f1f1f;
border-radius: 8px;
padding: 1.25rem;
```
Used extensively for summary metrics, tables, forms, empty states.

### Buttons
- **Primary**: `bg-blue-600 text-white`, hover `bg-blue-500`
- **Secondary**: `bg-neutral-800 text-neutral-200 border-neutral-700`
- **Ghost**: transparent, `text-neutral-400`, hover `bg-neutral-800`
- All: `border-radius: 6px`, `font-size: 0.875rem`, `font-weight: 500`

### Inputs
- Background: `#171717`, border: `1px solid #404040`
- Border-radius: 6px
- Placeholder: `#737373`

### Tables
- Header: 0.75rem uppercase tracked, `#737373`
- Cells: 0.875rem, mono for numbers, `#d4d4d4`
- Row borders: `1px solid rgba(23, 23, 23, 0.5)`

### Navigation
- **Inactive**: `nav-link` — `#a3a3a3`, hover `#f5f5f5` on `#262626`
- **Active**: `nav-link-active` — `#60a5fa` text, `rgba(59, 130, 246, 0.1)` background

### Sidebar
- Collapsible (16px icon width or 224px expanded)
- Chevron toggle, backdrop-blur for glass effect
- Logout at bottom in border-separated section

## Pages

### Login
- Centered card, max-w-sm
- Blue circle with "I" logo
- Simple form: email + password + sign in button
- Error display in red

### Portfolio (/) 
- "New Transaction" button opens dropdown form
- 5 summary metric cards in grid
- Holdings table with price refresh
- Recent activity table with edit/delete per row

### Top 30
- Upload button for CSV
- Metadata card (Model, Quarter, As-of date, Generated at, Loaded at, Source, File name, Holdings, Validation)
- Snapshot history dropdown
- Holdings table with scores

### Compare
- Snapshot selector dropdown
- Three sections: Keep / Buy / Sell
- Portfolio vs model comparison tables

### Settings
- Reset App Data button with confirmation

## Anti-Patterns to Avoid
- Gradient text
- Glassmorphism (current sidebar backdrop-blur is borderline)
- Identical card grids
- SaaS cliché hero metrics
- Toy/crypto dashboard design
- Hype copy or financial cheerleading
