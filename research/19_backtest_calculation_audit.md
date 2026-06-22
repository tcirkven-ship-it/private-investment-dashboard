# Phase 1A forensic backtest calculation audit

**Audit experiment:** EXP-0011  
**Method:** Independent recomputation from preserved CSV ledgers, trade files, selections, raw price snapshots, frozen hashes, and separate audit code  
**Decision impact:** Headline arithmetic reproduces; methodological qualifications do not reverse FAIL and reduce evidentiary strength.

## Reproduction result

The saved ledgers reproduce the reported values within floating-point tolerance.

| Full stitched metric | C03-M | SPY | QQQ |
|---|---:|---:|---:|
| Contributions | $214,500 | $214,500 | $214,500 |
| Ending value | $1,570,117.47 | $820,567.00 | $1,403,434.25 |
| Annualized TWR | 20.5457% | 14.0293% | 19.3013% |
| XIRR | 21.4228% | 14.7987% | 20.2863% |
| Annualized volatility | 18.8795% | 17.1385% | 20.6517% |
| Maximum drawdown | −32.4066% | −33.7179% | −35.1212% |
| Explicit modeled cost | $7,450.16 | $407.35 | $407.35 |
| Gross discretionary turnover | 177.6553% | n/a | n/a |

The maximum independent-vs-reported metric difference was below `2.4e-10`. Eight deterministic accounting tests passed. Strategy, SPY and QQQ external cash-flow series are exactly equal.

The holdout convention also reproduces: opening wealth is inserted as the first negative XIRR flow while the daily TWR path remains the continuation return path. The holdout annualized TWR of 34.4982%, XIRR of 34.5557%, ending wealth and 172.0% turnover reproduce. “Total contributed” in holdout metrics includes opening wealth and therefore must not be interpreted as new 2023–2026 deposits.

## Contributions and portfolio accounting

| Audit item | Finding |
|---|---|
| USD 250 schedule | 858 positive flows totaling $214,500. |
| Timing | 831 contributions were posted on the scheduled Friday session itself; 27 market-holiday Fridays moved to a later session. Code uses first session **on or after** Friday, not always “the next session” as written. |
| Cash | No negative closing cash; reported minimum was zero. |
| Fractional shares | Modeled throughout. Quantities are synthetic adjusted-price units, not raw broker share quantities. |
| Dividends and splits | Embedded in Adjusted Close exactly once at the return-series level. No explicit dividend cash, withholding, payment date, split-unit or reinvestment ledger exists. |
| Settlement | Sale proceeds are immediately reusable. T+1 settlement/unsettled-cash restrictions are not modeled. |
| Uninvested cash | Closing cash is recorded and nearly always exhausted because fractional buying is permitted. Whole-share residual cash was not tested. |
| Trade reconciliation | 6,352 C03-M trade rows; commissions and impact sum exactly to daily ledgers. |
| Contribution matching | Strategy/SPY/QQQ external flows are byte-equivalent by date and amount. |
| Deposit treatment in TWR | Daily identity `(NAV_t − flow_t) / NAV_(t−1) − 1` holds to about `5.4e-16`; this treats the flow as a close-boundary external cash flow. |
| XIRR | Independent 365.2425-day bisection reproduces every reported full-period XIRR. |

### Adjusted-close accounting limitation

Every strategy fill uses the yfinance Adjusted Close as both execution and valuation price. This is a coherent synthetic total-return-unit approximation, and the arithmetic is internally consistent. It is not an auditable raw-share portfolio:

- adjusted closes are not tradable prices;
- cash dividends are implicitly reinvested without a separate decision, commission, withholding or residual-cash event;
- splits and other adjustments are not represented as quantity changes;
- share quantities cannot be reconciled directly to broker statements; and
- mergers, bankruptcies, delistings and terminal proceeds are absent.

This does not create the reported TWR arithmetic error, but it prevents the ledger from satisfying the original corporate-action and execution standard.

## Return and risk calculations

| Calculation | Verification and qualification |
|---|---|
| Daily return | Independently reproduced from NAV and external flows. |
| TWR | Product of daily subperiod returns; independently reproduced. |
| Annualized TWR | `(1 + total TWR)^(252 / observations) − 1`; independently reproduced. Calling this CAGR would be misleading for a contribution portfolio. |
| Volatility | Sample standard deviation of daily TWR × √252; reproduced. |
| Maximum drawdown | Drawdown of cumulative daily TWR wealth; reproduced. |
| Active return | Difference between separately annualized strategy and benchmark TWRs. This is not the same statistic as compounding a monthly active-return-difference series. |
| Rolling returns | Monthly compounded strategy and benchmark returns are compared over fixed windows. Full stitched QQQ win rates are about 61.35% (3y), 52.52% (5y) and 27.85% (10y); the original report omitted 10y. |
| Costs | Fixed per-order commission and linear adverse impact are charged and reconcile. No historical bid/ask, FX, tax, settlement or missed-fill cost. |
| Turnover | Gross discretionary buys plus sells divided by average NAV and calendar years. Full gross is 177.66%; sells-only is about 88.72%. The protocol explicitly selected gross, so the gate fails. |

Thirty-four monthly selection dates also carried $8,500 of new external contributions. Purchases made on those dates are classified entirely as discretionary, so gross discretionary turnover is slightly overstated. Correcting that classification cannot plausibly bring 177.66% below the 100% gate.

### Bootstrap qualification

The reported interval is reproducible from the implemented code, but the procedure does not match the preregistered test:

- it is a two-sided, non-studentized circular moving-block percentile bootstrap;
- it resamples arithmetic monthly strategy-minus-benchmark return differences;
- it annualizes the resampled arithmetic mean as `(1 + mean)^12 − 1`;
- it is not the promised one-sided studentized lower bound;
- it is not a whole-search reality/superiority test; and
- no deflated-Sharpe probability was calculated.

Its QQQ interval of approximately −3.58% to +4.81% includes zero. A skeptical paired compound-return block calculation also includes zero (approximately −3.88% to +5.95%). Thus the implementation mismatch does not rescue C03-M; it means the exact preregistered uncertainty gate was not completed.

## Signal and execution timing

| Audit item | Finding |
|---|---|
| Signal observation | Last trading session of each month. |
| Momentum window | Adjusted total return from 252 sessions before the signal date to 21 sessions before it. |
| Ranking | Calculated from month-end data after eligibility filters. |
| Decision/fill | First subsequent trading session. Across 197 selections, calendar lag was 1–4 days and same-day count was zero. |
| Execution price | Subsequent-session Adjusted Close plus separately charged adverse impact—not an attainable raw close or broker order. |
| Missing prices | Panels forward-fill up to three sessions. No audited fill lacked an Adjusted Close, but the code can carry/omit stale values without an explicit suspension-event ledger. |
| Corporate actions | Only those embedded by the current adjusted series; no explicit event processing. |
| Universe entry/exit | No historical OEF membership entry/exit. Current members are eligible backward once sufficient price history exists. |

No same-day month-end look-ahead was found in C03-M's signal/fill schedule. The larger look-ahead problem is universe membership and current sector/share-class information projected backward.

## Concentration-control implementation

The selection rule uses a 25% sector cap. For 30 equal-weight names, integer selection permits at most seven names per sector (about 23.33% at target). The diagnostic code, however, counts a “sector drift violation” only above 30%.

- Full stitched sessions above 25%: approximately 314.
- Full stitched sessions above 30%: 18.
- Maximum current-label sector weight: about 33.14%.

The published “18 breaches” is correct only for the separate 30% drift-review threshold, not for the 25% target cap. The reports should distinguish those thresholds.

## Holdout-integrity audit

### What the repository supports

- Candidate configuration was registered before individual-stock results.
- EXP-0009 completed before the recorded holdout freeze.
- Freeze file records C03-M, known pre-holdout failures, no intended rule change, and hashes.
- Current engine, strategy, runner, configuration and accounting-test hashes match the freeze record.
- The strategy holdout output was generated after the freeze, and no post-result parameter change is evident.
- The invalid truncated-lookback run was preserved rather than substituted silently.

### What it does not support

EXP-0006 completed before the strategy freeze and wrote SPY/QQQ ledgers through 2026-06-18. The engine was then modified and the strategy/runner files were created or modified before the freeze. Therefore the 2023–2026 benchmark path and values were available during strategy-code development. Raw market files also contained the full period; there was no physical or logical holdout separation.

Consequently:

- `access_count_before_freeze = 0` cannot mean zero access to all holdout information;
- “genuinely untouched holdout” is unsupported under the written protocol;
- the defensible description is **one-batch strategy evaluation under frozen hashes after pre-holdout failure**, not sealed final holdout; and
- absence of tuning to the strategy outcome is supported by chronology, but impossible to prove from repository artifacts alone.

All ten price variants were evaluated in that batch. They were registered diagnostics, not newly selected after observing results. The failed truncated-lookback execution should ideally have had its own audit-registry row; preserving its directory and note is transparent but less complete than the stated “every material run” standard.

## Overall forensic judgment

1. The headline numbers are computationally reproducible from the saved synthetic ledgers.
2. Benchmark cash flows and basic TWR/XIRR accounting are sound under the stated close-boundary convention.
3. The ledger is not a raw-share/corporate-action execution ledger.
4. The universe is structurally survivor-biased.
5. The bootstrap, multiple-testing and holdout controls do not fully match the preregistered protocol.
6. The holdout was not sealed because benchmark information was available before strategy freeze.
7. None of these findings upgrades C03-M; the correct decision remains FAIL for this generation.

Machine-readable audit evidence:

- `outputs/experiment_runs/EXP-0011/phase1a_calculation_audit.json`
- `outputs/experiment_runs/EXP-0011/phase1a_benchmark_diagnostics.json`
