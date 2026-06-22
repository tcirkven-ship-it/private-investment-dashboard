# Phase 1B historical feasibility and storage

## Historical-use classification

- Price-history feasible: `M12_1`, `M6_1`, `RS63_MKT`, `TREND200`, `VOL252`, `DOWNVOL252`, `DD252`, and `LIQ63`. Any test on today's universe remains survivor-biased.
- Statement-history feasible with approximate lag: the statement-only Quality and Growth factors, using 90 calendar days after quarterly periods and 120 after annual periods. Currently retrievable statements may be restated, so this is not point-in-time evidence.
- Current/prospective only: `RS252_SEC`; every market-cap or enterprise-value factor (`EARN_YIELD`, `FCF_YIELD`, `EBIT_EV`, `SALES_EV`, `BOOK_MARKET`, `SHAREHOLDER_YIELD`). Current sector, market cap, and EV may not be projected backward. Historical shares were not reliable enough to construct denominators.
- Prospective archive only: estimates, revisions, recommendations, and earnings-history event signals.

The complete factor-by-factor classification is `outputs/experiment_runs/EXP-0014/historical_factor_feasibility.csv`.

## Storage implementation

The raw snapshot is 790.78 MB across 20,518 files. The deterministic gzip content-addressed archive references 151.53 MB and created 149.44 MB of unique compressed objects. Each logical path maps to a SHA-256 object in an immutable manifest; repeated identical files reuse the same object.

A measured lightweight weekly package—partition queries/responses, current enrichment info, key universe tables, and the latest 63 sessions for eligible names—compresses to 6.65 MB; planning rounds this to 7 MB.

| Horizon | Full monthly snapshots | Weekly lightweight updates | Conservative storage upper bound |
|---|---:|---:|---:|
| One complete snapshot | 1 | 0 | 0.152 GB |
| One year | 12 | 52 | 2.18 GB |
| 36 months | 36 | 156 | 6.55 GB |
| 60 months | 60 | 260 | 10.91 GB |

These bounds assume no cross-snapshot deduplication benefit, making them conservative. Exact content reuse should reduce realized storage, but changing price-history files limit whole-file deduplication. A future incremental refinement can shard prices by ticker/month without changing logical reconstruction.

## Evidence ceiling

Storage and approximate lags make exploration possible; they do not cure survivorship, missing delisting returns, absent filing timestamps, or restatement-vintage bias. Complete strategy evidence must come from snapshots archived prospectively at retrieval time.
