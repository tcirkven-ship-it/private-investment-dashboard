# Daily YF-QVP scanner specification

## Command

```bash
.venv/bin/python -m src.daily_screen --holdings user/holdings.csv --contribution 500
```

Both arguments are optional. With no holdings file the scanner produces a model portfolio but no personal holdings classification. With no contribution argument it uses USD 0 while still reporting standard USD 250/500/1,000/5,000 illustrations.

## Pipeline

1. Create a timestamped immutable raw directory.
2. Screen a non-truncated sector × market-cap yfinance universe.
3. Apply the frozen domestic, USD, ordinary-equity, size, price, history and liquidity rules.
4. identify the latest fully completed SPY daily session; before 16:15 America/New_York, exclude the current calendar date even if Yahoo exposes a partial daily row.
5. Recalculate the frozen Quality, Value and Price factors and archive calculation evidence.
6. Rank all eligible names with complete QVP support.
7. Greedily select 30 names by score subject to 25% sector and 15% industry target caps; identify cap exclusions and replacement admissions.
8. Compare with the prior daily-scanner run only. Never substitute the old Checkpoint 2 list as the previous practical run.
9. Optionally classify holdings and calculate contribution allocations across up to three largest model underweights plus a one-name alternative.
10. Write immutable CSV/Markdown/HTML outputs and a SHA-256 manifest; publish compact current copies under `outputs/final/`.

## Frozen scoring

- Quality: ROA, gross profitability/assets, FCF margin, inverse debt/assets.
- Value: FCF yield, sales/EV, book-to-market.
- Price: 12–1 momentum, 6–1 momentum, 200-day trend, inverse 252-day volatility.
- Category factors must all be present; missing required inputs remain missing rather than zero.
- Contribution amount cannot enter any factor, eligibility, rank or portfolio-selection calculation.

## Holdings classifications

- rank 1–30: `HOLD`;
- rank 31–60: `HOLD` under the buffer;
- rank below 60: `MODEL EXIT`;
- hard ineligibility: `REVIEW`;
- missing/unreliable data: `DATA OR CORPORATE-ACTION REVIEW`;
- constrained-model name not held: `BUY/ADD CANDIDATE`.

These are transparent model labels, not automatic actions or personalized advice.
