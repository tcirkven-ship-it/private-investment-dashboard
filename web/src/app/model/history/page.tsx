"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, ChevronRight } from "lucide-react";

interface Snapshot {
  id: string;
  effective_date: string;
  status: string;
  holdings: number;
  added: number;
  removed: number;
  turnover: number;
}

const MOCK_SNAPSHOTS: Snapshot[] = [
  { id: "2026-06-24T080500Z", effective_date: "2026-06-23", status: "PUBLISHED", holdings: 30, added: 5, removed: 3, turnover: 16.7 },
  { id: "2026-03-31T160000Z", effective_date: "2026-03-31", status: "PUBLISHED", holdings: 30, added: 8, removed: 6, turnover: 26.7 },
  { id: "2025-12-31T160000Z", effective_date: "2025-12-31", status: "SUPERSEDED", holdings: 30, added: 7, removed: 5, turnover: 23.3 },
  { id: "2025-09-30T160000Z", effective_date: "2025-09-30", status: "SUPERSEDED", holdings: 30, added: 6, removed: 4, turnover: 20.0 },
];

export default function ModelHistoryPage() {
  const [snapshots] = useState<Snapshot[]>(MOCK_SNAPSHOTS);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/model" className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
        <h1 className="text-xl font-semibold">Model History</h1>
      </div>

      {snapshots.length === 0 ? (
        <div className="card text-center py-12"><p className="text-neutral-500">No snapshots imported yet.</p></div>
      ) : (
        <div className="space-y-3">
          {snapshots.map((s) => (
            <Link key={s.id} href={`/model/${s.id}`} className="card hover:bg-neutral-900/50 transition-colors block">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold">Q{s.effective_date.slice(5, 7) === "03" ? "1" : s.effective_date.slice(5, 7) === "06" ? "2" : s.effective_date.slice(5, 7) === "09" ? "3" : "4"} {s.effective_date.slice(0, 4)}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                      s.status === "PUBLISHED" ? "bg-green-500/10 text-green-400" : "bg-neutral-800 text-neutral-400"
                    }`}>{s.status}</span>
                  </div>
                  <p className="text-sm text-neutral-500 mt-1">
                    {s.holdings} holdings · {s.added} added · {s.removed} removed · {s.turnover}% turnover
                  </p>
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
