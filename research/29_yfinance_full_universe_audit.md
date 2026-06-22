# Phase 1B full current-universe audit

**Checkpoint:** Phase 1B Checkpoint 2  
**Snapshot:** `data/raw/yfinance_phase1b_checkpoint2/2026-06-22T_currentZ`  
**Retrieval:** 2026-06-22 06:43:51–07:07:35 UTC, yfinance 1.4.0 only  
**Classification:** current universe, not a historical universe

## Result

The deterministic sector × market-cap partition worked. It issued 110 nonoverlapping queries, archived every query and raw response, and returned 2,207 unique current screened tickers. The largest leaf contained 106 names, below Yahoo's 250-result cap; therefore no leaf was silently truncated. The current snapshot manifest SHA-256 is `d94f0498e79eddf8b3c96b2b0c56d9dec82fdb9460a4e5b3f30ac6ee5c2c3373`.

All 698 final ticker bundles completed with zero endpoint errors after targeted rate-limit retries. SPY and QQQ were ultimately retrieved in the checkpoint run and have individual checksums in the manifest.

## Eligibility waterfall

| Stage | Remaining |
|---|---:|
| Unique screener result, including the USD 1B–2B query band | 2,207 |
| Enriched candidates with screener market cap at least USD 2B | 1,876 |
| Main exchange | 1,218 |
| Equity quote type | 1,218 |
| Country = United States | 984 |
| Trading and financial currency = USD | 976 |
| Current market cap at least USD 2B | 976 |
| Latest raw close at least USD 5 | 974 |
| At least 504 daily observations | 926 |
| 63-session median dollar volume at least USD 5M | 924 |
| Sector present | 924 |
| Financial Services excluded | 774 |
| Real Estate excluded | 709 |
| Nonordinary-security exclusions | 702 |
| Issuer/share-class deduplication | **698** |
| Five-field base fundamental coverage | **698** |

The final universe has 200 names between USD 2B–5B, 151 between USD 5B–10B, and 347 above USD 10B. Sector counts are Industrials 153, Technology 138, Consumer Cyclical 110, Healthcare 107, Consumer Defensive 44, Energy 44, Basic Materials 42, Utilities 37, and Communication Services 23. It spans 109 current Yahoo industries.

## Controls and artifacts

- `query_registry.csv` records boundaries, timestamps, returned counts, and query specifications.
- `universe_queries/` preserves 110 query/response pairs.
- `screen_duplicate_rows.csv`, `issuer_deduplication_decisions.csv`, and `eligibility_and_exclusions.csv` preserve duplicate and exclusion decisions.
- `base_eligible_universe.csv` is the final merged current universe.
- Every ticker manifest records endpoint sizes and SHA-256 checksums.
- The content-addressed archive manifest is `data/archive/yfinance_phase1b_cas/manifests/2026-06-22T_currentZ.json`.

## Limitations

This is a broad reproducible current screen, not a security master. It omits inactive and delisted companies, lacks permanent issuer identifiers, uses mutable Yahoo classifications, and cannot reconstruct prior membership. The normalized-name share-class rule is current-only and imperfect. None of these 698 names may be projected backward and called a historical universe.

