"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { importM1B2Model } from "@/lib/actions";

export default function GenerateModelButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  async function handleClick() {
    setLoading(true);
    setResult(null);
    const res = await importM1B2Model();
    if (res.error) {
      setResult(res.error);
    } else {
      setResult(res.message || "Done");
      router.refresh();
    }
    setLoading(false);
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={handleClick}
        disabled={loading}
        className="btn-primary"
      >
        <RefreshCw className={`w-4 h-4 mr-1.5 ${loading ? "animate-spin" : ""}`} />
        {loading ? "Generating..." : "Generate / Refresh"}
      </button>
      {result && (
        <span className={`text-xs ${result.includes("success") && !result.startsWith("Error") ? "text-green-400" : "text-red-400"}`}>
          {result}
        </span>
      )}
    </div>
  );
}
