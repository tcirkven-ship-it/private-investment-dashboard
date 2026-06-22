# Walk-forward, multiple-testing, and holdout protocol

**Version:** 0.1 draft  
**As of:** 2026-06-21  
**Status:** No dataset selected; calendar boundaries remain unassigned

## 1. Principles

- Time, not random sampling, defines train, validation, and test observations.
- Any rule or parameter chosen using a period is not out of sample for that period.
- Cross-sectional fitting at a date may use only records available at that date.
- The final holdout is a one-use audit, not another development loop.
- Selection uncertainty is measured across the full experiment family recorded in the registry, not only the surviving configuration.

## 2. Calendar partition rule

After Checkpoint 2 approves the reliable dataset span, freeze the calendar split before factor results are reviewed:

- If reliable coverage is at least 20 years, use at least 8 initial training years, at least 7 annual walk-forward test windows, and reserve the latest 5 complete years as the final holdout. Extra history expands walk-forward evaluation rather than the holdout.
- If reliable coverage is 16–20 years, use at least 8 initial training years, at least 5 annual walk-forward windows, and at least a 3-year final holdout. Evidence is conditional at best.
- Fewer than 16 reliable years is presumptively insufficient for a definitive pass. Such data may support prototypes; an exception cannot weaken this rule after results are viewed.

The manifest records exact first/last dates, row counts, provider version, and checksums for pre-holdout and holdout partitions. Exploratory code receives no holdout path or credentials.

## 3. Nested chronological design

Within the pre-holdout history:

1. Begin with at least 8 years of training data when available.
2. Use the next 2 years as an inner validation window for the small preregistered parameter grid.
3. Freeze the selected rule and test it over the next 12 months.
4. Advance by 12 months, expand the training information set, roll validation forward, and repeat.
5. Concatenate the untouched one-year test ledgers into a stitched OOS path.

If data availability makes those lengths infeasible, the statistical reviewer must set an alternative before strategy results are observed. Longer non-overlapping summaries aggregate adjacent test years so that consistency is not overstated by overlapping windows.

## 4. What may be selected inside each fold

Only choices explicitly registered for the candidate family may be selected, such as a small portfolio-size set, a rank buffer, or one of a few conservative signal lags. The outer test cannot change:

- factor formula or direction;
- point-in-time availability rule;
- security-type exclusions;
- missing-data treatment;
- cost-model definition;
- contribution timing;
- benchmark construction; or
- the family-level primary metric.

If a model is simple enough not to require fitting, the same frozen rule is carried through each outer test rather than pretending repeated “training” adds information.

## 5. Candidate and hyperparameter discipline

- Register a bounded grid before execution and store it with a checksum.
- Assign one hypothesis ID per economic claim and link all variants to it.
- Use nested validation for parameter choice; never choose with outer-test or final-holdout performance.
- Report the full stability surface and the fraction of neighbors with the same sign, not only the maximum.
- Treat weekday, minute, and execution-window searches as a separate family with their own testing penalty.
- A post-result rule change creates a new experiment generation. Prior test periods then become development data for the new generation.

## 6. Multiple-testing and uncertainty plan

Use monthly net return differences as the main statistical series and preserve cross-sectional/serial dependence with block or stationary bootstrap methods. The final method and block-length rule are frozen before composite results.

The audit includes:

1. confidence intervals for annualized active return, drawdown, and rolling-win proportions;
2. Benjamini–Hochberg false-discovery control at `q = 10%` within declared exploratory single-factor families;
3. Romano–Wolf dependence-aware stepdown family-wise control at `alpha = 5%` for confirmatory comparisons;
4. Hansen superior-predictive-ability as the primary whole-search test and White Reality Check as a conservative sensitivity, separately versus each benchmark;
5. deflated/probabilistic Sharpe analysis with a 95% pass threshold, including raw and correlation-adjusted trial counts and non-normal returns;
6. CSCV/probability-of-backtest-overfitting as a diagnostic only, with at most 20% preferred, 20–40% a warning, and above 40% a serious warning;
7. at least 10,000 reproducibly seeded time-series resamples with block-length sensitivity; and
8. selection-aware effect sizes and explicit limitations where few independent regimes make asymptotic inference fragile.

No single statistical test decides success. Economic thresholds, uncertainty bounds, stability, and falsification must agree.

## 7. Robustness and falsification suite

Run the frozen candidate through:

- alternate liquid-universe definitions and a large-cap-only subset;
- exclusion of smallest/least-liquid securities;
- raw, sector-neutral, and appropriate sector-specific accounting treatment;
- longer fundamental lags and stale-data exclusions;
- weekly, biweekly, monthly, quarterly, and hybrid rebalance policies as preregistered;
- expected and stressed commission, spread, slippage, delayed fill, and no-fraction cases;
- neighboring portfolio sizes, score thresholds, buffers, and position caps;
- bull/bear, high/low volatility, inflationary/disinflationary, and rate-regime diagnostics where sample size supports them;
- starting-date perturbations and bootstrap resamples;
- removal of best name, top contributors, and best year;
- industry and factor concentration analysis;
- alternative benchmark proxy and expense assumptions; and
- contribution cash arriving after rather than before the decision cutoff.

Regime labels are diagnostics unless they were defined from data available at the time. They must not become retrospective switches.

## 8. Holdout release checklist

The final holdout remains sealed until all items are signed and dated:

- data provider/version, period, schema, and checksums frozen;
- data-quality report approved for definitive research;
- universe and permanent-identifier rules frozen;
- signal formulas, directions, lags, missingness, and neutralization frozen;
- portfolio size, weights, contribution routing, buffers, exits, and risk constraints frozen;
- execution and all cost scenarios frozen;
- benchmark definitions and contribution-ledger reconciliation frozen;
- success thresholds and pass logic frozen;
- candidate-search registry complete, including failures;
- source code/config checksums and environment lock recorded;
- adversarial reviewer has reviewed the design; and
- one named operator is authorized to run the final evaluation exactly once.

## 9. Final-holdout decision

The final run writes results to a new read-only result directory and updates the registry. If it passes, it proceeds to the complete adversarial outcome review. If it fails, the recorded candidate fails. The holdout may be analyzed to learn why, but not reused to certify a redesigned strategy.

Accidental access must be recorded immediately in `handoff.md` and `research/decision_log.md`; the contaminated period cannot continue as an untouched final holdout.

## 10. Experiment governance

Before running anything, add a row to `research/experiment_registry.csv` with hypothesis, purpose, parent, data/universe/signal/portfolio/cost versions, dates, seed, grid URI, and expected primary metrics. After execution, append result URI, decision, failure reason, timestamps, and checksum. Registry history is append-oriented; failures remain visible.

Each result bundle contains configuration, code/environment identity, input manifests, metrics, monthly returns, trades, holdings/exposures, QA output, and logs. A result without a registry row is exploratory debris and cannot support a conclusion.
