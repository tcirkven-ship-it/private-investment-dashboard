import { getLatestModelSnapshot, getModelSnapshotById, getModelHistory } from "@/lib/supabase-queries";
import LoadNotebookModelButton from "@/components/model/LoadNotebookModelButton";
import SnapshotSelector from "@/components/model/SnapshotSelector";
import Link from "next/link";

export default async function ModelPage({
  searchParams,
}: {
  searchParams: Promise<{ snapshot?: string }>;
}) {
  const params = await searchParams;
  const snapshotId = params.snapshot || null;

  const [historyResult, result] = await Promise.all([
    getModelHistory(),
    snapshotId
      ? getModelSnapshotById(snapshotId)
      : getLatestModelSnapshot(),
  ]);

  const history = historyResult.data || [];
  const currentSnapshotId = snapshotId || (result.data?.id as string) || null;

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

  const warnings = model?.warnings as Record<string, unknown> | string | null | undefined;
  let warningsObj: Record<string, unknown> | null = null;
  if (warnings) {
    if (typeof warnings === "string") {
      try { warningsObj = JSON.parse(warnings) as Record<string, unknown>; } catch { warningsObj = null; }
    } else {
      warningsObj = warnings as Record<string, unknown>;
    }
  }
  const w = warningsObj || {};
  const asOfDate = w?.as_of_date ? String(w.as_of_date) : null;
  const generatedAt = w?.generated_at ? String(w.generated_at) : null;
  const loadedAt = w?.loaded_at ? String(w.loaded_at) : null;
  const generator = w?.generator ? String(w.generator) : null;
  const quarterLabel = w?.quarter_label ? String(w.quarter_label) : null;
  const fileName = w?.file_name ? String(w.file_name) : null;
  const metadataMissing = w?.metadata_missing as string[] | null | undefined;
  const companyWarning = w?.company_warning ? String(w.company_warning) : null;
  const holdingsCount = model?.holdings?.length || 0;
  const b2ScoresVisible = model?.holdings?.some(h => h.b2_score != null && h.b2_score !== 0) ?? false;
  const qScoresVisible = model?.holdings?.some(h => h.quality_percentile != null && h.quality_percentile !== 0) ?? false;
  const metadataFields = {
    model: "M1_B2_QUALITY_VETO_N30", // hardcoded, always populated
    quarter: quarterLabel,
    as_of_date: asOfDate,
    generated_at: generatedAt,
    loaded_at: loadedAt,
    source: generator,
    file_name: fileName,
  };
  const allMetadataPopulated = Object.values(metadataFields).every(v => v !== null && v !== "");
  const validationPassed = holdingsCount === 30 && allMetadataPopulated && b2ScoresVisible && qScoresVisible;

  const formatTs = (s: string | null): string => {
    if (!s) return "—";
    try { return new Date(s).toLocaleString(); }
    catch { return s; }
  };

  return (
    <div className="space-y-6">
      <LoadNotebookModelButton />
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Quarterly Top 30</h1>
      </div>

      {!model ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">
            No official model loaded yet. Click Load Notebook-Generated Top 30 and select m1_b2_quality_veto_targets.csv.
          </p>
          {history.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-neutral-500 mb-2">Previous snapshots:</p>
              <SnapshotSelector history={history} currentId={null} />
            </div>
          )}
        </div>
      ) : (
        <>
          {history.length > 1 && (
            <SnapshotSelector history={history} currentId={currentSnapshotId} />
          )}
          {!validationPassed && (
            <div className="card border-amber-500/30 bg-amber-500/5 space-y-1">
              <p className="text-sm font-semibold text-amber-400">Warning — metadata incomplete</p>
              {metadataMissing && metadataMissing.length > 0 && (
                <p className="text-sm text-neutral-400">
                  Loaded CSV is missing: {metadataMissing.join(", ")}.
                </p>
              )}
              {!generatedAt && <p className="text-sm text-neutral-400">generated_at is empty.</p>}
              {!loadedAt && <p className="text-sm text-neutral-400">loaded_at is empty.</p>}
              {!generator && <p className="text-sm text-neutral-400">source is empty.</p>}
              {!quarterLabel && <p className="text-sm text-neutral-400">quarter_label is empty.</p>}
              {!fileName && <p className="text-sm text-neutral-400">file_name is empty.</p>}
              {!asOfDate && <p className="text-sm text-neutral-400">as_of_date is empty.</p>}
              {!b2ScoresVisible && <p className="text-sm text-neutral-400">B2 scores are empty.</p>}
              {!qScoresVisible && <p className="text-sm text-neutral-400">Q scores are empty.</p>}
              <p className="text-sm text-neutral-500 mt-1">
                This can be viewed for testing but should not be treated as the official quarterly model.
              </p>
            </div>
          )}

          {companyWarning && (
            <div className="card border-amber-500/30 bg-amber-500/5 space-y-1">
              <p className="text-sm font-semibold text-amber-400">Note</p>
              <p className="text-sm text-neutral-400">{companyWarning}</p>
            </div>
          )}

          <div className="card space-y-2 text-sm">
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">Model:</span>
              <span className="text-neutral-200 font-semibold">M1_B2_QUALITY_VETO_N30</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">Quarter:</span>
              <span className="text-neutral-200">{quarterLabel || "—"}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">As-of date:</span>
              <span className="text-neutral-200">{asOfDate || model.effective_date || "—"}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">Generated at:</span>
              <span className="text-neutral-200">{formatTs(generatedAt)}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">Loaded at:</span>
              <span className="text-neutral-200">{formatTs(loadedAt)}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">Source:</span>
              <span className="text-neutral-200">{generator || "—"}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">File name:</span>
              <span className="text-neutral-200">{fileName || "—"}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">Holdings:</span>
              <span className="text-neutral-200">{holdingsCount}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-neutral-500 w-28 shrink-0">Validation:</span>
              <span className={validationPassed ? "text-green-400 font-semibold" : "text-red-400 font-semibold"}>
                {validationPassed ? "Passed" : "Incomplete"}
              </span>
            </div>
          </div>

          <div className="card p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px]">
                <colgroup>
                  <col style={{ width: "8%" }} />
                  <col style={{ width: "12%" }} />
                  <col style={{ width: "28%" }} />
                  <col style={{ width: "12%" }} />
                  <col style={{ width: "14%" }} />
                  <col style={{ width: "14%" }} />
                  <col style={{ width: "12%" }} />
                </colgroup>
                <thead>
                  <tr>
                    <th className="table-header td-right">Rank</th>
                    <th className="table-header td-left">Ticker</th>
                    <th className="table-header td-left">Company</th>
                    <th className="table-header td-right">B2 Score</th>
                    <th className="table-header td-right">Q Percentile</th>
                    <th className="table-header td-left">Sector</th>
                    <th className="table-header td-left">Industry</th>
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
                      <tr key={h.rank || h.security?.ticker} className="table-row">
                        <td className="table-cell td-right text-neutral-500">{h.rank || "—"}</td>
                        <td className="table-cell-text td-left font-semibold">{h.security?.ticker ?? "—"}</td>
                        <td className="table-cell-text td-left text-sm text-neutral-400">{h.security?.company_name ?? "—"}</td>
                        <td className="table-cell td-right">{h.b2_score != null && h.b2_score !== 0 ? h.b2_score.toFixed(3) : "—"}</td>
                        <td className="table-cell td-right">{h.quality_percentile != null && h.quality_percentile !== 0 ? h.quality_percentile.toFixed(3) : "—"}</td>
                        <td className="table-cell-text td-left text-sm">{h.security?.sector ?? "—"}</td>
                        <td className="table-cell-text td-left text-sm text-neutral-400">{h.security?.industry ?? "—"}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      <div className="flex gap-4 mt-4">
        <Link href="/compare" className="btn btn-ghost text-sm">Compare to Portfolio →</Link>
      </div>
    </div>
  );
}
