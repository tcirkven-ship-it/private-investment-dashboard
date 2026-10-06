import { createServerSupabase } from "./supabase";
import { cache } from "react";

export interface ModelSnapshot {
  id: string;
  snapshot_id: string;
  effective_date: string;
  status: string;
  published_at: string | null;
  warnings: Record<string, unknown> | null;
  model_version: { model_id: string; version: string; description: string | null } | null;
  holdings: Array<{
    rank: number;
    target_weight: number;
    b2_score: number | null;
    quality_percentile: number | null;
    quality_components_ok: number;
    inclusion_reason: string | null;
    security: { ticker: string; company_name: string | null; sector: string | null; industry: string | null } | null;
  }>;
}

export interface Portfolio {
  id: string;
  name: string;
  currency: string;
  opening_date: string;
  is_archived: boolean;
  created_at: string;
}

export interface Transaction {
  id: string;
  event_type: string;
  event_date: string;
  quantity: number | null;
  price: number | null;
  gross_amount: number;
  commission: number | null;
  tax: number | null;
  security_ticker: string | null;
  notes: string | null;
  created_at: string;
}

export interface QueryResult<T> {
  data: T | null;
  error: string | null;
}

export const getPublishedModel = cache(async (): Promise<QueryResult<ModelSnapshot>> => {
  const supabase = await createServerSupabase();
  const { data, error } = await supabase
    .from("model_snapshots")
    .select(`
      id, snapshot_id, effective_date, status, published_at, warnings,
      model_version:model_version_id(model_id, version, description),
      holdings:model_snapshot_holdings(
        rank, target_weight, b2_score, quality_percentile,
        quality_components_ok, inclusion_reason,
        security:security_id(ticker, company_name, sector, industry)
      )
    `)
    .eq("status", "PUBLISHED")
    .order("effective_date", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) return { data: null, error: `Failed to load model: ${error.message}` };
  return { data: data as ModelSnapshot | null, error: null };
});

export const getLatestModelSnapshot = cache(async (): Promise<QueryResult<ModelSnapshot>> => {
  const supabase = await createServerSupabase();
  const { data, error } = await supabase
    .from("model_snapshots")
    .select(`
      id, snapshot_id, effective_date, status, published_at, warnings,
      model_version:model_version_id(model_id, version, description),
      holdings:model_snapshot_holdings(
        rank, target_weight, b2_score, quality_percentile,
        quality_components_ok, inclusion_reason,
        security:security_id(ticker, company_name, sector, industry)
      )
    `)
    .eq("status", "PUBLISHED")
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) return { data: null, error: `Failed to load model: ${error.message}` };
  return { data: data as ModelSnapshot | null, error: null };
});

export const getModelCounts = cache(async (): Promise<{ published: number; draft: number }> => {
  const supabase = await createServerSupabase();
  const [pubRes, draftRes] = await Promise.all([
    supabase.from("model_snapshots").select("*", { count: "exact", head: true }).eq("status", "PUBLISHED"),
    supabase.from("model_snapshots").select("*", { count: "exact", head: true }).eq("status", "DRAFT"),
  ]);
  return {
    published: pubRes.count ?? 0,
    draft: draftRes.count ?? 0,
  };
});

export const getModelHistory = cache(async (): Promise<QueryResult<Record<string, unknown>[]>> => {
  const supabase = await createServerSupabase();
  const { data, error } = await supabase
    .from("model_snapshots")
    .select("id, snapshot_id, effective_date, status, warnings, created_at")
    .eq("status", "PUBLISHED")
    .order("effective_date", { ascending: false });
  if (error) return { data: null, error: error.message };
  const enriched = (data || []).map((s: Record<string, unknown>) => {
    const w = s.warnings as Record<string, unknown> | string | null;
    let wo: Record<string, unknown> = {};
    if (w) {
      if (typeof w === "string") { try { wo = JSON.parse(w) as Record<string, unknown>; } catch { wo = {}; } }
      else { wo = w as Record<string, unknown>; }
    }
    return {
      ...s,
      quarter_label: wo?.quarter_label || null,
      generated_at: wo?.generated_at || null,
      source: wo?.source || null,
    };
  });
  return { data: enriched || [], error: null };
});

export const getModelSnapshotById = cache(async (id: string): Promise<QueryResult<ModelSnapshot>> => {
  const supabase = await createServerSupabase();
  const { data, error } = await supabase
    .from("model_snapshots")
    .select(`
      id, snapshot_id, effective_date, status, published_at, warnings,
      model_version:model_version_id(model_id, version, description),
      holdings:model_snapshot_holdings(
        rank, target_weight, b2_score, quality_percentile,
        quality_components_ok, inclusion_reason,
        security:security_id(ticker, company_name, sector, industry)
      )
    `)
    .eq("id", id)
    .eq("status", "PUBLISHED")
    .maybeSingle();
  if (error) return { data: null, error: `Failed to load snapshot: ${error.message}` };
  return { data: data as ModelSnapshot | null, error: null };
});

export const getPortfolios = cache(async (): Promise<QueryResult<Portfolio[]>> => {
  const supabase = await createServerSupabase();
  const { data, error } = await supabase
    .from("portfolios")
    .select("id, name, currency, opening_date, is_archived, created_at")
    .is("is_archived", false)
    .order("created_at", { ascending: false });
  if (error) return { data: null, error: error.message };
  return { data: data as Portfolio[], error: null };
});

export const getTransactions = cache(async (portfolioId: string): Promise<QueryResult<Transaction[]>> => {
  const supabase = await createServerSupabase();
  const { data, error } = await supabase
    .from("transactions")
    .select(`
      id, event_type, event_date, quantity, price, gross_amount, commission, tax, notes, created_at,
      security:security_id(ticker)
    `)
    .eq("portfolio_id", portfolioId)
    .is("corrected_by", null)
    .order("event_date", { ascending: false });
  if (error) return { data: null, error: error.message };
  const transactions = (data || []).map((t: Record<string, unknown>) => {
    const sec = t.security as { ticker?: string } | null;
    return { ...t, security_ticker: sec?.ticker || null };
  });
  return { data: transactions as Transaction[], error: null };
});
