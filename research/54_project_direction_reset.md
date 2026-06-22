# Project direction reset — daily on-demand decision support

## Decision

The month-end-only activation protocol is superseded as the controller of practical decision support. It remains preserved as historical governance and may continue only as a decoupled evidence ledger. The current practical system is `YF-DAILY-QVP-1.0.0`.

The reset does not change the economic model. YF-QVP remains Quality + Value + Price, N=30, equal targets, rank-60 holding buffer, and the frozen sector, industry and position constraints. YF-P, YF-QP and YF-QVGP remain comparisons.

What changes is timing:

- current scores and rankings can be generated on demand after any fully completed daily session;
- the user chooses when to review;
- the user chooses whether and when to transact;
- no score generation creates an order, fill or prospective-ledger event;
- month-end remains a schedule to test, not an information-access gate.

## Evidence classification

Each daily scanner run is current cross-sectional decision-support research. It is not an untouched prospective return observation. If the user explicitly chooses a paper decision, that decision must be recorded separately before any later paper-price observation is consumed.

The complete QVP strategy still cannot receive a reliable long historical backtest from yfinance alone. Historical point-in-time market capitalization, enterprise value and valuation vintages are unavailable; current active listings and classifications cannot be projected backward as truth.

## Data-integrity correction discovered during reset

The original 698-name Checkpoint 2 result remains a valid calculation/semantic audit for those names, but its “complete universe” wording was too strong. The enrichment stage treated silent empty Yahoo responses as successful calls, so many candidates failed eligibility before the final-ticker endpoint-error count was measured. The reset retrieval added essential-field and 504-observation retry checks and recovered 1,072 eligible names from the same 1,876 candidates: 697 overlap, 375 additions and one prior name now excluded. Current scoring uses the recovered fresh universe; the old list is not reused.
