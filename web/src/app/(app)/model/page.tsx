import { createServerSupabase } from "@/lib/supabase";
import GenerateModelButton from "./GenerateModelButton";

export default async function ModelPage() {
  const supabase = await createServerSupabase();

  const { data: snapshot, error: snapError } = await supabase
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
    .order("effective_date", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (snapError) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Quarterly Top 30</h1>
          <p className="text-sm text-neutral-500 mt-1">M1_B2_QUALITY_VETO_N30</p>
        </div>
        <GenerateModelButton />
      </div>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">Error: {snapError.message}</p>
          <p className="text-sm text-neutral-500 mt-2">Ensure the database migration has been applied and a model snapshot has been published.</p>
        </div>
      </div>
    );
  }

  const model = snapshot as {
    id: string;
    snapshot_id: string;
    effective_date: string;
    status: string;
    published_at: string | null;
    model_version: { model_id: string; version: string; description: string | null } | null;
    holdings: Array<{
      rank: number;
      target_weight: number;
      b2_score: number | null;
      quality_percentile: number | null;
      quality_components_ok: number;
      inclusion_reason: string | null;
      security: { ticker: string; company_name: string | null; sector: string | null; industry: string | null } | null;
    }>;
  } | null;

  const isUnpublished = model && model.status !== "PUBLISHED";

  return (
    <div className="space-y-6">
      {isUnpublished && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg px-4 py-2 text-sm text-yellow-400">
          Not yet published — currently in {model.status} status
        </div>
      )}

      <div>
        <h1 className="text-2xl font-semibold">Quarterly Top 30</h1>
        <p className="text-sm text-neutral-500 mt-1">M1_B2_QUALITY_VETO_N30</p>
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
          <p className="text-neutral-500">No Quarterly Top 30 generated yet.</p>
          <p className="text-sm text-neutral-600 mt-2">Use the Generate button on the Dashboard to create this quarter&apos;s Top 30.</p>
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
