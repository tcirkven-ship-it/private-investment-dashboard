# Corrected executive summary

**Phase 1A audit date:** 2026-06-21  
**Existing decision preserved:** **FAIL for C03-M and the tested preliminary price-only generation; no live active strategy approved.**

## What the evidence establishes

C03-M—a 30-stock monthly 12–1 momentum portfolio—and nine related price variants did not satisfy the frozen best-effort approval standard. C03-M trailed QQQ in the 2023–2026 strategy evaluation, failed under stressed costs, required gross turnover above the 100% limit, lacked stable parameter support, and had uncertainty spanning zero versus QQQ. Every candidate also failed the decisive historical-universe and delisting-data gate.

The reported full-period values, TWR, XIRR, volatility, drawdown, costs and gross turnover are numerically reproducible from the saved ledgers. Those ledgers are synthetic adjusted-close total-return ledgers, not raw-share broker ledgers.

## What the evidence does not establish

It does not establish that:

- momentum strategies generally fail;
- direct-stock strategies generally fail;
- price-plus-fundamental strategies fail;
- passive investing is necessarily superior for this investor; or
- no active strategy could satisfy the original objective.

The original mandate remains incomplete. No historical point-in-time fundamental strategy was tested, and the requested fundamental composites, many price factors, stop alternatives, portfolio rules, repeated walk-forward tests, and formal whole-search controls were not completed.

## Largest problem

The backtest projected the **2026 OEF holdings backward to 2010**. Removed, acquired, bankrupt, diminished and delisted historical securities were absent. This conditions the historical opportunity set on future survival and importance and can inflate returns and understate terminal-loss/drawdown risk. Better price quotes alone cannot repair that problem.

The 2023–2026 strategy result was generated once after code/configuration hashes were frozen, but complete SPY/QQQ benchmark data for that period existed before the freeze and raw data were not access-separated. It should be described as a controlled one-batch evaluation, not a strictly untouched protocol-compliant final holdout. No evidence of tuning to the strategy outcome was found.

## Practical conclusion

- Do not deploy C03-M or select the high-return N=10/N=20 variants from these results.
- Retain SPY and QQQ as separate decision benchmarks; factor diagnostics do not waive either hurdle.
- Treat the passive benchmark policy as the current evidence-compatible default, not as proof of a personalized optimal allocation.
- Do not begin another strategy search until the investor chooses an evidence/data path.

## Decision required

Choose one:

1. fund research-grade historical data and repeat the original price-plus-fundamentals mandate under a new preregistration and new future holdout;
2. accept a narrower, explicitly non-equivalent study matched to affordable data; or
3. keep costs at zero and run a frozen forward paper portfolio with immutable snapshots for several years.

Under a strict zero-cost constraint, only the third path is presently defensible. It can generate prospective evidence but cannot retroactively complete the original historical mandate.

Detailed audit:

- `research/18_research_audit_and_gap_analysis.md`
- `research/19_backtest_calculation_audit.md`
- `research/20_data_requirements_and_vendor_matrix.md`
- `research/21_research_continuation_decision.md`
