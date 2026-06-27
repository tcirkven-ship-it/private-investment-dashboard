/**
 * Route-level data loaders with typed I/O.
 * Extracted from page components so they can be tested independently.
 */

import { createServerSupabase } from "./supabase";
import { deriveHoldings, totalNav, type Transaction } from "./holdings";
import { getTransaction, getModelHolding, getPriceObservation, getBenchmarkObs } from "./adapters";

// ─── Model history ─────────────────────────────────────────────

export interface ModelHistoryRecord {
  id: string;
  snapshot_id: string;
  effective_date: string;
  status: string;
}

export async function loadModelHistory(): Promise<ModelHistoryRecord[]> {
  const supabase = await createServerSupabase();
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

// ─── Transactions for a portfolio ──────────────────────────────

export async function loadTransactions(portfolioId: string): Promise<TransactionData[]> {
  const supabase = await createServerSupabase();
  const { data, error } = await supabase
    .from("transactions")
    .select("id, event_type, event_date, quantity, price, gross_amount, commission, tax_amount, notes, created_at, security:security_id(ticker)")
    .eq("portfolio_id", portfolioId)
    .is("corrected_by", null)
    .order("event_date", { ascending: true });
  if (error) throw new Error(`Failed to load transactions: ${error.message}`);
  return (data || []).map(getTransaction).filter((t: TransactionData | null): t is TransactionData => t !== null);
}

// ─── Holdings with prices ──────────────────────────────────────

import type { TransactionData } from "./adapters";

export interface HoldingsResult {
  transactions: Transaction[];
  state: ReturnType<typeof deriveHoldings>;
  nav: number;
  priceCount: number;
}

export async function loadHoldings(portfolioId: string): Promise<HoldingsResult> {
  const supabase = await createServerSupabase();
  const [txData, priceData] = await Promise.all([
    loadTransactions(portfolioId),
    supabase
      .from("price_observations")
      .select("close, observation_date, security:security_id(ticker)")
      .order("observation_date", { ascending: false })
      .limit(2000),
  ]);

  const priceMap = new Map<string, number>();
  if (priceData.data) {
    for (const row of priceData.data) {
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
    tax_amount: t.tax_amount,
    corrected_by: undefined,
  }));

  const state = deriveHoldings(txs, priceMap);
  const nav = totalNav(state);
  return { transactions: txs, state, nav, priceCount: priceMap.size };
}

// ─── Benchmark returns ─────────────────────────────────────────

export interface BenchmarkReturns {
  spyReturn: number | null;
  qqqReturn: number | null;
}

export async function loadBenchmarkReturns(): Promise<BenchmarkReturns> {
  const supabase = await createServerSupabase();
  const [spyResult, qqqResult] = await Promise.all([
    supabase
      .from("benchmark_observations")
      .select("observation_date, total_return_index")
      .eq("ticker", "SPY")
      .order("observation_date", { ascending: false })
      .limit(2),
    supabase
      .from("benchmark_observations")
      .select("observation_date, total_return_index")
      .eq("ticker", "QQQ")
      .order("observation_date", { ascending: false })
      .limit(2),
  ]);

  const spyReturn = spyResult.data && spyResult.data.length >= 2
    ? (Number(spyResult.data[0].total_return_index) / Number(spyResult.data[1].total_return_index) - 1) * 100
    : null;
  const qqqReturn = qqqResult.data && qqqResult.data.length >= 2
    ? (Number(qqqResult.data[0].total_return_index) / Number(qqqResult.data[1].total_return_index) - 1) * 100
    : null;
  return { spyReturn, qqqReturn };
}

// ─── Rebalance comparison ──────────────────────────────────────

export interface RebalanceLine {
  ticker: string;
  currentWeight: string;
  targetWeight: string;
  action: "Add" | "Remove" | "Reduce" | "Increase" | "Keep";
}

export async function loadRebalance(portfolioId: string): Promise<{
  modelDate: string;
  comparisons: RebalanceLine[];
  hasPrices: boolean;
}> {
  const supabase = await createServerSupabase();
  const snapResult = await supabase
    .from("model_snapshots")
    .select("id, snapshot_id, effective_date")
    .eq("status", "PUBLISHED")
    .order("effective_date", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (snapResult.error) throw new Error(`Failed to load model: ${snapResult.error.message}`);
  if (!snapResult.data) return { modelDate: "", comparisons: [], hasPrices: false };

  const snapshot = snapResult.data;
  const modelId = String(snapshot.id);

  const [modelResult, holdingsResult] = await Promise.all([
    supabase
      .from("model_snapshot_holdings")
      .select("rank, target_weight, security:security_id(ticker)")
      .eq("snapshot_id", modelId),
    loadHoldings(portfolioId),
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
    const isNew = !h || h.quantity <= 0;
    const isRemoved = targetW === 0;
    let action: RebalanceLine["action"] = "Keep";
    if (isNew) action = "Add";
    else if (isRemoved) action = "Remove";
    else if (currentW > targetW * 1.05) action = "Reduce";
    else if (targetW > 0 && currentW < targetW * 0.95) action = "Increase";
    return {
      ticker,
      currentWeight: (currentW * 100).toFixed(1),
      targetWeight: (targetW * 100).toFixed(2),
      action,
    };
  });

  return {
    modelDate: String(snapshot.effective_date ?? ""),
    comparisons,
    hasPrices: priceCount > 0,
  };
}
