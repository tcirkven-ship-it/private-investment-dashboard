# Private Investment Dashboard — Database Schema

All tables include `created_at TIMESTAMPTZ DEFAULT now()` and `updated_at TIMESTAMPTZ DEFAULT now()` unless noted.

## profiles
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, references auth.users |
| email | TEXT | NOT NULL |
| display_name | TEXT | |
| totp_enabled | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMPTZ | |

## app_settings
| Column | Type | Constraints |
|---|---|---|
| key | TEXT | PK |
| value | JSONB | NOT NULL |
| owner_id | UUID | FK, RLS |

## securities
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| ticker | TEXT | NOT NULL, UNIQUE |
| company_name | TEXT | |
| sector | TEXT | |
| industry | TEXT | |
| asset_class | TEXT | |
| is_active | BOOLEAN | DEFAULT true |
| data_source | TEXT | |

## model_versions
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| model_id | TEXT | NOT NULL |
| version | TEXT | NOT NULL |
| description | TEXT | |
| config_hash | TEXT | |
| formula_version | TEXT | |
| UNIQUE(model_id, version) | | |

## model_snapshots
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| model_version_id | UUID | FK |
| snapshot_id | TEXT | NOT NULL |
| status | TEXT | CHECK (DRAFT/VALIDATED/APPROVED/PUBLISHED/SUPERSEDED) |
| effective_date | DATE | NOT NULL |
| decision_timestamp | TIMESTAMPTZ | |
| execution_convention | TEXT | |
| universe_screened | INT | |
| eligible_count | INT | |
| valid_score_count | INT | |
| integrity_hash | TEXT | |
| import_notes | TEXT | |
| UNIQUE(snapshot_id) | | |

## model_snapshot_holdings
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| snapshot_id | UUID | FK, NOT NULL |
| security_id | UUID | FK |
| target_weight | NUMERIC(8,6) | |
| rank | INT | |
| b2_score | NUMERIC(8,6) | |
| quality_percentile | NUMERIC(8,6) | |
| quality_components_ok | INT | |
| sector | TEXT | |
| industry | TEXT | |
| UNIQUE(snapshot_id, security_id) | | |

## portfolios
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| owner_id | UUID | FK, NOT NULL |
| name | TEXT | NOT NULL |
| currency | TEXT | DEFAULT 'USD' |
| opening_date | DATE | NOT NULL |
| starting_cash | NUMERIC(14,2) | |
| benchmark_model_id | TEXT | |
| benchmark_ticker | TEXT | |
| notes | TEXT | |
| is_archived | BOOLEAN | DEFAULT false |

## transactions
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| portfolio_id | UUID | FK, NOT NULL |
| security_id | UUID | FK (null for cash movements) |
| event_type | TEXT | CHECK (BUY/SELL/DIVIDEND/DEPOSIT/WITHDRAWAL/FEE/TAX/INTEREST/SPLIT/SYMBOL_CHANGE/MERGER/SPINOFF/ADJUSTMENT/CORRECTION) |
| event_date | DATE | NOT NULL |
| quantity | NUMERIC(14,6) | |
| price | NUMERIC(14,4) | |
| gross_amount | NUMERIC(14,2) | |
| commission | NUMERIC(10,2) | |
| tax | NUMERIC(10,2) | |
| fx_rate | NUMERIC(12,6) | |
| notes | TEXT | |
| idempotency_key | TEXT | UNIQUE |
| corrected_by | UUID | FK (self) |
| owner_id | UUID | FK |

## price_observations
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| security_id | UUID | FK |
| observation_date | DATE | NOT NULL |
| open | NUMERIC(12,4) | |
| high | NUMERIC(12,4) | |
| low | NUMERIC(12,4) | |
| close | NUMERIC(12,4) | |
| adj_close | NUMERIC(12,4) | |
| volume | BIGINT | |
| source | TEXT | |
| UNIQUE(security_id, observation_date) | | |

## portfolio_valuations
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| portfolio_id | UUID | FK |
| valuation_date | DATE | NOT NULL |
| total_value | NUMERIC(14,2) | |
| cash_balance | NUMERIC(14,2) | |
| total_cost | NUMERIC(14,2) | |
| realized_pl | NUMERIC(14,2) | |
| unrealized_pl | NUMERIC(14,2) | |
| UNIQUE(portfolio_id, valuation_date) | | |

## benchmark_valuations
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| benchmark_ticker | TEXT | NOT NULL |
| valuation_date | DATE | NOT NULL |
| price | NUMERIC(12,4) | |
| total_return_index | NUMERIC(14,6) | |
| UNIQUE(benchmark_ticker, valuation_date) | | |

## rebalance_events
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| portfolio_id | UUID | FK |
| model_snapshot_id | UUID | FK |
| rebalance_date | DATE | NOT NULL |
| status | TEXT | CHECK (PENDING/COMPLETED/CANCELLED) |
| estimated_cost | NUMERIC(12,2) | |
| completed_at | TIMESTAMPTZ | |

## rebalance_lines
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| rebalance_event_id | UUID | FK |
| security_id | UUID | FK |
| current_quantity | NUMERIC(14,6) | |
| target_quantity | NUMERIC(14,6) | |
| illustrative_buy_qty | NUMERIC(14,6) | |
| illustrative_sell_qty | NUMERIC(14,6) | |
| estimated_cost | NUMERIC(10,2) | |

## audit_events
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| owner_id | UUID | FK |
| event_type | TEXT | NOT NULL |
| description | TEXT | |
| ip_address | INET | |
| metadata | JSONB | |
