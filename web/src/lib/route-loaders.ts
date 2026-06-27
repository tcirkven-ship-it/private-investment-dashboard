/**
 * Route-level data loaders with injectable Supabase client.
 * Defaults to real server Supabase when no client is provided.
 */

import { createServerSupabase, type SupabaseClient } from "./supabase";
import { deriveHoldings, totalNav, type Transaction } from "./holdings";
import { getTransaction, getModelHolding, getPriceObservation } from "./adapters";

type DB = SupabaseClient;

export interface ModelHistoryRecord {
  id: string;
  snapshot_id: string;
  effective_date: string;
  status: string;
}

export async function loadModelHistory(db?: DB): Promise<ModelHistoryRecord[]> {
  const supabase = db ?? await createServerSupabase();
  const { data, error } = await supabase
    .from("model_snapshots")
    .select("id, snapshot_id, effective_date, status")
    .order("effective_date", { ascending: false });
  if (error) throw new Error(`Failed to load model history: ${error.message}`);
  return (data || []).map((r: Record<string, unknown>) => ({
    id: String(r.id ?? ""),
    snapshot_id: String(r.snapshot_id ?? ""),
    effective_date: String(r.effective_date ?? ""),
    status: String(r.status ?? ""),
  }));
}

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

export async function loadTransactions(portfolioId: string, db?: DB): Promise<TransactionData[]> {
  const supabase = db ?? await createServerSupabase();
  const { data, error } = await supabase
    .from("transactions")
    .select("id, event_type, event_date, quantity, price, gross_amount, commission, tax, notes, created_at, security:security_id(ticker)")
    .eq("portfolio_id", portfolioId)
    .is("corrected_by", null)
    .order("event_date", { ascending: true });
  if (error) throw new Error(`Failed to load transactions: ${error.message}`);
  return (data || []).map(getTransaction).filter((t): t is TransactionData => t !== null);
}

export interface HoldingsResult {
  transactions: Transaction[];
  state: ReturnType<typeof deriveHoldings>;
  nav: number;
  priceCount: number;
}

export async function loadHoldings(portfolioId: string, db?: DB): Promise<HoldingsResult> {
  const supabase = db ?? await createServerSupabase();
  const txData = await loadTransactions(portfolioId, supabase);

  const { data: priceData } = await supabase
    .from("price_observations")
    .select("close, observation_date, security:security_id(ticker)")
    .order("observation_date", { ascending: false })
    .limit(2000);

  const priceMap = new Map<string, number>();
  if (priceData) {
    for (const row of priceData) {
      const obs = getPriceObservation(row);
      if (obs && !priceMap.has(obs.ticker)) {
        priceMap.set(obs.ticker, obs.close);
      }
    }
  }

  const txs: Transaction[] = txData.map((t) => ({
    event_type: t.event_type as Transaction["event_type"],
    event_date: t.event_date,
    ticker: t.ticker,
    quantity: t.quantity,
    price: t.price,
    gross_amount: t.gross_amount,
    commission: t.commission,
    tax: t.tax,
    corrected_by: undefined,
  }));

  const state = deriveHoldings(txs, priceMap);
  return { transactions: txs, state, nav: totalNav(state), priceCount: priceMap.size };
}

export interface BenchmarkReturns {
  spyReturn: number | null;
  qqqReturn: number | null;
}

export async function loadBenchmarkReturns(db?: DB): Promise<BenchmarkReturns> {
  const supabase = db ?? await createServerSupabase();
  const [spyResult, qqqResult] = await Promise.all([
    supabase.from("benchmark_observations")
      .select("observation_date, total_return_index")
      .eq("ticker", "SPY")
      .order("observation_date", { ascending: false })
      .limit(2),
    supabase.from("benchmark_observations")
      .select("observation_date, total_return_index")
      .eq("ticker", "QQQ")
      .order("observation_date", { ascending: false })
      .limit(2),
  ]);

  if (spyResult.error) throw new Error(`Failed to load SPY benchmark: ${spyResult.error.message}`);
  if (qqqResult.error) throw new Error(`Failed to load QQQ benchmark: ${qqqResult.error.message}`);

  const calcReturn = (data: { total_return_index: number }[] | null): number | null => {
    if (!data || data.length < 2) return null;
    return (Number(data[0].total_return_index) / Number(data[1].total_return_index) - 1) * 100;
  };
  return { spyReturn: calcReturn(spyResult.data), qqqReturn: calcReturn(qqqResult.data) };
}

export interface RebalanceLine {
  ticker: string;
  currentWeight: string;
  targetWeight: string;
  action: "Add" | "Remove" | "Reduce" | "Increase" | "Keep";
}

export interface RebalanceResult {
  modelDate: string;
  comparisons: RebalanceLine[];
  hasPrices: boolean;
}

export async function loadRebalance(portfolioId: string, db?: DB): Promise<RebalanceResult> {
  const supabase = db ?? await createServerSupabase();
  const snapResult = await supabase
    .from("model_snapshots")
    .select("id, effective_date")
    .eq("status", "PUBLISHED")
    .order("effective_date", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (snapResult.error) throw new Error(`Failed to load model: ${snapResult.error.message}`);
  if (!snapResult.data) return { modelDate: "", comparisons: [], hasPrices: false };

  const snapId = String(snapResult.data.id);

  const [modelResult, holdingsResult] = await Promise.all([
    supabase.from("model_snapshot_holdings")
      .select("rank, target_weight, security:security_id(ticker)")
      .eq("snapshot_id", snapId),
    loadHoldings(portfolioId, supabase),
  ]);

  const modelTargets = new Map<string, number>();
  if (modelResult.data) {
    for (const row of modelResult.data) {
      const h = getModelHolding(row);
      if (h) modelTargets.set(h.ticker, h.target_weight);
    }
  }

  const { state, nav, priceCount } = holdingsResult;
  const allTickers = [...new Set([...state.holdings.keys(), ...modelTargets.keys()])].filter(Boolean).sort();

  const comparisons: RebalanceLine[] = allTickers.map((ticker) => {
    const h = state.holdings.get(ticker);
    const targetW = modelTargets.get(ticker) || 0;
    const currentW = h?.market_value && nav > 0 ? h.market_value / nav : 0;
    let action: RebalanceLine["action"] = "Keep";
    if (!h || h.quantity <= 0) action = "Add";
    else if (targetW === 0) action = "Remove";
    else if (currentW > targetW * 1.05) action = "Reduce";
    else if (targetW > 0 && currentW < targetW * 0.95) action = "Increase";
    return { ticker, currentWeight: (currentW * 100).toFixed(1), targetWeight: (targetW * 100).toFixed(2), action };
  });

  return { modelDate: String(snapResult.data.effective_date ?? ""), comparisons, hasPrices: priceCount > 0 };
}
