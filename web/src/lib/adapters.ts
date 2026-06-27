/**
 * Type-safe adapter functions for Supabase join results.
 * Supabase may return joined relations as object or array depending on
 * relationship cardinality. These adapters normalize the shape.
 */

// ─── Security join adapter ─────────────────────────────────────

interface SecurityJoin {
  ticker: string;
  company_name?: string | null;
  sector?: string | null;
  industry?: string | null;
}

export function getSecurity(row: unknown): SecurityJoin | null {
  if (!row || typeof row !== "object") return null;
  const r = row as Record<string, unknown>;
  // Supabase may return single object or array with one element
  const target = Array.isArray(r) ? (r.length > 0 ? (r[0] as Record<string, unknown>) : null) : r;
  if (!target) return null;
  if (typeof target.ticker !== "string") return null;
  return {
    ticker: target.ticker,
    company_name: typeof target.company_name === "string" ? target.company_name : null,
    sector: typeof target.sector === "string" ? target.sector : null,
    industry: typeof target.industry === "string" ? target.industry : null,
  };
}

export function getTicker(securityJoin: unknown): string {
  return getSecurity(securityJoin)?.ticker ?? "";
}

// ─── Price observation adapter ─────────────────────────────────

export interface PriceObservation {
  ticker: string;
  close: number;
}

export function getPriceObservation(row: unknown): PriceObservation | null {
  if (!row || typeof row !== "object") return null;
  const r = row as Record<string, unknown>;
  const sec = getSecurity(r.security);
  if (!sec) return null;
  const close = typeof r.close === "number" ? r.close : Number(r.close ?? NaN);
  if (!isFinite(close)) return null;
  return { ticker: sec.ticker, close };
}

// ─── Benchmark observation adapter ─────────────────────────────

export interface BenchmarkObs {
  observation_date: string;
  total_return_index: number;
}

export function getBenchmarkObs(row: unknown): BenchmarkObs | null {
  if (!row || typeof row !== "object") return null;
  const r = row as Record<string, unknown>;
  const tri = typeof r.total_return_index === "number" ? r.total_return_index : Number(r.total_return_index ?? NaN);
  if (!isFinite(tri)) return null;
  return {
    observation_date: String(r.observation_date ?? ""),
    total_return_index: tri,
  };
}

// ─── Model holding adapter ─────────────────────────────────────

export interface ModelHoldingRow {
  rank: number;
  target_weight: number;
  ticker: string;
}

export function getModelHolding(row: unknown): ModelHoldingRow | null {
  if (!row || typeof row !== "object") return null;
  const r = row as Record<string, unknown>;
  const rank = typeof r.rank === "number" ? r.rank : NaN;
  const tw = typeof r.target_weight === "number" ? r.target_weight : Number(r.target_weight ?? NaN);
  if (!isFinite(rank) || !isFinite(tw)) return null;
  const sec = getSecurity(r.security);
  return { rank, target_weight: tw, ticker: sec?.ticker ?? "" };
}

// ─── Transaction row adapter ───────────────────────────────────

export interface TransactionData {
  id: string;
  event_type: string;
  event_date: string;
  quantity: number;
  price: number;
  gross_amount: number;
  commission: number;
  tax: number;
  ticker: string;
  notes: string | null;
  created_at: string;
}

export function getTransaction(row: unknown): TransactionData | null {
  if (!row || typeof row !== "object") return null;
  const r = row as Record<string, unknown>;
  if (typeof r.id !== "string") return null;
  return {
    id: r.id,
    event_type: String(r.event_type ?? ""),
    event_date: String(r.event_date ?? ""),
    quantity: typeof r.quantity === "number" ? r.quantity : 0,
    price: typeof r.price === "number" ? r.price : 0,
    gross_amount: typeof r.gross_amount === "number" ? r.gross_amount : 0,
    commission: typeof r.commission === "number" ? r.commission : 0,
    tax: typeof r.tax === "number" ? r.tax : Number(r.tax_amount ?? 0),
    ticker: getTicker(r.security),
    notes: typeof r.notes === "string" ? r.notes : null,
    created_at: String(r.created_at ?? ""),
  };
}
