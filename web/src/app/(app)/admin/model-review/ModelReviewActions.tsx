"use client";

import { useState } from "react";
import { Check, X } from "lucide-react";
import { createBrowserClient } from "@supabase/ssr";

interface Snapshot {
  id: string;
  snapshot_id: string;
  status: string;
  effective_date: string;
}

export default function ModelReviewActions({ snapshots }: { snapshots: Snapshot[] }) {
  const [selected, setSelected] = useState<Snapshot | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function transition(id: string, status: string) {
    setErr(null);
    setMsg(null);
    const supabase = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    );
    const { error } = await supabase
      .from("model_snapshots")
      .update({ status, published_at: status === "PUBLISHED" ? new Date().toISOString() : undefined })
      .eq("id", id);
    if (error) setErr(error.message);
    else { setMsg(`${status}: done`); setSelected(null); }
  }

  return (
    <div className="space-y-3">
      {err && <div className="text-sm text-red-400">{err}</div>}
      {msg && <div className="card border-green-500/30 bg-green-500/5"><p className="text-sm text-green-400">{msg}</p></div>}

      {!selected ? (
        snapshots.map((s) => (
          <button key={s.id} onClick={() => setSelected(s)}
            className="card hover:bg-neutral-900/50 transition-colors text-left w-full">
            <div className="flex items-center justify-between">
              <p className="font-semibold">{s.snapshot_id}</p>
              <span className="text-xs px-2 py-0.5 rounded bg-yellow-500/10 text-yellow-400">{s.status}</span>
            </div>
            <p className="text-sm text-neutral-400 mt-0.5">Effective: {s.effective_date}</p>
          </button>
        ))
      ) : (
        <div className="card space-y-3">
          <p className="text-sm text-neutral-400">Snapshot: {selected.snapshot_id} (Status: {selected.status})</p>
          <div className="flex gap-3">
            {selected.status === "DRAFT" && <button onClick={() => transition(selected.id, "VALIDATED")} className="btn-secondary"><Check className="w-4 h-4 mr-1" /> Validate</button>}
            {selected.status === "VALIDATED" && <button onClick={() => transition(selected.id, "APPROVED")} className="btn-secondary"><Check className="w-4 h-4 mr-1" /> Approve</button>}
            {selected.status === "APPROVED" && <button onClick={() => transition(selected.id, "PUBLISHED")} className="btn-primary"><Check className="w-4 h-4 mr-1" /> Publish</button>}
            <button onClick={() => setSelected(null)} className="btn-ghost"><X className="w-4 h-4 mr-1" /> Back</button>
          </div>
        </div>
      )}
    </div>
  );
}
