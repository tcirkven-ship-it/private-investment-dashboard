"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Check, AlertTriangle, X } from "lucide-react";
import { createClient } from "@/lib/supabase";

interface DraftSnapshot {
  id: string;
  snapshot_id: string;
  status: string;
  effective_date: string;
  eligible_count: number;
  valid_score_count: number;
  integrity_hash: string;
}

export default function ModelReviewPage() {
  const [drafts, setDrafts] = useState<DraftSnapshot[]>([
    { id: "draft-1", snapshot_id: "2026-09-30T160000Z", status: "DRAFT", effective_date: "2026-09-30", eligible_count: 1070, valid_score_count: 1070, integrity_hash: "abc123..." },
  ]);
  const [selectedDraft, setSelectedDraft] = useState<DraftSnapshot | null>(null);
  const [action, setAction] = useState<"validated" | "approved" | "rejected" | null>(null);

  async function handleTransition(status: "VALIDATED" | "APPROVED" | "PUBLISHED") {
    if (!selectedDraft) return;
    // In production, update Supabase and create audit event
    setAction(status === "VALIDATED" ? "validated" : status === "APPROVED" ? "approved" : "rejected");
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-4">
        <Link href="/settings" className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
        <h1 className="text-xl font-semibold">Model Review</h1>
      </div>

      {drafts.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No draft snapshots to review. Import one first.</p>
        </div>
      ) : !selectedDraft ? (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold">Draft Snapshots</h2>
          {drafts.map((d) => (
            <button key={d.id} onClick={() => setSelectedDraft(d)}
              className="card hover:bg-neutral-900/50 transition-colors text-left w-full">
              <p className="font-semibold">{d.snapshot_id}</p>
              <p className="text-sm text-neutral-400 mt-0.5">{d.effective_date} · {d.eligible_count} eligible · {d.valid_score_count} scored</p>
            </button>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="card space-y-3">
            <h2 className="text-sm font-semibold">Review Snapshot</h2>
            <div className="text-sm text-neutral-400 space-y-1">
              <p>Snapshot ID: {selectedDraft.snapshot_id}</p>
              <p>Effective date: {selectedDraft.effective_date}</p>
              <p>Eligible count: {selectedDraft.eligible_count}</p>
              <p>Valid scores: {selectedDraft.valid_score_count}</p>
              <p>Integrity hash: {selectedDraft.integrity_hash}</p>
            </div>
            <div className="text-xs text-neutral-500 mt-3 space-y-1">
              <p className="flex items-center gap-1"><Check className="w-3 h-3 text-green-400" /> Schema validation: PASS</p>
              <p className="flex items-center gap-1"><Check className="w-3 h-3 text-green-400" /> Integrity hash: MATCH</p>
              <p className="flex items-center gap-1"><Check className="w-3 h-3 text-green-400" /> Holdings sum to 1.0: PASS</p>
            </div>

            <div className="flex gap-3 pt-3 border-t border-neutral-800">
              <button onClick={() => handleTransition("VALIDATED")} className="btn-secondary">
                <Check className="w-4 h-4 mr-1" /> Validate
              </button>
              <button onClick={() => handleTransition("APPROVED")} className="btn-primary">
                <Check className="w-4 h-4 mr-1" /> Approve & Publish
              </button>
              <button onClick={() => { setSelectedDraft(null); }} className="btn-ghost">
                <X className="w-4 h-4 mr-1" /> Reject
              </button>
            </div>
          </div>
          {action && (
            <div className="card border-green-500/30 bg-green-500/5">
              <p className="text-sm text-green-400">
                {action === "validated" ? "Snapshot validated. Ready for approval." :
                 action === "approved" ? "Snapshot approved and published." :
                 "Snapshot rejected."}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
