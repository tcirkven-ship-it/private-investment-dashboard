"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { importM1B2Model } from "@/lib/actions";

export default function GenerateModelButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setResult(null);
    const res = await importM1B2Model();
    setResult(res.error || res.message || "Done");
    if (!res.error) {
      setTimeout(() => router.refresh(), 500);
    }
    setLoading(false);
  }

  return (
    <div>
      <button onClick={handleGenerate} disabled={loading} className="btn-primary text-sm">
        {loading ? "Generating..." : "Generate / Refresh Quarterly Top 30"}
      </button>
      {result && (
        <p className={`text-xs mt-2 ${result.startsWith("Error") ? "text-red-400" : "text-green-400"}`}>
          {result}
        </p>
      )}
    </div>
  );
}
