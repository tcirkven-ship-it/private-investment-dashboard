"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, ChevronRight } from "lucide-react";

export default function ModelHistoryPage() {
  const [snapshots] = useState<any[]>([]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/model" className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
        <h1 className="text-xl font-semibold">Model History</h1>
      </div>

      {snapshots.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No snapshots imported yet.</p>
          <p className="text-sm text-neutral-600 mt-2">Import a model snapshot on the Settings page.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {snapshots.map((s: any) => (
            <Link key={s.id} href={`/model/${s.snapshot_id}`} className="card hover:bg-neutral-900/50 transition-colors block">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold">{s.effective_date}</h3>
                    <span className="text-xs px-2 py-0.5 rounded font-medium bg-neutral-800 text-neutral-400">{s.status}</span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-neutral-500" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
