// Server-side Supabase queries for production routes

import { createServerSupabase } from "./supabase";
import { cache } from "react";

export const getPublishedModel = cache(async () => {
  const supabase = await createServerSupabase();
  const { data, error } = await supabase
    .from("model_snapshots")
    .select(`
      id, snapshot_id, effective_date, status, published_at,
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
    .single();

  if (error) return null;
  return data;
});

export const getModelHistory = cache(async () => {
  const supabase = await createServerSupabase();
  const { data } = await supabase
    .from("model_snapshots")
    .select("id, snapshot_id, effective_date, status, created_at")
    .order("effective_date", { ascending: false });
  return data || [];
});

export const getPortfolios = cache(async () => {
  const supabase = await createServerSupabase();
  const { data } = await supabase
    .from("portfolios")
    .select("id, name, currency, opening_date, is_archived, created_at")
    .is("is_archived", false)
    .order("created_at", { ascending: false });
  return data || [];
});

export const getTransactions = cache(async (portfolioId: string) => {
  const supabase = await createServerSupabase();
  const { data } = await supabase
    .from("transactions")
    .select("id, event_type, event_date, quantity, price, gross_amount, commission, notes, created_at")
    .eq("portfolio_id", portfolioId)
    .is("corrected_by", null)
    .order("event_date", { ascending: false });
  return data || [];
});
