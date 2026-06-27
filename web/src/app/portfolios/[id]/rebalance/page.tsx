import { createServerSupabase } from "@/lib/supabase";
import { deriveHoldings, totalNav } from "@/lib/holdings";
import Link from "next/link";
import { ArrowLeft, Download, Check } from "lucide-react";
import { redirect } from "next/navigation";

export default async function RebalancePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createServerSupabase();

  // Get latest published model snapshot
  const { data: snapshot } = await supabase
    .from("model_snapshots")
    .select("id, snapshot_id, effective_date")
    .eq("status", "PUBLISHED")
    .order("effective_date", { ascending: false })
    .limit(1)
    .single();

  // Get model holdings
  const modelHoldings = snapshot
    ? await supabase
        .from("model_snapshot_holdings")
        .select("rank, target_weight, security:security_id(ticker, sector, industry)")
        .eq("snapshot_id", snapshot.id)
        .order("rank", { ascending: true })
    : { data: null };

  // Get portfolio transactions
  const { data: transactions } = await supabase
    .from("transactions")
    .select("event_type, event_date, gross_amount, commission, quantity, price, security:security_id(ticker)")
    .eq("portfolio_id", id)
    .is("corrected_by", null)
    .order("event_date", { ascending: true });

  // Derive current holdings
  const txs = (transactions || []).map((t: any) => ({
    event_type: t.event_type, event_date: t.event_date,
    ticker: t.security?.ticker || "", quantity: t.quantity || 0,
    price: t.price || 0, gross_amount: t.gross_amount,
    commission: t.commission || 0, tax_amount: 0,
    corrected_by: undefined,
  }));
  const state = deriveHoldings(txs);
  const nav = totalNav(state);

  // Build comparison
  const modelMap = new Map((modelHoldings?.data || []).map((h: any) => [
    h.security?.ticker, h.target_weight
  ]));

  const comparisons = [...new Set([
    ...state.holdings.keys(),
    ...modelMap.keys(),
  ])].filter(Boolean).sort().map((ticker) => {
    const h = state.holdings.get(ticker as string);
    const targetW = modelMap.get(ticker as string) || 0;
    const currentW = h?.market_value ? h.market_value / nav : 0;
    return {
      ticker: ticker as string,
      current_weight: (currentW * 100).toFixed(1),
      target_weight: (targetW * 100).toFixed(2),
      action: !h ? "Add" : !targetW ? "Remove" : currentW > targetW * 1.05 ? "Reduce" : currentW < targetW * 0.95 ? "Increase" : "Keep",
    };
  });

  if (!snapshot) {
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <div>
            <h1 className="text-xl font-semibold">Quarterly Review</h1>
            <p className="text-sm text-neutral-500">Model: {snapshot.effective_date}</p>
          </div>
        </div>
      </div>

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

      {comparisons.length === 0 && (
        <div className="card text-center py-12">
          <p className="text-neutral-500">Add transactions and a model snapshot to see comparisons.</p>
        </div>
      )}
    </div>
  );
}
