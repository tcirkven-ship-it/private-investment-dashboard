"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { recordValuationSnapshot } from "@/lib/actions";

export default function RecordSnapshotButton({ portfolioId }: { portfolioId: string }) {
  const router = useRouter();
  const [recording, setRecording] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function handleRecord() {
    setRecording(true);
    setMsg(null);
    const result = await recordValuationSnapshot(portfolioId);
    if (result.error) {
      setMsg(result.error);
    } else {
      setMsg(`Snapshot recorded: NAV $${result.nav?.toLocaleString("en-US", { maximumFractionDigits: 2 })}, date ${result.date}`);
      router.refresh();
    }
    setRecording(false);
  }

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <button onClick={handleRecord} disabled={recording} className="btn btn-secondary">
        {recording ? "Recording..." : "Record Valuation Snapshot"}
      </button>
      {msg && (
        <p className={`text-xs ${msg.startsWith("Cannot") ? "text-amber-400" : "text-green-400"}`}>{msg}</p>
      )}
    </div>
  );
}
