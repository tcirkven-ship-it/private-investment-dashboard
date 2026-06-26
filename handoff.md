# Handoff

## Project

Recurring-Contribution Fundamental and Price-Based Stock Strategy Research

## Last updated

2026-06-26 19:45 CEST (Europe/Zagreb)

## Active checkpoint

The practical direction is now **daily/on-demand YF-QVP decision support** under `YF-DAILY-QVP-1.0.0`. Scores, full rankings, constrained portfolios and contribution illustrations may be generated after any fully completed daily session. Score, review and transaction clocks are independent; the user decides whether and when to act. No order placement or broker connection exists.

The implementation is `src/daily_screen.py`; configuration is `research/configs/daily_qvp_v1.json`. The command retrieves a timestamped yfinance universe, excludes incomplete current-session daily bars, applies the frozen Q/V/P factors, selects 30 equal-target names under sector/industry caps, compares with a prior integrity-passed run only, optionally classifies holdings, and writes CSV/Markdown/HTML plus checksums. Sixty-three tests pass.

Scanner-integrity correction is complete. The invalid `mechanics_smoke_2` compact files were generated from a reconstructed Checkpoint 2 snapshot containing the old 698-name eligibility table, then published by an unconditional copy block. They are preserved under `outputs/audit/superseded_invalid_current_output/`. Publication now rejects rehearsal IDs, cached/external snapshots, source snapshots older than invocation, prior rankings without a passing manifest, eligible/ranking mismatches, and undocumented missing-score omissions.

The passing one-command run is `2026-06-22T172514Z`, based on immutable snapshot `data/prospective/daily_qvp/snapshots/2026-06-22T172514Z/raw`. It screened 2,205 names, enriched 1,875, retained 1,069 eligible, and fully QVP-scored 1,033; all 1,069 eligible rows are present in the ranking and the 36 unscored rows carry factor-missing flags. Reconciliation against the old 698 is 693 overlap, 376 additions and five removals. The earlier 1,072 reset count differs by a net three because five names fell out of the current USD 2 billion screen and KSS/NUVB entered. Current compact outputs are in `outputs/final/`; the run manifest classification is `current_decision_support_integrity_passed`.

The isolated frozen-Price historical study is complete under EXP-0019 through EXP-0022. It did not modify the scanner, current QVP formula or compact current outputs. An initial 80-history fallback and attribution-scope failure are preserved. The decisive `PRICE-WF-1.1.0-FULL-HISTORY` pull completed maximum histories for all 1,069 current eligible stocks plus SPY/QQQ with zero failures. Membership is still current-survivor biased.

No P4 configuration passed the 2015–2020 development gates; even the lowest-turnover monthly/rank-2N variants required 584%–629% annual gross turnover. The frozen diagnostic P4/N=30/monthly/rank-60 reference returned 12.85% annualized in 2021–2025 versus 14.40% SPY and 15.14% QQQ, with −21.49% maximum drawdown, 19.76% volatility and 681.70% turnover. Implementation validity passes, standalone P4 evidence fails, and true historical-universe inference remains inconclusive. P1–P3 had much higher biased point returns but 38%–41% volatility and 493%–725% turnover; they are not promoted replacements. Current QVP and Price top 30 overlap only in ENS, so Quality/Value incremental effect remains unproven.

`YF-FWD-SIMPLE-001`/EXP-0017 is preserved as `active_evidence_ledger_decoupled`. Its immutable activation manifest is historical. Month-end no longer gates practical information, and scanner runs do not enter prospective performance evidence. The evidence ledger still has zero contribution events, zero paper decisions and zero transactions.

Research status remains mixed: price-only C03-M and nine variants failed the original approval standard; current QVP calculation/semantic engineering passes; no credible long historical QVP test exists; and repeated walk-forward QP/QGP plus selection-frequency tests remain unfinished. `research/57_research_completion_plan.md` specifies the honest proxy track and the data-source choice required for reliable full QVP.

Reset documentation is `research/54`–`research/58`. The old execution-heavy and month-end activation documents remain preserved as historical evidence, not current practical instructions.

Price Generation 2 (`research/67`–`research/71`) tested 20 new Price-only candidates across families A–E. No candidate passed every development gate. The Gen2 P4_CONTROL formula was corrected and reconciled.

Price reconciliation (`research/72`), E3 diagnostic audit (`research/73`), persistence experiment (`research/74`–`research/76`) are complete.

A3 exit2 — the only near-finalist from the persistence experiment (24.69% dev return, 64% TO, 6/6 SPY wins, missed one gate by 0.09pp) — was selected for confirmatory evaluation on untouched 2021–2025. It PASSES all evaluation gates after 10bps cost adjustment: 23.04% net return vs 14.40% SPY and 15.14% QQQ, 63% TO, −28.44% max DD, 3/5 SPY wins, 3/5 QQQ wins. It is approved as the frozen Price candidate for the next QVP weight experiment (`research/77`–`research/79`).

SMA150 exit experiment (`research/80`–`research/82`) tested V0 rank-exit2, V1 SMA-only, V2 OR and V3 AND exit variants against the frozen A3 signal. V1 and V2 produced 383% turnover (approx 6.1× V0, 2.55× the 150% ceiling). V3 (AND rule) had 22.18% return, 65% TO, −29.42% DD — no improvement over V0. Decision: RETAIN BASELINE RANK EXIT2.

Instrumentation audit (`research/83`) and state-machine audit (`research/84`) discovered a critical implementation defect: the exit2 confirmation counter was cleared for ALL survivors each month, preventing any rank-based exit from ever triggering (0 exits in 5 years). Corrected evaluation: A3 exit2 with fixed state machine produces 424% turnover and fails all gates.

Contamination matrix (`research/85`) maps all affected modules and documents. Corrected persistence rerun (`research/86`–`research/87`) closes the Price persistence path under the current dataset — no corrected specification passes all development gates. Scanner confirmed unaffected.

Decision log and experiment registry updated with supersession entries (DEC-060 through DEC-063, EXP-0023/EXP-0024).

QVP Generation 1 audit (`research/92`) fixed B2 P100 self-overlap bug (22/30 → 30/30). Historical P100 simulator corrected (holding period tracking, immediate rank-60 exit). Status: ADDITIVE QVP ARCHITECTURES FAIL PRICE-IDENTITY GATE; PERFORMANCE EFFECT UNTESTED.

Price-gated overlay design (`research/93`–`research/96`): G3 (Quality veto) retains 21-22/30 of P100 top 30. Decision: ADOPT G3 QUALITY VETO FOR SHADOW MODE.

Quality-veto validation (`research/97`–`research/99`) built historical Quality extraction from annual statements. Data covers only 2022+. Current cross-section: A3 G3 retains 21/30 with improved median Quality (0.459 vs 0.333 eligible-universe percentile). Decision: INCONCLUSIVE DUE TO QUALITY-DATA COVERAGE.

Shadow system activation (`research/100`–`research/101`): four immutable ledgers initialized. Activation status: INITIALIZED.

Corrected practical QV backtest (`research/106`–`research/108`): Fixed critical B2 score bug. All models beat SPY but fail 200% TO gate (547-610%).

Decision correction (`research/109`–`research/111`): NO MODEL PASSES — TO OVERRIDE REQUIRED. Selected: M1 B2 QUALITY VETO.

Database release verification: NOT YET VERIFIED. CI proof required.

Corrected release migration:
- Atomic transaction wrapping (BEGIN/COMMIT)
- Owner-only RLS (all tables use is_owner() check)
- Append-only transactions (owner has INSERT+SELECT only, no UPDATE/DELETE)
- Model immutability (prevent_published_mutation trigger, CHECK constraints)
- Portfolio deletion prevention (prevent_portfolio_deletion trigger)
- Cascading protection (ON DELETE RESTRICT on transactions)
- Single authoritative cash source (no starting_cash — transactions only)
- 31 RLS policies (strict owner isolation with second-user denial)
- Corporate-action CHECK constraints
- idempotency_key UNIQUE on transactions and checksum UNIQUE on imports
- GitHub Actions workflow (.github/workflows/database-release.yml)

CI must pass before deployment. Actions workflow requires Docker for local
Supabase PostgreSQL. Current system lacks Docker — proof deferred to CI run.

Routes connected to Supabase: /model (async server component with real query).
Remaining routes (holdings, transactions, rebalance) still show empty states
awaiting full integration in a subsequent task.

82 tests pass (73 original + 4 instrumentation + 5 state machine).

### Superseded Checkpoint 3 decision

Phase 1B Checkpoint 3 is **complete with an activation-readiness FAIL**.
`YF-FWD-001`/EXP-0013 remains `registered_not_started`; activation was not
performed.

The inactive hypothesis is frozen for readiness as YF-QVP, Quality + Value +
Price, N=30, equal target weights, monthly selection, rank-60 retention,
quarterly correction, USD 250 on the first session on/after Friday, maximum
three underweights, fractional primary, and separate contribution-matched SPY
and QQQ ledgers. YF-P/YF-QP/YF-QVGP are ablations only. N=20/40, whole shares,
and USD 500 biweekly are operational sensitivities.

A yfinance-only no-return intraday smoke test archived six securities at 1m,
5m and 15m intervals. Its superseded raw tree was removed after retaining the
compact manifest under `outputs/storage_cleanup/retained_manifests/`. Five-minute bars were
selected for a 15:45–15:55 America/New_York paper limit window: 60 sessions,
three window bars/session, zero duplicate timestamps and zero missing OHLC in
the window. One-minute data retained only seven sessions and had 11 missing
window rows; 15-minute data could not resolve a ten-minute lifecycle.

Versioned universe-refresh and raw-share ledger code is in `src/paper/`.
Forty-four repository tests pass, covering contributions, fractional/whole
orders, commissions, adverse prices, full/partial/unfilled orders, duplicate
prevention, raw-cash constraints, dividends, forward/reverse splits,
missing/stale prices, eligibility/rank exits, trimming, concentration, corporate
exceptions and benchmark parity.

The final two complete rehearsals under `outputs/experiment_runs/EXP-0015/rehearsal_3`
and `rehearsal_4` are byte-identical. They used the same Checkpoint 2 score/raw
snapshot and archived 2026-06-18 intraday bars; they are not prospective trades
or recommendations. SPY and QQQ received identical flow/execution rules.

Readiness fails two hard gates:

1. the workspace is not a Git repository, so no required Git commit hash can be
   recorded; and
2. IBKR Tiered base/fractional commissions are modeled, but exchange, clearing,
   regulatory and pass-through fees are not completely frozen.

Checkpoint 3 deliverables are `research/35` through `research/40`,
`research/configs/yfinance_forward_readiness_v1.json`,
`outputs/experiment_runs/EXP-0015/`, and
`outputs/final/yfinance_activation_checklist.md`.

Next action: establish version control, implement/freeze the complete fee
schedule, regenerate hashes/tests/rehearsals under a new readiness version, and
request review. Even a later readiness PASS would still require a separate
explicit instruction to activate.

Phase 1B Checkpoint 2 is **complete with a conditional pass for current research
implementation**. This is not strategy approval.

EXP-0014 constructed a non-truncated yfinance-only current universe using 110
sector × market-cap queries. The maximum query leaf was 106, so Yahoo's
250-result cap was not reached. Counts were 2,207 unique screened names, 1,876
enriched at the preliminary USD 2B threshold, and 698 final eligible domestic
USD nonfinancial/non-Real-Estate issuers. All 698 final ticker bundles completed
with zero endpoint errors.

The redundant uncompressed raw tree was removed after full checksum reconstruction.
Its retained logical manifest is
`outputs/storage_cleanup/retained_manifests/checkpoint2_full_universe_manifest.json`; SHA-256
is `d94f0498e79eddf8b3c96b2b0c56d9dec82fdb9460a4e5b3f30ac6ee5c2c3373`.
The 790.78 MB logical snapshot remains in a reconstructable gzip
content-addressed manifest at
`data/archive/yfinance_phase1b_cas/manifests/2026-06-22T_currentZ.json`.

Version `YF-ALIAS-1.0.0` and `YF-FACTOR-1.0.0` are implemented and tested.
Twenty-two tests pass. Semantic QA demoted `OP_MARGIN`, `DILUTION`, and
`EBIT_EV`; shareholder yield remains rejected. The frozen current primary sets
are:

- Price: `M12_1`, `M6_1`, `TREND200`, inverse `VOL252`;
- Quality: `ROA`, `GPA`, `FCF_MARGIN`, inverse `DEBT_ASSETS`;
- Value: `FCF_YIELD`, `SALES_EV`, `BOOK_MARKET`; and
- Growth: `REV_GROWTH`, `MARGIN_CHANGE`.

Strict current scores exist for 698 YF-P, 676 YF-QP, 674 YF-QVP, and 672
YF-QVGP names. They are research inspection tables, not approved holdings.
`YF-QVP` is proposed—but not activated—as the primary prospective candidate;
the other three remain ablations. N=30 is proposed with N=20/40 sensitivities.

Checkpoint 2 deliverables are `research/29` through `research/34`,
`outputs/experiment_runs/EXP-0014/`, and
`outputs/final/yfinance_current_research_report.md`.

`YF-FWD-001`/EXP-0013 remains `registered_not_started`. No historical return
optimization, prospective activation, target portfolio, brokerage order, or
live recommendation occurred. Next action requires explicit review of the
factor freeze, paper-ledger tests, fill/cost convention, and proposed success
criteria before any activation.

Phase 1B first checkpoint is **complete** under a strict yfinance-only data
constraint. Work stopped before factor-performance testing, strategy
optimization, target-portfolio generation, paper orders, or live action.

EXP-0012 audited yfinance 1.4.0 on 110 stocks—ten from each Yahoo sector—using
a sample constructed only with `yf.screen(EquityQuery)`. Its superseded raw
sample was removed after retaining the compact manifest at
`outputs/storage_cleanup/retained_manifests/checkpoint1_capability_manifest.json`;
the original manifest hash is `f76313258c9bd11c768833bba5ad5753598f442dc540e64660d3fffc72cf2f91`.

Key capability results:

- zero endpoint exceptions across the 110-stock run;
- annual and trailing income/balance/cash-flow frames were nonempty for all
  names; quarterly income/cash flow were nonempty for 105/103;
- median history was five annual and six quarterly periods;
- statement schemas were highly heterogeneous: 107–108 unique row sets;
- current valuation, shares, estimates and revisions had broad coverage, but
  are not historical observations;
- the current US nonfinancial/non-Real-Estate analysis subset contained 66
  names; most proposed raw factor inputs covered at least 98.48%; and
- shareholder-yield inputs covered only 39.39% and were rejected.

The snapshot inventory contains 2,324 files (142,856,913 bytes); all 110 ticker
manifests and all 2,200 registered endpoint hashes passed validation.

The proposed family is YF-P, YF-QP, YF-QVP and YF-QVGP with equal category
weights. It is proposed for review, not performance-tested or activated.
`YF-FWD-001`/EXP-0013 is reserved for a minimum 36-month prospective paper
experiment but remains `registered_not_started`.

Phase 1B checkpoint artifacts:

- `research/22_yfinance_capability_audit.md`
- `research/23_yfinance_factor_dictionary.md`
- `research/24_yfinance_data_coverage.md`
- `research/25_yfinance_strategy_specification.md`
- `research/27_yfinance_forward_protocol.md`
- `research/28_yfinance_limitations.md`
- `research/configs/yfinance_phase1b_checkpoint1.json`
- `outputs/experiment_runs/EXP-0012/`

`research/26_yfinance_exploratory_results.md` and
`outputs/final/yfinance_strategy_card.md` are intentionally deferred because
the checkpoint prohibits strategy testing/selection before review.

Phase 1A audit and gap analysis is **complete**. It preserves every existing
experiment and the current FAIL decision. No new strategy optimization,
factor-formula change, or holdout-based selection was performed.

The corrected scope is: C03-M and the nine tested price variants failed the
best-effort approval standard. The evidence does not establish failure of
momentum generally, direct-stock strategies generally, or untested
price-plus-fundamental strategies. The original mandate remains incomplete.

## Current phase and decision

The preliminary Phase One generation and Phase 1A audit are complete.

Preserved decision: **FAIL for C03-M and the tested price-only generation**. No active individual-stock strategy is approved for live use. Phase Two is not authorized or implemented.

The decisive report is `research/16_final_recommendation.md`; the standalone investor report is `outputs/final/final_research_report.md`.

## Objective tested

Determine whether a transparent, long-only individual-stock strategy funded with approximately USD 250 weekly can demonstrate credible after-cost out-of-sample performance against separate contribution-matched SPY and QQQ benchmarks.

The primary frozen candidate was C03-M: 30 equal-weight current-OEF large-cap stocks selected monthly on 12–1-month momentum, with a rank-60 buffer, quarterly weight correction, weekly underweight-filling contributions, fractional units, and explicit expected/stressed costs.

## Data used

- FRED immutable benchmark references under `data/raw/fred/2026-06-21/`.
- Validated SPY/QQQ yfinance histories under `data/raw/yfinance/2026-06-21/`.
- Official iShares OEF holdings workbook dated 2026-06-18 under `data/raw/universe/2026-06-21/`.
- 101 US USD OEF equity rows normalized to 100 issuer-deduplicated tickers.
- Maximum-history yfinance price/action extracts for all 100 tickers under `data/raw/yfinance/oef_2026-06-21/`.

All 100 ticker files passed checksums, schema, chronology, positive-price, nonnegative-volume and action checks. Ninety-one names had a 252-session lookback at the 2010 start; 97 did by 2015.

The evidence ceiling remains exploratory because the current 2026 universe is projected backward and inactive securities, delisting outcomes, permanent identifiers and historical point-in-time fundamental vintages are unavailable.

## Experiment history

- EXP-0004: FRED file validation — pass.
- EXP-0005: SPY/QQQ yfinance validation and FRED reconciliation — pass.
- EXP-0006: eight accounting unit tests plus six integrated contribution/benchmark checks — pass.
- EXP-0007: official OEF universe extraction — pass.
- EXP-0008: 100-stock price/action validation — pass.
- EXP-0009: preregistered pre-holdout price-family test — fail.
- EXP-0010: one-use 2023–2026-06-18 holdout and robustness audit — fail.

An initial EXP-0009 implementation run accidentally truncated the prior-252-session lookback. It was preserved under `outputs/experiment_runs/EXP-0009/invalid_run_lookback_truncation/`, fixed without changing research parameters, and rerun before the holdout.

## Main results

### Stitched 2010–2026 survivor-biased point estimates

| Metric | C03-M | SPY | QQQ |
|---|---:|---:|---:|
| Total contributed | $214,500 | $214,500 | $214,500 |
| Ending value | $1,570,117 | $820,567 | $1,403,434 |
| Annualized TWR | 20.55% | 14.03% | 19.30% |
| XIRR | 21.42% | 14.80% | 20.29% |
| Maximum drawdown | -32.41% | -33.72% | -35.12% |

The full-sample C03-M point estimate was +6.52 percentage points annualized TWR versus SPY and +1.24 versus QQQ. This does not overcome the structural data bias.

### Final holdout

- Active annualized TWR: +11.47 points versus SPY, **-0.83 point versus QQQ**.
- Active XIRR: +11.66 points versus SPY, **-0.50 point versus QQQ**.
- Stressed active TWR versus QQQ: **-0.99 point**.
- Annualized turnover: **172%**.
- Maximum sector weight reached 33.14%; sector-drift cap breached on 18 sessions.

### Robustness

- Stitched QQQ active-return bootstrap 95% interval: **-3.58% to +4.81%**; probability positive 63.1%.
- Only 2 of 10 registered candidates were positive versus both benchmarks in both pre-holdout and holdout; those sizes had 258% and 875% holdout turnover.
- Removing the best year reduced QQQ active return to +0.98 point.
- Starting in 2015 reduced QQQ active return to +0.53 point.
- Top stock MU represented approximately 7.45% of total portfolio profit, so one-stock dependence was not the primary failure.
- Weekly, biweekly and monthly contribution timing had nearly identical return rates; monthly reduced cost and workload.

## Why the strategy failed

1. Current-membership survivorship bias and missing delisting outcomes.
2. No credible historical point-in-time fundamentals; requested fundamental composites were not historically testable.
3. Final-holdout and stressed-cost underperformance versus QQQ.
4. Turnover far above the 100% cap.
5. QQQ uncertainty interval includes zero.
6. Parameter and rolling-period instability.
7. Sector drift and excessive operational burden.
8. IBKR's reviewed MOC workflow does not support fractional shares, so the modeled next-close convention is not literally implementable for fractional MOC orders.

These are structural/critical failures; a conditional pass is prohibited.

## Final deliverables

- `research/00_executive_summary.md`
- `research/10_results.md`
- `research/11_robustness_and_falsification.md`
- `research/12_execution_timing.md`
- `research/13_portfolio_size.md`
- `research/14_weekly_investment_playbook.md`
- `research/15_risks_and_failure_modes.md`
- `research/16_final_recommendation.md`
- `research/17_phase_two_options.md`
- `outputs/final/final_research_report.md`
- `outputs/final/final_decision.json`
- `outputs/final/strategy_card.md`
- `outputs/final/phase_one_research_results.xlsx`
- verified charts under `outputs/final/charts/`

The final workbook SHA-256 is `df05dc886856d30a7c5c02d7114ea11fffb3cd142a0078144b3549bb9427785b`.

## Final holdout status

**Unavailable for future certification:** 2023-01-01 through 2026-06-18.

Phase 1A found that the strategy outcome was generated in one batch after
frozen hashes, but complete SPY/QQQ benchmark paths through 2026-06-18 existed
before the strategy-code freeze and raw data were not access-separated. The
period is therefore not a strictly untouched protocol-compliant holdout. There
is no evidence that the strategy outcome was tuned against before its run.

It cannot be reused to certify a redesigned strategy.

## Phase 1A forensic findings

- Independent calculations reproduce ending values, annualized TWR, XIRR,
  volatility, drawdown, costs and frozen gross turnover within numerical
  tolerance.
- The engine is a synthetic Adjusted-Close total-return-unit ledger, not a
  broker-reconcilable raw-share/dividend/corporate-action ledger.
- Contributions map to the first session on or after Friday, not always the
  next session after Friday.
- The reported bootstrap is non-studentized and does not implement the full
  preregistered uncertainty/multiple-testing procedure; its QQQ interval still
  includes zero.
- The selector targets a 25% sector cap, while the reported 18 breaches count
  only sessions above a separate 30% drift threshold. About 314 stitched
  sessions exceeded 25%.
- Gross discretionary turnover was 177.66%; sells-only/half-gross was about
  88.7%. The frozen gate explicitly used gross, so FAIL is unchanged.
- Ten-year rolling QQQ consistency was weak (about 27.9% winning windows).
- Factor diagnostics show the expected positive momentum and mega-cap tilts,
  but are descriptive only because they inherit the survivor-biased universe.

## Phase 1A deliverables

- `research/18_research_audit_and_gap_analysis.md`
- `research/19_backtest_calculation_audit.md`
- `research/20_data_requirements_and_vendor_matrix.md`
- `research/21_research_continuation_decision.md`
- `outputs/final/corrected_executive_summary.md`
- `outputs/experiment_runs/EXP-0011/phase1a_calculation_audit.json`
- `outputs/experiment_runs/EXP-0011/phase1a_benchmark_diagnostics.json`

## Required investor decision

Before any new experiment, choose one evidence tier:

1. research-grade paid data and full original-mandate rebuild;
2. a paid but narrower, explicitly non-equivalent study; or
3. zero-cost forward paper evidence for at least 3–5 years.

Under a strict zero-cost constraint, only option 3 is currently defensible.

## Operational recommendation

- Do not deploy C03-M or any observed high-return size variant as a validated active strategy.
- Keep contribution-matched passive ETFs as the decision baseline; exact allocation requires separate investor suitability, tax and currency decisions.
- C03-M may be forward paper-tracked only.
- Any continued zero-cost research should build prospective SEC as-filed fundamentals using an owner-provided compliant contact identity and archive dated universe/event snapshots.

## Optional next step

Phase Two requires explicit approval. The preferred no-cost option is a local forward-research ledger or spreadsheet that validates data and produces paper-only ranks/orders. No broker connection, credential storage, order routing or live automation should be built from this failed generation.

## Instructions for the next agent

Read `AGENTS.md`, this file, `research/00_executive_summary.md`, `research/16_final_recommendation.md`, and the experiment registry. Do not reuse the completed holdout, promote N=10/N=20 after observing returns, or represent the historical result as survivor-bias-free. Do not implement Phase Two without explicit user approval.
