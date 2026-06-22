# Phase 1B yfinance strategy preregistration candidate

**Generation:** `RP-001-YFINANCE-1B-V1`  
**Status:** First-checkpoint proposal; no performance optimization or paper activation  
**Data source:** yfinance only  
**Evidence ceiling:** Tier 1 survivor-biased price diagnostics, Tier 2 non-PIT fundamental exploration, Tier 3 prospective paper validation

## Objective

Test whether a transparent yfinance-only price-plus-fundamental ranking process is technically maintainable and operationally coherent for a USD 250 recurring contribution. Historical fundamental performance cannot approve live deployment.

## Current-universe construction

On each archived universe date, query Yahoo through `yf.screen(EquityQuery)` separately for all eleven Yahoo equity sectors because one screen is capped at 250 results. Use:

- region `us`;
- exchanges `NMS`, `NYQ`, or `ASE`;
- screener price at least USD 5;
- screener market capitalization at least USD 1 billion;
- three-month average daily volume at least 200,000 shares; and
- descending market-cap ordering, retaining up to the Yahoo per-query limit.

The screen is a practical current candidate list, not a complete US listing database. Archive every raw sector response and the merged result.

### Primary eligibility after enrichment

- `quoteType == EQUITY` and exchange remains NMS/NYQ/ASE.
- `country == United States`; foreign issuers/ADRs are excluded from the primary portfolio.
- Trading currency USD and, for fundamental composites, `financialCurrency == USD`.
- Current market capitalization at least USD 2 billion.
- Raw share price at least USD 5.
- At least 504 trading sessions since the first available price, excluding recent IPOs.
- At least 252 total-return observations for signals.
- Median raw Close × Volume over 63 sessions at least USD 5 million, with at least 55 observations.
- Current Yahoo sector and industry present.
- Exclude Financial Services and Real Estate in the initial fundamental strategy; this covers banks, insurers and most REITs whose accounting is not comparable.
- Exclude names whose current metadata/name indicates a limited partnership, fund, trust, warrant, unit or other nonordinary security. Because Yahoo lacks a fully reliable permanent security master, ambiguous names are ineligible and logged.
- For each candidate composite, every required category score must exist under the frozen missing-data rule.

Deduplicate apparent issuer share classes by normalized current issuer name, retaining the class with greater current market capitalization and liquidity. This is an imperfect current-only rule and cannot resolve all historical ticker/issuer identities.

### Fair comparator support

Report two price-only arms:

1. `YF-P-BROAD` on all price-eligible names; and
2. `YF-P` on the same common-support universe used by the complete Q/V/G/P composite.

Only `YF-P` is the direct comparator for whether current fundamentals change selection. This prevents missing fundamental coverage from silently changing the comparison universe.

## Factor transformation

- Use the exact proposed formulas in `research/23_yfinance_factor_dictionary.md`.
- Admit factors by coverage/semantic rules before any performance review.
- Score accounting/value/growth factors within current Yahoo sector; use the full cross-section only when fewer than 20 valid sector observations exist and flag it.
- Winsorize raw values at sector 2.5%/97.5% bounds before ranking.
- Price factors use sector-relative treatment only where specified; the primary momentum/trend/volatility ranks are market-wide.
- Category score = equal mean of admitted, nonredundant factor percentile ranks.
- Require at least half of admitted category factors and no fewer than two; otherwise the category is missing.
- Composite score = equal mean of category scores. No fitted coefficients or machine learning.
- Tie-break: higher composite, then higher 63-day median dollar volume, then ticker ascending.

## Small preregistered candidate family

| Candidate | Categories | Primary purpose |
|---|---|---|
| `YF-P` | Price | Common-support price comparator |
| `YF-QP` | Quality + Price | Test whether current quality changes price selection |
| `YF-QVP` | Quality + Value + Price | Add valuation discipline |
| `YF-QVGP` | Quality + Value + Growth + Price | Complete initial yfinance composite |

Every category has equal weight. Current analyst revisions/estimates are archived but excluded from this generation; adding them requires a new prospective preregistration. `YF-P-BROAD` is a universe diagnostic, not a fifth model selected on returns.

The primary portfolio size is 30. N=20 and N=40 are preregistered concentration/operational sensitivities, not return-selected replacements. No Cartesian factor-weight search is authorized.

## Portfolio policy

- Long-only, no leverage, margin, shorts or options.
- Equal target weights.
- Monthly rank calculation after the final completed month-end session.
- Enter highest-ranked nonheld names as vacancies exist.
- Retain a held name while its eligible candidate rank is at most `2N`; normal exit occurs when rank exceeds `2N` or a required category becomes persistently missing.
- Quarterly corrective rebalance after March, June, September and December reviews.
- Target sector cap 25%; drift-review cap 30%.
- Target industry cap 15%; drift-review cap 20%.
- Drift name cap 7.5%. Initial equal-weight N=20 position is 5%; N=30 is 3.33%; N=40 is 2.5%.
- Minimum hypothetical order USD 25.
- Gross trailing-12-month discretionary turnover budget 100%.
- Hold cash rather than violate eligibility, concentration or minimum-order rules.

### Contributions

- Primary: USD 250 on the first trading session on or after each Friday.
- Sensitivity: USD 500 every second Friday, preserving total cash availability.
- Direct each contribution to at most three approved holdings with the largest dollar deficits to target.
- Do not sell merely to invest a contribution.
- Fractional units are primary; whole-share rounding and residual cash are mandatory sensitivities.

## Entry and exit

### Entry

A name must pass every current eligibility rule, have all categories required by its candidate, remain within concentration limits, and rank high enough to fill an available target slot. No current estimate/recommendation threshold is used.

### Normal exit

At the monthly review, exit when:

- rank is worse than `2N`;
- the name fails hard security/price/liquidity eligibility on two consecutive reviews;
- a required category is missing on two consecutive reviews; or
- a concentration breach cannot be resolved with contributions and scheduled trimming.

### Unscheduled review

Review only for a retrievable split, acquisition/merger indication, suspension/stale price, apparent delisting, bankruptcy disclosure visible in current metadata/history, or irreconcilable data/action error. Yfinance may not supply complete terminal-event information; ambiguous events suspend paper trading and retain a documented conservative value pending resolution.

There is no stop-loss in the primary rule. Trailing/volatility stops are not added at this checkpoint and may not be selected from exploratory results.

## Historical evidence protocol

### Tier 1 price

Longer yfinance price tests may examine factor mechanics, sizes, buffers, contributions and costs. Every result must state that the current screen/universe is projected backward and excludes unavailable historical failures/delistings.

### Tier 2 fundamentals

If later authorized, use only statement periods currently returned, lag quarterly values 90 calendar days and annual values 120 calendar days, and never use current info/valuation/estimate/revision fields historically. Label every result:

> Exploratory non-point-in-time fundamental analysis using currently retrievable and potentially restated Yahoo Finance data.

No Tier 2 result can approve live deployment or certify durable SPY/QQQ outperformance.

### Tier 3 prospective

The primary valid test is `YF-FWD-001` under `research/27_yfinance_forward_protocol.md`. It is inactive until explicit checkpoint review and registry freeze.

## Benchmarks and evaluation

Maintain contribution-matched SPY and QQQ as separate required comparisons. At this stage evaluate coverage, score/rank persistence, turnover, factor correlation, concentration, implementability and selection differences before emphasizing returns. Recent exploratory and prospective performance must always be shown with its evidence tier.

## First-checkpoint stop

This specification authorizes no strategy optimization, exploratory fundamental backtest, target portfolio, paper order, or live action. The next checkpoint decides which factors pass data admission and whether to implement the calculation/scoring layer.
