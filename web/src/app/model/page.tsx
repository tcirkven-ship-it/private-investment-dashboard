import { getPublishedModel } from "@/lib/supabase-queries";
import Link from "next/link";

export default async function ModelPage() {
  const result = await getPublishedModel();

  if (result.error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Official Model</h1>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">Error: {result.error}</p>
          <p className="text-sm text-neutral-500 mt-2">Ensure the database migration has been applied and a model snapshot has been published.</p>
        </div>
      </div>
    );
  }

  const model = result.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Official Model</h1>
        <p className="text-sm text-neutral-500 mt-1">M1 B2 Quality Veto N30</p>
      </div>

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
          <p className={`text-sm font-semibold mt-1 ${model?.status === "PUBLISHED" ? "text-green-400" : "text-yellow-400"}`}>
            {model?.status || "None"}
          </p>
        </div>
      </div>

      {!model ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No published model snapshot.</p>
          <p className="text-sm text-neutral-600 mt-2">
            Import via <Link href="/admin/model-import" className="text-blue-400 hover:underline">Model Import</Link>.
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
                  <th className="table-header">Name</th>
                  <th className="table-header text-right">Weight</th>
                  <th className="table-header text-right">B2</th>
                  <th className="table-header text-right">Q %ile</th>
                  <th className="table-header">Sector</th>
                  <th className="table-header">Reason</th>
                </tr>
              </thead>
              <tbody>
                {[...model.holdings]
                  .sort((a, b) => a.rank - b.rank)
                  .map((h) => (
                    <tr key={h.rank} className="border-b border-neutral-800/50">
                      <td className="table-cell text-neutral-500">{h.rank}</td>
                      <td className="table-cell-text font-semibold">{h.security?.ticker ?? "—"}</td>
                      <td className="table-cell-text text-sm text-neutral-400">{h.security?.company_name ?? ""}</td>
                      <td className="table-cell text-right">{(h.target_weight * 100).toFixed(1)}%</td>
                      <td className="table-cell text-right">{h.b2_score?.toFixed(3) ?? "—"}</td>
                      <td className="table-cell text-right">{h.quality_percentile?.toFixed(3) ?? "—"}</td>
                      <td className="table-cell-text text-sm">{h.security?.sector ?? "—"}</td>
                      <td className="table-cell-text text-sm text-neutral-400 max-w-xs truncate">{h.inclusion_reason ?? ""}</td>
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
