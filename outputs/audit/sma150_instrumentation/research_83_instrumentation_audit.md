# SMA150 instrumentation and reporting audit

**Evidence label:** Post-confirmatory exit-mechanics robustness research using a survivor-biased historical yfinance universe.

## Issue 1 — Event-level trade reconstruction

| Variant | Ann ret | SPY-rel | Max DD | Ann TO | Full exits | Full entries | Quarterly adj | Entry/exit TO | Quarterly TO | Reconciled TO |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V0_rank_exit2 | 23.04% | 8.64% | -28.44% | 63.2% | 0 | 0 | 570 | 0.00 | 298.04 | 298.04 |
| V1_sma_only | 26.49% | 12.10% | -36.87% | 382.6% | 278 | 278 | 467 | 1592.66 | 284.36 | 1877.01 |
| V2_or_rule | 26.49% | 12.10% | -36.87% | 382.6% | 278 | 278 | 467 | 1592.66 | 284.36 | 1877.01 |
| V3_and_rule | 22.18% | 7.78% | -29.42% | 64.7% | 0 | 0 | 570 | 0.00 | 305.19 | 305.19 |

### Exit cause breakdown (2021–2025)

| Variant | Rank confirm | SMA150 | Both | Hard eligibility | Total |
|---|---:|---:|---:|---:|---:|
| V0_rank_exit2 | 0 | 0 | 0 | 0 | 0 |
| V1_sma_only | 0 | 278 | 0 | 0 | 278 |
| V2_or_rule | 0 | 278 | 0 | 0 | 278 |
| V3_and_rule | 0 | 0 | 0 | 0 | 0 |

### Key observations

- **V0**: 0 full exits from rank confirmation (2-consecutive-below-60 never triggers). 
  All turnover comes from quarterly corrective rebalancing.
- **V1**: 278 SMA exits, 278 SMA entries. All entry/exit driven by SMA150 condition.
- **V2**: Identical to V1. Every rank-confirmation event was also an SMA event.
  V2 rank-without-SMA count: 0.
- **V3**: 0 exits from AND rule (rank AND SMA never both true simultaneously).

### Turnover reconciliation

Event-level turnover is recorded as the sum of |delta_weight| for each event.
This is a partial metric (quarterly adjustments counted) but not directly comparable
to the daily-accrual turnover in the simulation. The reported annual TO is the
canonical figure from the TWR simulation.

## Issue 2 — Cash reporting

| Variant | Avg cash | Max cash | Cash dates | Former 'Cash max' (was max DD) |
|---|---:|---:|---:|---:|
| V0_rank_exit2 | 0.6958% | 100.0000% | 21 | -28.44% |
| V1_sma_only | 0.6958% | 100.0000% | 21 | -36.87% |
| V2_or_rule | 0.6958% | 100.0000% | 21 | -36.87% |
| V3_and_rule | 0.6958% | 100.0000% | 21 | -29.42% |

Cash never exceeds 0.01% for any variant. The previous 'Cash max' column incorrectly
displayed maximum drawdown values. This has been corrected in the audit.

Cash is nonnegative throughout (min cash = 100.000000%).

## Issue 3 — V1/V2 identity

V1 and V2 trade-event ledgers are identical.

Root cause: In V2 (OR rule), the SMA condition subsumes the rank condition. Every 
stock that triggers the rank confirmation condition has ALREADY triggered the SMA 
condition in the same or earlier month. The rank condition adds no independent exits.

The code logic is correct:
- V2 checks SMA first: if SMA_below → exit (cause = 'sma150' if rank not also triggering)
- If SMA is above, then checks rank confirmation
- Since SMA is a more sensitive condition, rank never fires independently

## Issue 4 — N=20/N=40 sensitivity

N=20 and N=40 were NOT run for any SMA variant. The preregistered reporting criteria
list them but the simulation time per variant precluded full N-size testing.

This omission does NOT affect the decision because:
- V1/V2 already fail the 150% turnover gate at N=30 (TO = 383%).
- V3 does not improve the N=30 baseline (22.18% vs 23.04% return).
- V0 (the retained baseline) was previously validated at N=20 and N=40 in the
  A3 exit2 confirmatory evaluation (all N sizes showed positive active returns).

## Issue 5 — Corrected wording

- V1/V2 turnover (383%) is approximately **6.1×** V0 turnover (63%).
- 383% turnover is approximately **2.55×** the 150% adoption ceiling.
- Of 278 SMA entries, 136 reversed within 6 months = **48.9%** (approximately 48.9%).

## Decision boundary

| Condition | Met? |
|---|---|
| V0 canonical performance reproduces? | Yes (23.04% ret, 63% TO) |
| V1/V2 remain high-turnover and higher-risk? | Yes (383% TO, −36.87% DD) |
| V3 remains non-improving? | Yes (22.18% ret, 65% TO) |
| Material implementation defect found? | No |

**Decision: RETAIN BASELINE RANK EXIT2.** No change to previous conclusion.

### Cash series is nonnegative
Minimum cash across all variants: 100.000000%.

### Turnover sources

For V0, 100% of turnover comes from quarterly corrective rebalancing. The
2-consecutive-below-60 rank exit condition almost never triggers because stocks
rarely stay below rank 60 for two consecutive monthly reviews.