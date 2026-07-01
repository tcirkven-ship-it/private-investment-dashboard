"use client";

import { useRouter } from "next/navigation";

export default function SnapshotSelector({
  history,
  currentId,
}: {
  history: Record<string, unknown>[];
  currentId: string | null;
}) {
  const router = useRouter();

  return (
    <div className="card py-2 px-4 flex items-center gap-2">
      <label className="text-sm text-neutral-500 shrink-0">Model:</label>
      <select
        className="bg-neutral-800 text-sm text-neutral-200 border border-neutral-700 rounded px-2 py-1 flex-1"
        value={currentId || ""}
        onChange={(e) => {
          const val = e.target.value;
          if (val) {
            router.push(`/model?snapshot=${val}`);
          } else {
            router.push("/model");
          }
        }}
      >
        <option value="">Current (latest)</option>
        {history.map((s) => {
          const ql = s.quarter_label ? String(s.quarter_label) : null;
          const ed = s.effective_date ? String(s.effective_date) : null;
          const label = ql ? `${ql} — ${ed}` : (ed || "Unknown");
          return (
            <option key={String(s.id)} value={String(s.id)}>
              {label}
            </option>
          );
        })}
      </select>
    </div>
  );
}
