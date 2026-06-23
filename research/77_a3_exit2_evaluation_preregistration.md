# A3 exit2 — frozen confirmatory evaluation preregistration

**Evidence label:** Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe.
**Generation:** A3-EXIT2-EVAL-1.0.0
**Parent:** Price persistence experiment (commit 639f460)

## Candidate

A3: equal average of M12_1 and M6_1 cross-sectional percentile ranks.

## Portfolio mechanics

- N=30, monthly review, rank-60 retention
- Two-consecutive-below-60 exit confirmation
- Hard eligibility failures exit immediately
- Survivors drift; quarterly weight correction (Mar/Jun/Sep/Dec)
- Fill vacancies with highest-ranked non-held
- Next-valid-session-close execution
- Zero-cost primary; 10bps one-way cost sensitivity

## Evaluation period: 2021–2025 (untouched)

## PASS gates

| Gate | Threshold |
|---|---|
| Annualized net return vs SPY | exceeds SPY |
| Annualized net return vs QQQ | exceeds QQQ |
| Annual gross turnover | < 150% |
| Maximum drawdown | > -40% |
| DD vs SPY per fold | not worse than 15pp |
| SPY fold wins | >= 3/5 |
| QQQ fold wins | >= 3/5 |
| Best stock removal | does not eliminate SPY advantage |
| Best year removal | does not eliminate SPY advantage |
| N=20/N=40 direction | same sign active return |
| Suspicious series | not driving result |