"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Check, X } from "lucide-react";
import { createBrowserClient } from "@supabase/ssr";

interface DraftSnapshot {
  id: string;
  snapshot_id: string;
  status: string;
  effective_date: string;
  model_version_id: string;
  holdings?: Array<{ rank: number; ticker: string; target_weight: number }>;
}

export default function ModelReviewPage() {
  const [drafts, setDrafts] = useState<DraftSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDraft, setSelectedDraft] = useState<DraftSnapshot | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadDrafts() {
    const supabase = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    );
    setLoading(true);
    setError(null);
    const { data, error: err } = await supabase
      .from("model_snapshots")
      .select("id, snapshot_id, status, effective_date, model_version_id")
      .in("status", ["DRAFT", "VALIDATED", "APPROVED"])
      .order("effective_date", { ascending: false });
    if (err) {
      setError(err.message);
    } else {
      setDrafts(data || []);
    }
    setLoading(false);
  }

  useEffect(() => {
    loadDrafts();
  }, []);

  async function handleTransition(newStatus: "VALIDATED" | "APPROVED" | "PUBLISHED") {
    if (!selectedDraft) return;
    setActionMsg(null);
    setError(null);
    const supabase = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    );
    const { error: err } = await supabase
      .from("model_snapshots")
      .update({ status: newStatus, published_at: newStatus === "PUBLISHED" ? new Date().toISOString() : undefined })
      .eq("id", selectedDraft.id);
    if (err) {
      setError(err.message);
    } else {
      const msgs: Record<string, string> = {
        VALIDATED: "Snapshot validated. Ready for approval.",
        APPROVED: "Snapshot approved. Ready to publish.",
        PUBLISHED: "Snapshot published.",
      };
      setActionMsg(msgs[newStatus]);
      setSelectedDraft(null);
      loadDrafts();
    }
  }

  if (loading) {
    return <div className="p-8 text-sm text-neutral-500">Loading...</div>;
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-4">
        <Link href="/settings" className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
        <h1 className="text-xl font-semibold">Model Review</h1>
      </div>

      {error && (
        <div className="text-sm text-red-400 bg-red-500/10 rounded px-3 py-2">{error}</div>
      )}

      {drafts.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No drafts to review.</p>
          <p className="text-sm text-neutral-600 mt-2">
            Import the model via the Dashboard or{" "}
            <Link href="/admin/model-import" className="text-blue-400 hover:underline">Model Import</Link>.
          </p>
        </div>
      ) : !selectedDraft ? (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold">Draft Snapshots</h2>
          {drafts.map((d) => (
            <button key={d.id} onClick={() => setSelectedDraft(d)}
              className="card hover:bg-neutral-900/50 transition-colors text-left w-full">
              <div className="flex items-center justify-between">
                <p className="font-semibold">{d.snapshot_id}</p>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  d.status === "DRAFT" ? "bg-yellow-500/10 text-yellow-400" :
                  d.status === "VALIDATED" ? "bg-blue-500/10 text-blue-400" :
                  "bg-green-500/10 text-green-400"
                }`}>{d.status}</span>
              </div>
              <p className="text-sm text-neutral-400 mt-0.5">Effective: {d.effective_date}</p>
            </button>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="card space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold">Review Snapshot</h2>
              <span className={`text-xs px-2 py-0.5 rounded ${
                selectedDraft.status === "DRAFT" ? "bg-yellow-500/10 text-yellow-400" :
                selectedDraft.status === "VALIDATED" ? "bg-blue-500/10 text-blue-400" :
                "bg-green-500/10 text-green-400"
              }`}>{selectedDraft.status}</span>
            </div>
            <div className="text-sm text-neutral-400 space-y-1">
              <p>Snapshot: {selectedDraft.snapshot_id}</p>
              <p>Effective: {selectedDraft.effective_date}</p>
            </div>

            <div className="flex gap-3 pt-3 border-t border-neutral-800">
              {selectedDraft.status === "DRAFT" && (
                <button onClick={() => handleTransition("VALIDATED")} className="btn-secondary">
                  <Check className="w-4 h-4 mr-1" /> Validate
                </button>
              )}
              {selectedDraft.status === "VALIDATED" && (
                <button onClick={() => handleTransition("APPROVED")} className="btn-secondary">
                  <Check className="w-4 h-4 mr-1" /> Approve
                </button>
              )}
              {selectedDraft.status === "APPROVED" && (
                <button onClick={() => handleTransition("PUBLISHED")} className="btn-primary">
                  <Check className="w-4 h-4 mr-1" /> Publish
                </button>
              )}
              <button onClick={() => { setSelectedDraft(null); }} className="btn-ghost">
                <X className="w-4 h-4 mr-1" /> Back
              </button>
            </div>
          </div>
          {actionMsg && (
            <div className="card border-green-500/30 bg-green-500/5">
              <p className="text-sm text-green-400">{actionMsg}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
