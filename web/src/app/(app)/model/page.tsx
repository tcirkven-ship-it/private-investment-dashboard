import { getLatestModelSnapshot } from "@/lib/supabase-queries";
import GenerateModelButton from "@/components/model/GenerateModelButton";
import Link from "next/link";

export default async function ModelPage() {
  const result = await getLatestModelSnapshot();

  if (result.error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Quarterly Top 30</h1>
          <GenerateModelButton />
        </div>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">Error: {result.error}</p>
          <p className="text-sm text-neutral-500 mt-2">Ensure the database migration has been applied and a model snapshot has been imported.</p>
        </div>
      </div>
    );
  }

  const model = result.data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Quarterly Top 30</h1>
          <p className="text-sm text-neutral-500 mt-1">M1_B2_QUALITY_VETO_N30</p>
          {model && (
            <div className="flex flex-wrap gap-x-6 gap-y-1 mt-2 text-xs text-neutral-400">
              {(model.model_version?.description || (model.warnings as Record<string, unknown> | null)) && (
                <span>
                  Generation:{" "}
                  <span className="text-neutral-300">
                    {String(model.model_version?.description ?? "") || JSON.stringify(model.warnings)}
                  </span>
                </span>
              )}
              {model.warnings && (
                <>
                  {((model.warnings as Record<string, unknown>).factor_snapshot_date as string) && (
                    <span>
                      Factor snapshot:{" "}
                      <span className="text-neutral-300">
                        {(model.warnings as Record<string, unknown>).factor_snapshot_date as string}
                      </span>
                    </span>
                  )}
                  {(model.warnings as Record<string, unknown>).as_of_date && (
                    <span>
                      Factor snapshot:{" "}
                      <span className="text-neutral-300">
                        {String((model.warnings as Record<string, unknown>).as_of_date)}
                      </span>
                    </span>
                  )}
                  {(model.warnings as Record<string, unknown>).generator && (
                    <span>
                      Generator:{" "}
                      <span className="text-neutral-300">
                        {String((model.warnings as Record<string, unknown>).generator)}
                      </span>
                    </span>
                  )}
                </>
              )}
            </div>
          )}
        </div>
        <GenerateModelButton />
      </div>

      {model?.status === "DRAFT" && (
        <div className="card border-yellow-500/30 bg-yellow-500/5">
          <p className="text-sm text-yellow-400">
            Not yet published &mdash; currently in DRAFT status
          </p>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="metric-label">Model</p>
          <p className="text-sm font-semibold mt-1">{model?.model_version?.model_id || "—"}</p>
        </div>
        <div className="card">
          <p className="metric-label">Effective Date</p>
          <p className="text-sm font-semibold mt-1">{model?.effective_date || "—"}</p>
        </div>
        <div className="card">
          <p className="metric-label">Holdings</p>
          <p className="text-sm font-semibold mt-1">{model?.holdings?.length || 0}</p>
        </div>
        <div className="card">
          <p className="metric-label">Status</p>
          <p className={`text-sm font-semibold mt-1 ${model?.status === "PUBLISHED" ? "text-green-400" : model?.status === "DRAFT" ? "text-yellow-400" : "text-neutral-400"}`}>
            {model?.status || "None"}
          </p>
        </div>
      </div>

      {!model ? (
        <div className="card text-center py-12">
            <p className="text-neutral-500">No official model loaded yet.</p>
            <p className="text-sm text-neutral-600 mt-2">
              Load the notebook-generated Top 30 CSV from the Dashboard.
            </p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="table-header">#</th>
                  <th className="table-header">Ticker</th>
                  <th className="table-header">Company</th>
                  <th className="table-header">Sector</th>
                  <th className="table-header">Industry</th>
                  <th className="table-header text-right">Target Weight</th>
                  <th className="table-header text-right">B2 Score</th>
                  <th className="table-header text-right">Quality %ile</th>
                </tr>
              </thead>
              <tbody>
                {[...model.holdings]
                  .sort((a, b) => a.rank - b.rank)
                  .map((h) => (
                    <tr key={h.rank} className="border-b border-neutral-800/50">
                      <td className="table-cell text-neutral-500">{h.rank}</td>
                      <td className="table-cell-text font-semibold">{h.security?.ticker ?? "—"}</td>
                      <td className="table-cell-text text-sm text-neutral-400">{h.security?.company_name ?? "—"}</td>
                      <td className="table-cell-text text-sm">{h.security?.sector ?? "—"}</td>
                      <td className="table-cell-text text-sm text-neutral-400">{h.security?.industry ?? "—"}</td>
                      <td className="table-cell text-right">{(h.target_weight * 100).toFixed(1)}%</td>
                      <td className="table-cell text-right">{h.b2_score?.toFixed(3) ?? "—"}</td>
                      <td className="table-cell text-right">{h.quality_percentile?.toFixed(3) ?? "—"}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="flex gap-4 mt-4">
        <Link href="/model/history" className="btn-ghost text-sm">View Model History →</Link>
        <Link href="/portfolios" className="btn-ghost text-sm">View My Portfolio & Rebalance →</Link>
      </div>
    </div>
  );
}
