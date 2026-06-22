# Executive research summary

## Conclusion

**No tested direct-stock strategy met the required standard. Final decision: FAIL.**

The strongest candidate—a 30-stock, monthly 12–1-momentum portfolio funded with USD 250 weekly—produced an attractive survivor-biased full-sample result and beat SPY decisively. It did not beat QQQ in the final holdout, required roughly 172–184% annual turnover, failed QQQ uncertainty and stability tests, and could not satisfy the historical-universe, delisting or point-in-time fundamental-data gates.

Because those are structural failures, the result cannot receive a conditional pass.

## What was studied

- Ten preregistered price-strategy and portfolio-size variants.
- Weekly, biweekly and monthly contribution schedules.
- Contribution-matched SPY and QQQ benchmark ledgers.
- Expected and stressed commissions/price impact.
- Chronological pre-holdout and one-use 2023–2026 holdout periods.
- Drawdown, volatility, turnover, rolling consistency, parameter stability, starting dates, regimes, influential years and stocks, and moving-block uncertainty.
- Current Interactive Brokers commission, fractional-share and closing-order practicality.

## Best available historical result

From 2010 through 2026-06-18, USD 214,500 of contributions grew to approximately:

- C03-M: $1,570,117;
- QQQ: $1,403,434; and
- SPY: $820,567.

The corresponding annualized TWRs were 20.55%, 19.30%, and 14.03%. These numbers are **not unbiased expected returns**: the test used the current 2026 OEF holdings projected backward.

## Why it failed

1. Current-membership survivorship bias and missing delisting outcomes.
2. No credible historical point-in-time fundamentals, so the requested price-plus-fundamental strategy was not validated.
3. Holdout active TWR versus QQQ was -0.83 percentage point; stressed was -0.99 point.
4. Turnover was 172% in the holdout and 178% over the stitched period.
5. The full-period QQQ bootstrap interval ranged from -3.58% to +4.81% annualized.
6. Only 20% of registered candidates were positive versus both benchmarks in both pre-holdout and holdout periods.
7. Fractional Market-on-Close orders are not supported by IBKR, so the modeled next-close convention is not literally deployable for fractional orders.

## Practical implication

No active individual-stock portfolio is approved for live use. The evidence-compatible baseline remains a simple diversified passive contribution policy, with the exact ETF allocation left to the investor's risk, tax and currency context. C03-M may be maintained only as a forward paper-research portfolio.

## Deliverables

- Detailed results: `research/10_results.md`
- Robustness/adversarial review: `research/11_robustness_and_falsification.md`
- Execution: `research/12_execution_timing.md`
- Portfolio size: `research/13_portfolio_size.md`
- Research-only playbook: `research/14_weekly_investment_playbook.md`
- Risks: `research/15_risks_and_failure_modes.md`
- Final decision: `research/16_final_recommendation.md`
- Optional next phase: `research/17_phase_two_options.md`

