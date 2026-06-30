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
      const okCount = Object.values(res.results).filter((r) => r.ok).length;
      const failedCount = Object.values(res.results).length - okCount;
      setResult(`${okCount} price${okCount !== 1 ? "s" : ""} refreshed. ${failedCount} failed.`);
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
