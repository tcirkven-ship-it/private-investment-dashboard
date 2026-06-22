# Phase 1B yfinance limitations and permitted inference

**Applies to:** yfinance 1.4.0 capability research and any later Phase 1B experiment

## Evidence ceiling

### Tier 1 — Historical price research

Long daily price, volume, dividend and split histories can support prototype price-factor, benchmark and portfolio-mechanics tests. A backtest built from a current Yahoo screen or current ticker list remains survivor- and membership-biased. It is not a historical US-equity universe and cannot establish definitive active performance.

### Tier 2 — Fundamental feasibility

Yahoo's currently retrievable annual, quarterly and trailing statements are useful for field coverage, formula feasibility, current cross-sectional scoring and limited recent exploration. They do not preserve the exact value visible at each historical decision date, actual filing availability, or a complete restatement-vintage history.

Any later lagged analysis must be labeled exactly:

> Exploratory non-point-in-time fundamental analysis using currently retrievable and potentially restated Yahoo Finance data.

The 90-day quarterly/120-day annual lag reduces obvious period-end leakage but does not reconstruct filing timestamps or undo later restatements.

### Tier 3 — Prospective paper research

Immutable retrieval-time snapshots create genuine point-in-time evidence from activation forward. This is the strongest valid Phase 1B evidence, but it remains limited to the future regimes observed, current Yahoo coverage, and the yfinance/Yahoo interface's continued behavior.

## Structural limitations

- No complete historical security master, inactive/delisted universe, delisting returns or terminal-distribution table.
- Current screen membership, sector, industry, country and security type can change and cannot be projected backward.
- No permanent security identifier suitable for all ticker reuse, mergers and share-class changes.
- Statement histories are short and may be restated, standardized or corrected upstream without a historical-vintage API.
- Statement row schemas vary by sector, issuer, fiscal taxonomy and endpoint.
- `Ticker.info`, valuation measures, estimates, revisions and recommendations are current snapshots, not historical observations.
- `get_shares_full` coverage/frequency can vary and is not an authoritative corporate-action security master.
- Adjusted Close is convenient for total-return signals but is not an executable price or raw-share ledger.
- Dividends and splits are retrievable, but mergers, spin-offs, bankruptcy proceeds and other complex actions may be incomplete or ambiguous.
- Intraday history is retention-limited and must be archived promptly for prospective execution evidence.
- Yahoo/yfinance availability, schemas, throttling and corrections can change without a versioned vendor release.
- Data are intended for personal/research use under applicable Yahoo terms; redistribution rights are not assumed.

## Comparability limitations

- Banks, insurers and diversified financials require different balance-sheet, leverage, margin and cash-flow economics.
- REITs require FFO/AFFO and property-specific measures not consistently available in the audited statement schema.
- Limited partnerships, foreign issuers/ADRs and dual share classes are not always identifiable from one stable metadata field.
- Current sector-neutral ranks use current classifications only.
- Currency differences can make raw accounting values incomparable; the primary current strategy must require aligned reporting/trading currency or normalize explicitly.
- Negative denominators and sign-changing growth make ordinary percentage ratios unstable; formulas must mark them missing or use a separately frozen transformation.

## Operational limitations

- Fractional paper orders reduce cash drag but do not prove that the exact modeled price/order is available at IBKR.
- Whole-share, rejected-order, unfilled-limit, spread/slippage, settlement, FX and tax effects need separate explicit treatment.
- A USD 250 contribution may be too small to maintain many equal-weight whole-share positions.
- Data retrieval failure can create stale ranks; the protocol must hold cash rather than assume a successful update.

## Prohibited conclusions

Phase 1B may not claim that:

- a current Yahoo fundamental value existed historically;
- a current-universe backtest is survivorship-free;
- missing delisted securities are harmless;
- conservative statement lags make restated data point in time;
- short recent or forward performance proves durable outperformance;
- the strategy robustly beat SPY/QQQ in periods without archived point-in-time fundamentals; or
- a paper order implies a live attainable fill.

## Permitted conclusions

Subject to evidence-tier labels, Phase 1B may determine whether a practical process is buildable, which fields/factors have adequate current coverage, whether fundamentals change rankings, whether scores are stable, and whether a frozen prospective paper portfolio is operationally and economically acceptable over time.

The preserved Phase 1A FAIL is unaffected. Phase 1B is a new, explicitly lower-evidence research generation and cannot retroactively validate C03-M.
