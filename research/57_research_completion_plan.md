# Historical research completion status and plan

## Completed evidence

Price-only C03-M and nine registered variants were tested using chronological development (2010–2019), a 2020–2022 walk-forward label and a one-use 2023–2026 final period. The primary price-only strategy failed: it trailed QQQ in the final period, had 172% annual turnover, failed uncertainty/stability gates, and used a current survivor-biased universe. Contribution-frequency sensitivity found similar return rates for weekly, biweekly and monthly funding, but that was not a test of score/review frequency.

Current YF-QVP factor implementation has passed coverage, semantic and deterministic-calculation checks across a full current universe. Those are engineering/current-cross-sectional results, not return validation.

## Not completed or not credibly answerable

- No reliable long historical full-QVP backtest exists.
- No repeated anchored walk-forward QP or QGP return study exists.
- Daily, weekly, biweekly, monthly and quarterly *selection/review* frequencies have not yet been compared under frozen QP/QGP proxy rules.
- The prior “walk-forward” is one chronological stage, not repeated outer folds.

The limiting fact is not merely missing code. Yfinance lacks point-in-time market capitalization, enterprise value, valuation vintages, inactive listings, permanent identifiers and complete delisting outcomes. Current fields must not be projected backward.

## Next feasible proxy experiment

Register a new exploratory generation before observing results:

- candidates: Price, Quality + Price, Quality + Growth + Price; never call these historical QVP;
- fundamentals: only dated statement fields, conservatively lagged and never filled from current valuation/estimate fields;
- cross-section: market-wide fundamental ranks without current sector classifications;
- schedules: daily, weekly, biweekly, monthly and quarterly;
- N: 20/30/40;
- exits: immediate N, 1.5N and 2N;
- validation: expanding chronological folds, contribution-matched SPY/QQQ, zero-cost primary accounting, TWR/XIRR/drawdown/volatility/turnover/concentration;
- labels: survivor-biased and potentially restated exploratory proxy evidence.

If the user needs a credible long full-QVP conclusion, the next research action is to introduce a historical-universe and point-in-time fundamentals source. No amount of yfinance-only code can manufacture missing vintages.
