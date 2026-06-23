# Previous Price-test reconciliation

This is not the first Price-only test. EXP-0009/0010 previously evaluated
`C03-M` and nine registered variants.

## Previous frozen model

| Item | C03-M |
|---|---|
| Signal | raw 12–1 momentum: adjusted price at `t-21` divided by `t-252`, minus one |
| Universe | current 2026-06-18 OEF holdings projected backward; 100 issuer-deduplicated large-cap stocks |
| Portfolio | N=30, equal target, monthly selection, retain through rank 60 |
| Constraints | 25% sector target cap, 7.5% name-drift cap, quarterly weight correction |
| Funding | USD 250 weekly; contribution cash routed to at most three underweights |
| Execution/cost | next-session modeled trade, expected and stressed commission/impact layers |
| Development | 2010–2019 |
| Single walk-forward label | 2020–2022 |
| Final evaluation | 2023–2026-06-18 |

The earlier implementation sorted raw momentum rather than averaging four
cross-sectional factor percentiles. It therefore differs materially from the
current frozen Price category, which adds 6–1 momentum, 200-day trend and
inverse 252-day volatility and winsorizes each date's factor cross-section.

## Verified prior findings

- Through 2022, C03-M returned 17.09% annualized TWR, +5.34 points versus SPY
  and +1.72 points versus QQQ, but gross annual turnover was 184% and the QQQ
  block-bootstrap interval included zero.
- In 2023–2026-06-18 it returned 34.50% annualized, +11.47 points versus SPY
  but **−0.83 point versus QQQ**; stressed QQQ-relative TWR was also negative.
- Final-period turnover was **172%**. Only 2 of 10 registered variants were
  positive against both benchmarks in both stages, and those variants required
  about 258% and 875% final-period turnover.
- The model failed QQQ, turnover, uncertainty, stability and definitive-data
  gates. Its universe used current survivors, omitted inactive securities and
  reliable delisting outcomes, and had only one outer chronological stage.

Those failures remain in force. The new repeated-fold study neither renames nor
retroactively repairs C03-M.
