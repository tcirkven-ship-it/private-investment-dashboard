# Recurring-Contribution Stock Strategy Research

This repository tests whether a transparent, long-only US individual-stock strategy funded with approximately USD 250 each week can show credible after-cost out-of-sample performance against contribution-matched passive benchmarks.

Phase One is complete on a user-authorized best-effort free-data basis. The active direct-stock strategy received a **FAIL** decision. The repository does not contain a live trading system, brokerage integration, or an approved active investment recommendation.

## Start here

1. Read `AGENTS.md` and `handoff.md`.
2. Read `research/01_research_protocol.md` and `research/decision_log.md`.
3. Check `research/experiment_registry.csv` before starting a test.
4. Do not access a final holdout until the protocol is explicitly frozen.

## Current checkpoint

The project completed validated contribution benchmarks, a current OEF/yfinance prototype universe, preregistered price-factor tests, a one-use holdout, robustness checks, execution review and an adversarial final audit. Start with `research/00_executive_summary.md` and `research/16_final_recommendation.md`.

## Important limitation

Historical outperformance, if later observed, will not guarantee future results. The program permits a fail conclusion and requires point-in-time controls, realistic costs, fair benchmark cash flows, multiple-testing discipline, and adversarial review.
