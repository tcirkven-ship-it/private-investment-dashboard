"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { refreshPortfolioPrices } from "@/lib/actions";

export default function RefreshPricesButton({ portfolioId }: { portfolioId: string }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const router = useRouter();

  async function handleClick() {
    setLoading(true);
    setResult(null);
    const res = await refreshPortfolioPrices(portfolioId);
    setLoading(false);
    if (res.error) {
      setResult(res.error);
    } else if (res.results) {
      const entries = Object.entries(res.results) as [string, { ok: boolean }][];
      const okTickers = entries.filter(([, r]) => r.ok).map(([t]) => t);
      const failedTickers = entries.filter(([, r]) => !r.ok).map(([t]) => t);
      let msg = `${okTickers.length} price${okTickers.length !== 1 ? "s" : ""} refreshed.`;
      if (failedTickers.length > 0) {
        msg += ` Failed: ${failedTickers.join(", ")}.`;
      }
      setResult(msg);
    } else {
      setResult(res.message || "Done");
    }
    router.refresh();
  }

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={loading}
        className="btn-primary text-sm"
      >
        <RefreshCw className={`w-4 h-4 mr-1.5 inline ${loading ? "animate-spin" : ""}`} />
        Refresh Current Prices
      </button>
      {result && (
        <p className="text-xs text-neutral-400 mt-1">{result}</p>
      )}
    </div>
  );
}
