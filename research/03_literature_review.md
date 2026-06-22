# Literature-review search plan

**Version:** 0.1 search protocol  
**As of:** 2026-06-21  
**Coverage date:** Database inception through 2026-06-21  
**Status:** Search plan plus preliminary anchor screen, not a completed evidence review

## 1. Review question

Which transparent market and fundamental signals, portfolio rules, and execution practices have replicated evidence, an economically plausible mechanism, point-in-time testability, and realistic relevance to a long-only recurring-contribution US equity portfolio?

The review will not treat publication count as proof, and it will not promote a rule merely because a historical paper reports significance.

## 2. Source hierarchy

Search and cite in this order:

1. peer-reviewed research and independent replications;
2. recognized academic working papers from NBER, university repositories, or established scholarly networks;
3. official regulator, exchange, index-provider, broker, and data-vendor documentation;
4. transparent institutional research with formulas and study design;
5. well-documented practitioner research; and
6. commercial or informal articles only as leads to stronger sources.

Books are used for synthesis and method, not as a substitute for inspectable empirical evidence. Current broker, fund, index, and vendor facts require dated official documentation.

## 3. Search venues

- Crossref and DOI metadata for canonical publication identity;
- Google Scholar and Semantic Scholar for forward/backward citation trails;
- EconLit, JSTOR, Web of Science, or Scopus when access is available;
- NBER, SSRN, RePEc/IDEAS, and university repositories for working papers;
- journal sites and author repositories for the final paper and appendices;
- CRSP/WRDS, SEC, exchanges, index providers, and vendor documentation for data definitions;
- IBKR and fund sponsors for current operational facts; and
- citation searches for independent replication, international extension, post-publication decay, critiques, and corrections.

A search log records query, venue, run date, filters, results screened, inclusions, exclusions, and reviewer.

## 4. Topic map and query templates

Each query is combined with terms such as `stock returns`, `cross-section`, `US equities`, `out of sample`, `replication`, `transaction costs`, `publication bias`, `point in time`, and `delisting` as appropriate.

| Topic | Core query concepts | Evidence sought | Implementation question |
|---|---|---|---|
| Value | `book-to-market`, `earnings yield`, `free cash flow yield`, `enterprise value`, `value premium` | Original result, post-publication behavior, sector dependence, distress/quality interaction | Which valuation denominators remain comparable and available point in time? |
| Quality/profitability | `gross profitability`, `operating profitability`, `ROIC`, `ROE`, `cash-flow profitability`, `quality minus junk` | Independent replication, overlap among measures, valuation interaction | Is one robust measure preferable to a redundant score? |
| Momentum | `12-1 momentum`, `6-1 momentum`, `residual momentum`, `trend`, `momentum crashes` | Replication, regime/crash behavior, turnover and cost sensitivity | What lookback/skip/buffer neighborhood is stable? |
| Investment/asset growth | `asset growth anomaly`, `investment factor`, `capital expenditure`, `net operating assets` | Risk versus mispricing accounts, sector treatment, data lag | Can investment intensity be measured consistently across sectors? |
| Financial strength | `Piotroski F-score`, `accruals`, `bankruptcy risk`, `leverage`, `interest coverage` | Incremental effect beyond value/quality, distress exclusions | Is a gate more robust than a continuous score? |
| Shareholder yield | `net payout yield`, `shareholder yield`, `repurchases`, `issuance`, `dividends` | Replication with issuance data and corporate actions | Can buybacks/issuance be measured point in time without restatement leakage? |
| Low volatility/risk | `low volatility anomaly`, `betting against beta`, `downside risk`, `idiosyncratic volatility` | Leverage constraints, sector concentration, valuation/crowding | Risk control or expected-return signal? |
| Earnings revisions | `analyst revisions`, `earnings surprise`, `post-earnings announcement drift` | Timestamp quality, licensing, transaction cost | Is affordable point-in-time coverage sufficient? |
| Multifactor | `factor combination`, `multifactor`, `composite score`, `factor timing`, `diversification` | Out-of-sample combination evidence, redundancy, crowding | Equal ranks, gates, or evidence weights? |
| Portfolio size | `portfolio concentration`, `number of stocks`, `idiosyncratic diversification`, `active share` | Tail dependence, top-contributor effects, turnover | Which sizes are operationally viable at USD 250 weekly? |
| Rebalancing/turnover | `rebalancing frequency`, `turnover buffer`, `no-trade region`, `transaction costs` | Net-of-cost results, rank buffers, holding periods | Weekly contributions with less frequent full rebalance? |
| Recurring contributions | `dollar cost averaging`, `periodic investment`, `cash flow`, `lump sum` | Wealth and risk framing rather than spurious alpha | How should cash be routed without avoidable sells? |
| Tax-aware maintenance | `tax-aware rebalancing`, `tax lot`, `capital gains`, `loss harvesting` | General methods plus official jurisdiction rules later | Which conclusions are tax-dependent? |
| Execution | `closing auction`, `opening volatility`, `implementation shortfall`, `limit order`, `spread`, `slippage` | Attainable fill models and timing stability | Does timing matter after costs and multiple testing? |

Example canonical query:

```text
("gross profitability" OR "operating profitability")
AND ("stock returns" OR "cross-section")
AND (replication OR "out of sample" OR "transaction costs")
```

Each topic also receives a negative-result search using `fails`, `disappears`, `attenuation`, `publication bias`, `data snooping`, `international evidence`, and `post-publication`.

## 5. Inclusion and exclusion rules

### Include

- A precise signal or portfolio rule that can be reconstructed.
- An identifiable sample, universe, period, return definition, and rebalance convention.
- Sufficient method detail to assess timing, delistings, costs, and benchmark choice.
- US evidence or a clearly relevant cross-market replication.
- Critiques and failures that challenge a candidate rule.

### Exclude from evidentiary support

- Current-constituent or survivorship-biased tests presented as historical universes.
- Fundamentals used before filing/publication or latest-restated histories treated as original knowledge.
- Results without formulas, sample definitions, or an attainable implementation path.
- Marketing claims whose methodology cannot be audited.
- Pure in-sample machine-learning comparisons without chronological validation.
- Timing claims selected from many weekdays/minutes without multiplicity control.

Excluded material may be retained as a search lead with an explicit reason.

## 6. Extraction schema

For every included item record:

- source ID, citation, DOI/URL, publication date, and version;
- authors and institutional/commercial conflicts;
- study period, market, security universe, and sample filters;
- signal formula, direction, lags, rebalance, weights, and holding period;
- data provider, constituent treatment, delisting treatment, and point-in-time controls;
- gross and net effect size, uncertainty, benchmark, costs, and turnover;
- in-sample versus out-of-sample status;
- replication type and whether the replicator is independent;
- limitations, contradictions, and likely failure modes;
- required fields and operational complexity for this project; and
- resulting hypothesis, ablation, or rejection decision.

## 7. Replication and confidence grading

| Grade | Definition | Research use |
|---|---|---|
| A — replicated and implementable | Multiple independent studies or a strong cross-market/time replication; transparent definition; plausible after-cost implementation; no unresolved fatal bias | Eligible for a simple primary hypothesis |
| B — supported with caveats | Canonical evidence plus partial replication, but material regime, sector, data, or cost sensitivity | Eligible with conservative definition and explicit falsification |
| C — preliminary or difficult | Isolated result, weak independence, expensive point-in-time data, or unclear net implementation | Prototype/diagnostic only |
| D — contradicted or non-auditable | Major replication failure, leakage/survivorship concern, opaque method, or implausible execution | Exclude from candidate set; retain contradiction |

Grades describe the evidence base, not expected future return. A famous source does not automatically receive Grade A.

## 8. Synthesis method

Evidence is synthesized by claim, not by author. For each proposed rule, `research/04_evidence_matrix.md` will connect mechanism, replicated evidence, contradictions, data requirements, implementation cost, and our preregistered test result. Correlated variants are grouped so five similar profitability ratios do not appear to be five independent confirmations.

Priority is given to effect persistence after publication, comparable universes, realistic costs, conservative lags, and results not concentrated in microcaps or one era. Disagreements remain visible in `research/contradictions.md`.

## 9. Initial anchor set

The first backward/forward citation searches begin from canonical work on value and common factors, momentum, profitability, financial strength, asset growth/investment, accruals, factor replication, post-publication decay, and backtest selection bias. The bibliography in `research/references.md` is the current seed set; inclusion there does not mean its claim has passed review.

## 10. Completion rule

The literature checkpoint is complete only when every candidate family has at least one primary source, one independent replication or explicit absence-of-replication finding, one contradiction/limitation search, an evidence grade, a point-in-time data mapping, and a resulting test or rejection decision. Search dates and versions must be current enough for operational/vendor facts.

Stop expanding an individual factor when the review has a foundational study, a broad independent replication or meta-study, at least one implementation/cost study, and a documented contradiction search. Citation chaining continues when these disagree.

## 11. Preliminary anchor set

These are starting points, not accepted claims:

| Topic | Anchor sources |
|---|---|
| Replication and multiplicity | Hou, Xue & Zhang, *Replicating Anomalies* (2018/2020), https://doi.org/10.1093/rfs/hhy131; Harvey, Liu & Zhu (2016), https://doi.org/10.1093/rfs/hhv059; McLean & Pontiff (2016), https://doi.org/10.1111/jofi.12365; Chen & Zimmermann (2022), https://doi.org/10.1561/104.00000112; Jensen, Kelly & Pedersen (2023), https://doi.org/10.1111/jofi.13249 |
| Value | Fama & French (1992), https://doi.org/10.1111/j.1540-6261.1992.tb04398.x |
| Profitability and quality | Novy-Marx (2013), https://doi.org/10.1016/j.jfineco.2013.01.003; Asness, Frazzini & Pedersen, https://doi.org/10.1007/s11142-018-9470-2; Fama & French (2015), https://doi.org/10.1016/j.jfineco.2014.10.010 |
| Financial strength and distress | Piotroski (2000), https://doi.org/10.2307/2672906; Campbell, Hilscher & Szilagyi (2008), https://doi.org/10.1111/j.1540-6261.2008.01416.x |
| Momentum | Jegadeesh & Titman (1993), https://doi.org/10.1111/j.1540-6261.1993.tb04702.x; Daniel–Moskowitz crash-risk work to retrieve |
| Earnings revisions/PEAD | Bernard & Thomas (1989), https://doi.org/10.2307/2491062; Jegadeesh et al. (2004), https://doi.org/10.1111/j.1540-6261.2004.00657.x |
| Investment/asset growth | Cooper, Gulen & Schill (2008), https://doi.org/10.1111/j.1540-6261.2008.01370.x |
| Net payout/shareholder yield | Boudoukh et al. (2007), https://doi.org/10.1111/j.1540-6261.2007.01226.x |
| Low/idiosyncratic volatility | Ang et al. (2006), https://doi.org/10.1111/j.1540-6261.2006.00836.x |
| Trading costs and turnover | Novy-Marx & Velikov (2016), https://doi.org/10.1093/rfs/hhv063 |
| Concentration and stock-return skew | Evans & Archer (1968), https://doi.org/10.1111/j.1540-6261.1968.tb00315.x; Bessembinder (2018), https://doi.org/10.1016/j.jfineco.2018.06.004 |
| Contributions | Vanguard cost-averaging study, https://corporate.vanguard.com/content/dam/corp/research/pdf/cost_averaging_invest_now_or_temporarily_hold_your_cash.pdf |
| Tax-aware methods | Poterba, https://doi.org/10.3386/w8223; Boyd et al., https://web.stanford.edu/~boyd/papers/pdf/tax_aware_portfolio.pdf |
| Execution and current operations | SEC trading basics, https://www.sec.gov/files/trading101basics.pdf; official IBKR commissions, fractional shares, and order-type pages to reverify when costs freeze |

## 12. Preliminary evidence-screen findings

These findings guide retrieval and preregistration; they are not empirical results for this strategy.

- Replication studies materially disagree. Hou–Xue–Zhang eliminate many published anomalies after stricter breakpoints and significance standards, while Chen–Zimmermann and Jensen–Kelly–Pedersen report broader reproducibility. The reconciliation to test is that reproduction is not the same as standalone, liquid, long-only, after-cost alpha.
- McLean–Pontiff report material out-of-sample and post-publication attenuation. Original published effect sizes should therefore be treated as optimistic inputs, not expected strategy returns.
- Value, profitability/quality, momentum, conservative investment, and financial-strength/distress measures have the strongest initial evidence breadth, but definitions overlap and must be ablated.
- Earnings revisions require genuinely timestamped estimate history and may be excluded if the data are unaffordable or not point in time.
- Net payout requires dividends, repurchases, and issuance; incomplete repurchase/issuance history can turn it into a different signal.
- Momentum carries crash and turnover risk; low volatility can conceal sector, duration, valuation, and quality exposures.
- Piotroski’s original setting is high book-to-market stocks. A universal F-score claim would be an extension requiring its own test.
- Concentration increases exposure to the skewed distribution of individual-stock outcomes; portfolio size cannot be selected on mean return alone.
- Classic dollar-cost-averaging comparisons usually ask whether an already available lump sum should wait in cash. That is not the same question as exogenous weekly income and must not be cited as if it were.
- Execution weekday/minute remains secondary. Market orders do not guarantee price and limit orders do not guarantee fills; exact operational facts and costs are frozen from current official sources later.
