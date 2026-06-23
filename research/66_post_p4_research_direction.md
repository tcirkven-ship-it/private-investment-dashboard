# Post-P4 research direction decision

## Current state

| Artifact | Status |
|---|---|
| Daily YF-QVP scanner | Functional; 2,205 screened, 1,069 eligible, 1,033 scored; run `2026-06-22T172514Z` |
| Price component P4 (12-1 mom, 6-1 mom, 200-d trend, inverse 252-d vol) | **FAIL** — standalone evidence rejected under repeated walk-forward |
| P4 mechanics audit | Published reproduction PASS; practical correction reduces turnover 682% → 643%; P4 still trails QQQ by 2.27pp annually |
| Q and V incremental return | Untested; current QVP/Price top-30 overlap is one name (ENS) |
| Credible long QVP backtest | Does not exist; yfinance lacks point-in-time mkt-cap, EV, valuations, inactive/delisted names |
| Prospective evidence ledger | Active, decoupled, zero paper decisions registered |

## Decision options

### Option 1 — Retire P4 and design a new Price generation

| Attribute | Assessment |
|---|---|
| Question answered | Can a different Price formula (e.g., simple 12-1 momentum, no inverse vol) show standalone benchmark value? |
| Required data | Existing yfinance histories; no new retrieval needed |
| Implementation complexity | Low — existing grid infrastructure can be reused with a new factor set |
| Principal statistical risks | Survivor-bias ceiling unchanged; P1–P3 already tested with 38–41% vol and 493–725% turnover |
| Survivorship / PIT limits | Same current-survivor universe projected backward; no inactive/delisted names |
| Credible SPY/QQQ test? | No — survivor-bias prevents pass/conditional-pass claims |
| Supports Phase Two? | No — a recycled Price generation still lacks fundamental validation |
| PASS threshold | New candidate passes development gates, turnover <200%, beats both benchmarks in evaluation |
| FAIL threshold | Development gate failure, benchmark underperformance, or turnover >200% |

**Verdict: Not recommended.** P1–P3 already exist in the grid and showed extreme volatility and turnover. A narrower Price-only search would re-test signals already examined, without resolving the survivorship ceiling. This would consume research time without enabling a credible pass.

---

### Option 2 — Simpler momentum signal with Q/V as exclusion filters only

| Attribute | Assessment |
|---|---|
| Question answered | Can a momentum-only model (no inverse vol, no composite Price) combined with Q/V exclusion screens outperform benchmarks? |
| Required data | Existing yfinance price histories plus current Q/V fields |
| Implementation complexity | Medium — new portfolio logic (exclusion step before ranking); no new data retrieval |
| Principal statistical risks | Exclusion thresholds must be frozen pre-test; thin Q/V data creates randomness; historical Q/V values unavailable |
| Survivorship / PIT limits | Q/V fields are current retrieval-time only; cannot be projected backward as PIT fundamentals |
| Credible SPY/QQQ test? | No — same survivor-bias ceiling; Q/V historical vintages unavailable |
| Supports Phase Two? | No — exclusion logic would be a new strategy generation requiring its own validation |
| PASS threshold | Significantly reduced turnover, benchmark outperformance, threshold stability |
| FAIL threshold | Underperformance, unstable exclusions, or turnover >200% |

**Verdict: Not recommended for a definitive test.** The Q/V data limitation is the same as Option 1 — current fields cannot support a historical backtest. An exclusion filter could be explored prospectively but adds complexity without resolving the core data ceiling.

---

### Option 3 — Obtain PIT universe, delisting, fundamentals, market-cap and EV data; test QVP properly

| Attribute | Assessment |
|---|---|
| Question answered | Does a properly constructed QVP strategy outperform contribution-matched SPY and QQQ after costs in a point-in-time, survivor-aware historical test? |
| Required data | Paid vendor: historical constituent lists, inactive/delisted securities, permanent identifiers, PIT market-cap/EV, PIT fundamentals, corporate actions |
| Implementation complexity | High — vendor evaluation, data ingestion, schema alignment, PIT reconstruction, new backtest engine or major extension |
| Principal statistical risks | Vendor coverage gaps, restatement handling, costs and fees must be modeled correctly |
| Survivorship / PIT limits | Can be fully resolved with the right vendor (e.g., Sharadar + Norgate combination or CRSP/Compustat) |
| Credible SPY/QQQ test? | Yes, if the data meets the frozen hard gates |
| Supports Phase Two? | A validated strategy would be the prerequisite for any Phase Two development |
| PASS threshold | Preregistered frozen QVP passes all development gates, evaluation outperforms both benchmarks, turnover <200%, uncertainty interval excludes zero |
| FAIL threshold | Underperformance, turnover failure, or vendor data fails integrity gates |

**Verdict: The only path that can produce a definitive PASS or FAIL for the QVP hypothesis.** However, it requires a paid data budget, vendor selection, significant engineering, and a preregistered protocol. This is a months-long research generation, not a quick answer.

---

### Option 4 — Preserve current QVP model, rely only on prospective evidence

| Attribute | Assessment |
|---|---|
| Question answered | Does the current frozen QVP model accumulate credible forward evidence over a long observation period? |
| Required data | Existing daily scanner output; prospective yfinance snapshots over 3–5+ years |
| Implementation complexity | Low — the scanner already exists; the evidence ledger is decoupled and waiting |
| Principal statistical risks | Time cost; user may exit before meaningful evidence exists; regime-dependent results |
| Survivorship / PIT limits | Forward evidence is genuinely PIT by construction; no survivorship bias in future data |
| Credible SPY/QQQ test? | Yes, after a sufficient observation period (minimum 36 months per DEC-044), but no earlier |
| Supports Phase Two? | Not immediately; prospective evidence must accumulate before Phase Two can be justified |
| PASS threshold | After 36+ months: outperforms benchmarks with acceptable turnover and drawdown |
| FAIL threshold | Benchmark underperformance, high turnover, or early abandonment |

**Verdict: Defensible and low-cost, but slow.** The prospective ledger is already active and decoupled from the scanner. The user must wait years for a meaningful signal. This does not conflict with other options — it can run in parallel with any of them.

---

### Option 5 — Stop active-strategy development; retain passive SPY/QQQ baseline

| Attribute | Assessment |
|---|---|
| Question answered | Is the null hypothesis (passive ETF investing) the correct practical conclusion for this investor? |
| Required data | None beyond existing benchmark histories |
| Implementation complexity | None — no new code, data, or experiments |
| Principal statistical risks | Inflation, sequence-of-returns risk, opportunity cost if an active strategy could have added value |
| Survivorship / PIT limits | Not applicable — benchmarks are investable and PIT by construction |
| Credible SPY/QQQ test? | The decision is not a test; it is a practical conclusion from the FAIL determination |
| Supports Phase Two? | No — Phase Two would be explicitly abandoned |
| PASS threshold | N/A |
| FAIL threshold | N/A |

**Verdict: Justified by the evidence but premature for a final conclusion.** The QVP hypothesis has not been definitively tested (no credible historical test exists). Stopping now would abandon the original price-plus-fundamental mandate without resolving it. A retirement decision should be deferred until Option 3 or Option 4 produces a definitive answer.

---

## Recommendations

### Primary path: Option 4 (prospective evidence) in parallel with small-scope Option 3 preparation

The daily scanner is technically functional and produces usable current rankings at zero marginal cost. The prospective evidence ledger is active and decoupled — it can accumulate regardless of other work. Running the scanner on successive completed sessions adds evidence without requiring new research decisions.

In parallel, begin the low-cost preparation for Option 3: document the exact data requirements, evaluate the Sharadar + Norgate vendor combination already identified in the vendor matrix (`research/20_data_requirements_and_vendor_matrix.md`), and estimate the budget. This preparation does not require purchasing data until the user explicitly authorizes expenditure.

### Lower-cost fallback: Option 4 alone

If the user does not wish to pursue a paid-data generation, continue the prospective ledger as the sole forward evidence mechanism. Accept that:
* the current QVP list provides current cross-sectional rankings but no return validation;
* a credible PASS or FAIL for QVP will require 3–5 years of observation;
* the scanner is a decision-support tool, not a validated strategy.

## Hard constraints

* The scanner output is current decision-support research, not a return claim.
* Q and V have not been shown to improve returns — the current QVP top 30 overlaps the Price-only top 30 in exactly one name.
* P4 is historically rejected under the available survivor-biased evidence.
* The complete QVP strategy cannot receive a credible long historical backtest from yfinance alone.
* Further user-interface development (launcher, dashboard, alerting) is independent of strategy validation and should not be confused with evidence that the strategy works.
* No broker integration or order placement is authorized.
* No individual-stock recommendation is made.
