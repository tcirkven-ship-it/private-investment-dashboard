/** Shared TypeScript types for route integration */

export interface ModelSnapshotSummary {
  id: string;
  snapshot_id: string;
  effective_date: string;
  status: string;
  created_at: string;
}

export interface ModelHoldingSecurity {
  ticker: string;
  company_name: string | null;
  sector: string | null;
  industry: string | null;
}

export interface ModelHolding {
  rank: number;
  target_weight: number;
  b2_score: number | null;
  quality_percentile: number | null;
  quality_components_ok: number;
  inclusion_reason: string | null;
  security: ModelHoldingSecurity | null;
}

export interface ModelSnapshot {
  id: string;
  snapshot_id: string;
  effective_date: string;
  status: string;
  published_at: string | null;
  model_version: { model_id: string; version: string; description: string | null } | null;
  holdings: ModelHolding[];
}

export interface PortfolioRow {
  id: string;
  name: string;
  currency: string;
  opening_date: string;
  is_archived: boolean;
  created_at: string;
}

export interface TransactionRow {
  id: string;
  event_type: string;
  event_date: string;
  quantity: number | null;
  price: number | null;
  gross_amount: number;
  commission: number | null;
  tax: number | null;
  notes: string | null;
  created_at: string;
  security_ticker: string | null;
}

export interface BenchmarkRow {
  observation_date: string;
  total_return_index: number;
}

export interface PriceRow {
  ticker: string;
  adj_close: number;
  observation_date: string;
}

export interface HoldingView {
  ticker: string;
  quantity: number;
  average_cost: number;
  market_value: number;
  unrealized_pl: number;
  weight: number;
}

export interface RebalanceComparison {
  ticker: string;
  current_weight: string;
  target_weight: string;
  action: "Add" | "Remove" | "Reduce" | "Increase" | "Keep";
}
