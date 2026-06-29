"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { saveOwnerDecision } from "./actions";

const STATUS_OPTIONS = ["planned", "executed", "skipped", "watch", "not_now", ""] as const;
const STATUS_LABELS: Record<string, string> = {
  planned: "Planned",
  executed: "Executed",
  skipped: "Skipped",
  watch: "Watch",
  not_now: "Not now",
  "": "Undecided",
};

const STATUS_STYLE: Record<string, string> = {
  planned: "text-blue-400",
  executed: "text-green-400",
  skipped: "text-neutral-500 line-through",
  watch: "text-amber-400",
  not_now: "text-neutral-400",
  "": "text-neutral-500",
};

export default function DecisionCell({
  portfolioId,
  snapshotId,
  securityId,
  ticker,
  recommendation,
  initialStatus,
  initialNote,
}: {
  portfolioId: string;
  snapshotId: string;
  securityId: string;
  ticker: string;
  recommendation: string;
  initialStatus: string;
  initialNote: string;
}) {
  const router = useRouter();
  const [status, setStatus] = useState(initialStatus);
  const [note, setNote] = useState(initialNote);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    const result = await saveOwnerDecision(portfolioId, snapshotId, securityId, ticker, recommendation, status, note);
    setSaving(false);
    if (!result.error) {
      setSaved(true);
      router.refresh();
      setTimeout(() => setSaved(false), 2000);
    }
  };

  const dirty = status !== initialStatus || note !== initialNote;

  return (
    <div className="flex items-center gap-1.5">
      <select
        value={status}
        onChange={(e) => { setStatus(e.target.value); setSaved(false); }}
        className={`bg-neutral-800 border border-neutral-700 rounded px-1.5 py-0.5 text-xs w-24 ${STATUS_STYLE[status] || ""}`}
      >
        {STATUS_OPTIONS.map((opt) => (
          <option key={opt} value={opt} className="text-neutral-300 bg-neutral-800">
            {STATUS_LABELS[opt]}
          </option>
        ))}
      </select>
      <input
        type="text"
        value={note}
        onChange={(e) => { setNote(e.target.value); setSaved(false); }}
        placeholder="Note"
        className="bg-neutral-800 border border-neutral-700 rounded px-1.5 py-0.5 text-xs w-20 text-neutral-300 placeholder-neutral-600"
      />
      {dirty && (
        <button
          onClick={handleSave}
          disabled={saving}
          className="text-xs px-2 py-0.5 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white whitespace-nowrap"
        >
          {saving ? "..." : "Save"}
        </button>
      )}
      {saved && !dirty && (
        <span className="text-xs text-green-400 whitespace-nowrap">Saved</span>
      )}
    </div>
  );
}
