# Recurring-contribution stock-strategy research — final report

**As of:** 2026-06-21  
**Phase One decision:** **FAIL**  
**Live active strategy approved:** No

## Bottom line

The best-tested direct-stock candidate was a 30-stock monthly 12–1-momentum portfolio with weekly USD 250 contributions. Its full 2010–2026 survivor-biased point estimate beat SPY and narrowly beat QQQ, but it trailed QQQ in the one-use final holdout, required excessive turnover, failed QQQ uncertainty and stability tests, and lacked a valid historical universe, delisting outcomes and point-in-time fundamentals.

The strategy therefore fails the original standard and cannot receive a conditional pass.

## Main numbers

| Metric | C03-M | SPY | QQQ |
|---|---:|---:|---:|
| Contributions | $214,500 | $214,500 | $214,500 |
| Ending value | $1,570,117 | $820,567 | $1,403,434 |
| Annualized TWR | 20.55% | 14.03% | 19.30% |
| XIRR | 21.42% | 14.80% | 20.29% |
| Maximum drawdown | -32.41% | -33.72% | -35.12% |

These values use the current 2026 OEF universe projected backward and must not be interpreted as unbiased expected performance.

Final-holdout active annualized TWR was +11.47 points versus SPY but **-0.83 point versus QQQ**. Holdout annualized turnover was 172%. The stitched QQQ active-return bootstrap interval was -3.58% to +4.81%.

## Decision

- Do not deploy the active strategy as validated.
- Retain SPY/QQQ contribution ledgers as passive decision baselines.
- If desired, paper-track C03-M unchanged while building new forward, as-filed evidence.
- Do not reuse the completed 2023–2026 holdout.
- Phase Two development remains optional and requires explicit authorization.

## Visual evidence

![Contribution-matched portfolio values](charts/contribution_matched_values.png)

![Annual active returns](charts/annual_active_returns.png)

![Candidate stability versus QQQ](charts/candidate_stability_vs_qqq.png)

## Detailed files

- `research/00_executive_summary.md`
- `research/10_results.md`
- `research/11_robustness_and_falsification.md`
- `research/12_execution_timing.md`
- `research/13_portfolio_size.md`
- `research/14_weekly_investment_playbook.md`
- `research/15_risks_and_failure_modes.md`
- `research/16_final_recommendation.md`
- `research/17_phase_two_options.md`
- `outputs/final/strategy_card.md`

Past performance does not guarantee future results. This report is research, not personalized investment, tax or legal advice.
