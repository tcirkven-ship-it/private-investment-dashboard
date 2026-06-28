import { loadModelHistory } from "@/lib/route-loaders";
import Link from "next/link";

export default async function ModelHistoryPage() {
  let snapshots: Awaited<ReturnType<typeof loadModelHistory>> = [];
  let error: string | null = null;

  try {
    snapshots = await loadModelHistory();
  } catch (e: unknown) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Model History</h1>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/model" className="btn-ghost p-1"><span className="text-lg">←</span></Link>
        <h1 className="text-xl font-semibold">Model History</h1>
      </div>

      {snapshots.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No snapshots imported yet.</p>
          <p className="text-sm text-neutral-600 mt-2">Import a model snapshot on the Settings page.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {snapshots.map((s) => (
            <div key={s.id} className="card flex items-center justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold">{s.effective_date}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                    s.status === "PUBLISHED" ? "bg-green-500/10 text-green-400" : "bg-neutral-800 text-neutral-400"
                  }`}>{s.status}</span>
                </div>
                <p className="text-sm text-neutral-500 mt-0.5">ID: {s.snapshot_id}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
