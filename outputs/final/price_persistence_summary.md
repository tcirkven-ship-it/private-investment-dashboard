# Price persistence experiment — summary

**Decision:** FAIL — Price research path exhausted under current yfinance dataset.

**Closest result:** A3 with two-consecutive-below-60 exit confirmation (24.69% return, 64% turnover, 6/6 SPY wins) fails only the DD-vs-SPY-per-fold threshold by 0.09pp.

**Key mechanical finding:** Two-consecutive-below-60 exit confirmation reduces turnover from 500–600% to 64–70% — a 10× improvement. This should be considered for any future practical implementation but does not rescue the Price signal itself.

**Next actions:**
- Cease Price-only signal research under yfinance.
- Maintain YF-QVP scanner as practical decision-support tool.
- Prospective evidence accumulation remains active.
- Paid-data preparation required to resolve survivorship ceiling.
