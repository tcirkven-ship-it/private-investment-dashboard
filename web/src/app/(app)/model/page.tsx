import { getLatestModelSnapshot } from "@/lib/supabase-queries";
import Link from "next/link";

export default async function ModelPage() {
  const result = await getLatestModelSnapshot();

  if (result.error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Quarterly Top 30</h1>
        </div>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">Error: {result.error}</p>
          <p className="text-sm text-neutral-500 mt-2">Ensure the database migration has been applied and a model snapshot has been imported.</p>
        </div>
      </div>
    );
  }

  const model = result.data;

  const warnings = model?.warnings as Record<string, unknown> | null | undefined;
  const asOfDate = warnings?.as_of_date ? String(warnings.as_of_date) : null;
  const generatedAt = warnings?.generated_at ? String(warnings.generated_at) : null;
  const loadedAt = warnings?.loaded_at ? String(warnings.loaded_at) : null;
  const generator = warnings?.generator ? String(warnings.generator) : "offline notebook official generator";
  const holdingsCount = model?.holdings?.length || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Quarterly Top 30</h1>
      </div>

      {!model ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">
            No official model loaded yet. Load the notebook-generated Top 30 CSV from the Dashboard.
          </p>
        </div>
      ) : (
        <>
          <div className="card space-y-2 text-sm">
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">Model:</span>
              <span className="text-neutral-200 font-semibold">M1_B2_QUALITY_VETO_N30</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">As-of date:</span>
              <span className="text-neutral-200">{asOfDate || model.effective_date || "—"}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">Generated at:</span>
              <span className="text-neutral-200">{generatedAt || "—"}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">Loaded at:</span>
              <span className="text-neutral-200">{loadedAt || "—"}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">Source:</span>
              <span className="text-neutral-200">{generator}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">Holdings:</span>
              <span className="text-neutral-200">{holdingsCount}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">Validation:</span>
              <span className="text-green-400 font-semibold">Passed</span>
            </div>
          </div>

          <div className="card p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-neutral-800">
                    <th className="table-header">Rank</th>
                    <th className="table-header">Ticker</th>
                    <th className="table-header">Company</th>
                    <th className="table-header text-right">B2 Score</th>
                    <th className="table-header text-right">Q Percentile</th>
                    <th className="table-header">Sector</th>
                    <th className="table-header">Industry</th>
                  </tr>
                </thead>
                <tbody>
                  {[...model.holdings]
                    .sort((a, b) => {
                      if (a.rank && b.rank) return a.rank - b.rank;
                      if (a.b2_score != null && b.b2_score != null) return b.b2_score - a.b2_score;
                      return 0;
                    })
                    .map((h) => (
                      <tr key={h.rank || h.security?.ticker} className="border-b border-neutral-800/50">
                        <td className="table-cell text-neutral-500">{h.rank || "—"}</td>
                        <td className="table-cell-text font-semibold">{h.security?.ticker ?? "—"}</td>
                        <td className="table-cell-text text-sm text-neutral-400">{h.security?.company_name ?? "—"}</td>
                        <td className="table-cell text-right">{h.b2_score?.toFixed(3) ?? "—"}</td>
                        <td className="table-cell text-right">{h.quality_percentile?.toFixed(3) ?? "—"}</td>
                        <td className="table-cell-text text-sm">{h.security?.sector ?? "—"}</td>
                        <td className="table-cell-text text-sm text-neutral-400">{h.security?.industry ?? "—"}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      <div className="flex gap-4 mt-4">
        <Link href="/model/history" className="btn-ghost text-sm">View Model History →</Link>
        <Link href="/portfolios" className="btn-ghost text-sm">View My Portfolio & Rebalance →</Link>
      </div>
    </div>
  );
}
