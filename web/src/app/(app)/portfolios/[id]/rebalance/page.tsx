import { loadRebalance } from "@/lib/route-loaders";
import Link from "next/link";
import { ArrowLeft, AlertTriangle } from "lucide-react";

const STATUS_STYLE: Record<string, string> = {
  Buy: "bg-green-500/10 text-green-400",
  Sell: "bg-red-500/10 text-red-400",
  Add: "bg-green-500/10 text-green-400",
  Reduce: "bg-red-500/10 text-red-400",
  Hold: "bg-neutral-800 text-neutral-300",
};

const STATUS_LABEL: Record<string, string> = {
  Buy: "Buy",
  Sell: "Sell",
  Add: "Add",
  Reduce: "Reduce",
  Hold: "Hold",
};

export default async function RebalancePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let data: Awaited<ReturnType<typeof loadRebalance>> | null = null;
  let error: string | null = null;

  try {
    data = await loadRebalance(id as string);
  } catch (e: unknown) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Rebalance Instructions</h1>
        </div>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!data || data.modelDate === "") {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Rebalance Instructions</h1>
        </div>
        <div className="card text-center py-12">
          <p className="text-neutral-500">No Quarterly Top 30 generated yet. Generate one first.</p>
        </div>
      </div>
    );
  }

  if (data.comparisons.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Rebalance Instructions</h1>
        </div>
        <div className="card text-center py-12">
          <p className="text-neutral-500">No portfolio holdings yet.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
        <div>
          <h1 className="text-xl font-semibold">Rebalance Instructions</h1>
          <p className="text-sm text-neutral-500">Model date: {data.modelDate}{data.hasPrices ? ` · NAV: $${data.nav.toLocaleString()}` : ""}</p>
        </div>
      </div>

      {!data.hasPrices && (
        <div className="flex items-center gap-2 text-sm text-amber-400 bg-amber-500/10 rounded px-3 py-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          Prices unavailable — rebalance instructions are approximate
        </div>
      )}

      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="table-header">Ticker</th>
                <th className="table-header text-right">Current %</th>
                <th className="table-header text-right">Target %</th>
                {data.hasPrices && (
                  <>
                    <th className="table-header text-right">Current $</th>
                    <th className="table-header text-right">Target $</th>
                  </>
                )}
                <th className="table-header">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.comparisons.map((c) => (
                <tr key={c.ticker} className="border-b border-neutral-800/50">
                  <td className="table-cell-text font-semibold">{c.ticker}</td>
                  <td className="table-cell text-right">{c.currentWeight}%</td>
                  <td className="table-cell text-right">{c.targetWeight}%</td>
                  {data.hasPrices && (
                    <>
                      <td className="table-cell text-right">{c.currentValue ? `$${c.currentValue.toLocaleString()}` : "—"}</td>
                      <td className="table-cell text-right">{c.targetValue ? `$${c.targetValue.toLocaleString()}` : "—"}</td>
                    </>
                  )}
                  <td className="table-cell-text">
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded ${STATUS_STYLE[c.action] || "bg-neutral-800 text-neutral-300"}`}>
                      {STATUS_LABEL[c.action] || c.action}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="text-xs text-neutral-500 text-center">
        Manual decision support only. No orders are placed.
      </div>
    </div>
  );
}
