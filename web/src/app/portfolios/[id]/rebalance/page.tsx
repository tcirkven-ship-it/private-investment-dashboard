import { loadRebalance } from "@/lib/route-loaders";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

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
          <h1 className="text-xl font-semibold">Quarterly Review</h1>
        </div>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!data || data.comparisons.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Quarterly Review</h1>
        </div>
        <div className="card text-center py-12">
          <p className="text-neutral-500">
            {data?.modelDate === "" ? "No published model snapshot." : "No comparison data available."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
        <div>
          <h1 className="text-xl font-semibold">Quarterly Review</h1>
          <p className="text-sm text-neutral-500">
            Model: {data.modelDate}{!data.hasPrices ? " · prices unavailable" : ""}
          </p>
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
              {data.comparisons.map((c) => (
                <tr key={c.ticker} className="border-b border-neutral-800/50">
                  <td className="table-cell-text font-semibold">{c.ticker}</td>
                  <td className="table-cell text-right">{c.currentWeight}%</td>
                  <td className="table-cell text-right">{c.targetWeight}%</td>
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
    </div>
  );
}
