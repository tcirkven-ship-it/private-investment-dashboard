import { createServerSupabase } from "@/lib/supabase";
import { deriveHoldings, totalNav } from "@/lib/holdings";
import type { Transaction } from "@/lib/holdings";
import type { RebalanceComparison } from "@/lib/types";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default async function RebalancePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createServerSupabase();

  const snapResult = await supabase
    .from("model_snapshots")
    .select("id, snapshot_id, effective_date")
    .eq("status", "PUBLISHED")
    .order("effective_date", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (snapResult.error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Quarterly Review</h1>
        </div>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">Error: {snapResult.error.message}</p>
        </div>
      </div>
    );
  }

  if (!snapResult.data) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Quarterly Review</h1>
        </div>
        <div className="card text-center py-12">
          <p className="text-neutral-500">No published model snapshot.</p>
          <p className="text-sm text-neutral-600 mt-2">Import and publish a model snapshot first.</p>
        </div>
      </div>
    );
  }

  const snapshot = snapResult.data;

  const [txResult, modelResult, priceResult] = await Promise.all([
    supabase
      .from("transactions")
      .select("event_type, event_date, gross_amount, commission, quantity, price, security:security_id(ticker)")
      .eq("portfolio_id", id as string)
      .is("corrected_by", null)
      .order("event_date", { ascending: true }),
    supabase
      .from("model_snapshot_holdings")
      .select("rank, target_weight, security:security_id(ticker)")
      .eq("snapshot_id", snapshot.id)
      .order("rank", { ascending: true }),
    supabase
      .from("price_observations")
      .select("close, observation_date, security:security_id(ticker)")
      .order("observation_date", { ascending: false })
      .limit(2000),
  ]);

  if (txResult.error) {
    return <div className="card border-red-500/30 bg-red-500/5"><p className="text-sm text-red-400">Error: {txResult.error.message}</p></div>;
  }

  // Build price map
  const priceMap = new Map<string, number>();
  if (priceResult.data) {
    for (const row of priceResult.data as any[]) {
      const ticker: string | undefined = row.security?.ticker;
      if (ticker && !priceMap.has(ticker) && row.close) {
        priceMap.set(ticker, Number(row.close));
      }
    }
  }

  const txs: Transaction[] = (txResult.data || []).map((t: any) => ({
    event_type: t.event_type, event_date: t.event_date,
    ticker: t.security?.ticker || "", quantity: t.quantity || 0,
    price: t.price || 0, gross_amount: t.gross_amount,
    commission: t.commission || 0, tax_amount: 0,
    corrected_by: undefined,
  }));

  const state = deriveHoldings(txs, priceMap);
  const nav = totalNav(state);

  // Build model target map
  const modelMap = new Map<string, number>();
  if (modelResult.data) {
    for (const row of modelResult.data as any[]) {
      const ticker: string | undefined = row.security?.ticker;
      if (ticker) modelMap.set(ticker, Number(row.target_weight));
    }
  }

  const allTickers = [...new Set([...state.holdings.keys(), ...modelMap.keys()])].filter(Boolean).sort();

  const comparisons: RebalanceComparison[] = allTickers.map((ticker) => {
    const h = state.holdings.get(ticker);
    const targetW = modelMap.get(ticker) || 0;
    const currentW = h?.market_value && nav > 0 ? h.market_value / nav : 0;
    const isNew = !h || h.quantity <= 0;
    const isRemoved = targetW === 0;
    let action: RebalanceComparison["action"] = "Keep";
    if (isNew) action = "Add";
    else if (isRemoved) action = "Remove";
    else if (currentW > targetW * 1.05) action = "Reduce";
    else if (targetW > 0 && currentW < targetW * 0.95) action = "Increase";
    return {
      ticker,
      current_weight: (currentW * 100).toFixed(1),
      target_weight: (targetW * 100).toFixed(2),
      action,
    };
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
        <div>
          <h1 className="text-xl font-semibold">Quarterly Review</h1>
          <p className="text-sm text-neutral-500">Model: {snapshot.effective_date}{priceMap.size === 0 ? " · prices unavailable" : ""}</p>
        </div>
      </div>

      {comparisons.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No comparison data available.</p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="table-header">Ticker</th>
                  <th className="table-header text-right">Current</th>
                  <th className="table-header text-right">Target</th>
                  <th className="table-header">Action</th>
                </tr>
              </thead>
              <tbody>
                {comparisons.map((c) => (
                  <tr key={c.ticker} className="border-b border-neutral-800/50">
                    <td className="table-cell-text font-semibold">{c.ticker}</td>
                    <td className="table-cell text-right">{c.current_weight}%</td>
                    <td className="table-cell text-right">{c.target_weight}%</td>
                    <td className="table-cell-text">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                        c.action === "Add" ? "bg-green-500/10 text-green-400" :
                        c.action === "Remove" ? "bg-red-500/10 text-red-400" :
                        c.action === "Increase" ? "bg-blue-500/10 text-blue-400" :
                        c.action === "Reduce" ? "bg-orange-500/10 text-orange-400" :
                        "bg-neutral-800 text-neutral-300"
                      }`}>{c.action}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
