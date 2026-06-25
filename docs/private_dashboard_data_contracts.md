# Private Investment Dashboard — Data Contracts

## Model integrity manifest

```json
{
  "schema": "MODEL-INTEGRITY-MANIFEST-1.0.0",
  "snapshot_id": "2026-06-24T080500Z",
  "retrieval_timestamp": "2026-06-24T08:05:00Z",
  "last_completed_price_session": "2026-06-23",
  "fundamental_data_cutoff": "2026-06-24",
  "universe_screened": 2205,
  "eligible_count": 1070,
  "valid_b2_count": 1070,
  "valid_quality_count": 1070,
  "missing_quality_count": 0,
  "integrity_classification": "current_decision_support_integrity_passed",
  "configuration_hash": "abc123...",
  "universe_hash": "def456...",
  "warnings": [],
  "model_version": "M1-B2-QV-1.0.0"
}
```

## Model snapshot

```json
{
  "schema": "MODEL-SNAPSHOT-1.0.0",
  "model_id": "M1_B2_QUALITY_VETO_N30",
  "model_version": "M1-B2-QV-1.0.0",
  "snapshot_id": "2026-06-24T080500Z",
  "effective_date": "2026-06-23",
  "decision_timestamp": "2026-06-24T08:00:00Z",
  "execution_convention": "next_valid_session_close",
  "holdings": [
    {
      "ticker": "MU",
      "company_name": "Micron Technology, Inc.",
      "target_weight": 0.03333,
      "rank": 1,
      "b2_score": 0.9878,
      "quality_percentile": 0.6988,
      "quality_components_ok": 4,
      "sector": "Technology",
      "industry": "Semiconductors",
      "flags": []
    }
  ],
  "vetoed_stocks": ["AAPL", "MSFT", ...],
  "veto_count": 107,
  "missing_quality_count": 0
}
```

## Rebalance comparison

```json
{
  "schema": "REBALANCE-COMPARISON-1.0.0",
  "portfolio_id": "uuid...",
  "model_snapshot_id": "uuid...",
  "as_of_date": "2026-06-24",
  "lines": [
    {
      "ticker": "MU",
      "current_quantity": 10,
      "target_quantity": 12.5,
      "current_weight": 0.031,
      "target_weight": 0.03333,
      "illustrative_buy_qty": 2.5,
      "illustrative_sell_qty": 0,
      "estimated_cost_bps": 10,
      "estimated_cost_usd": 1.25
    }
  ],
  "estimated_total_cost_usd": 45.00,
  "estimated_cash_required": 5000.00,
  "residual_cash": 1250.00
}
```

## Validation rules

- All JSON imports must match a known schema version
- Missing required fields → reject
- Unknown fields → reject (strict mode)
- Holdings must sum to 1.0 ± floating-point tolerance
- snapshot_id must be unique
- Timestamps must be ISO 8601 UTC
- B2 scores must be 0-1
- Target weights must be 0-1
