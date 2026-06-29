import { loadHoldings, loadBenchmarkReturns } from "@/lib/route-loaders";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default async function PerformancePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let error: string | null = null;
  let nav = 0;
  let totalDeposits = 0;
  let totalRealizedPL = 0;
  let totalDividends = 0;
  let spyReturn: number | null = null;
  let qqqReturn: number | null = null;
  let hasTransactions = false;
  let hasMissingPrices = false;
  let totalUnrealized = 0;
  let somePrices = false;

  try {
    const [holdingsResult, benchResult] = await Promise.all([
      loadHoldings(id as string),
      loadBenchmarkReturns(),
    ]);
    nav = holdingsResult.nav;
    totalDeposits = holdingsResult.state.total_deposits;
    totalRealizedPL = holdingsResult.state.total_realized_pl;
    totalDividends = holdingsResult.state.total_dividends;
    spyReturn = benchResult.spyReturn;
    qqqReturn = benchResult.qqqReturn;
    hasTransactions = holdingsResult.transactions.length > 0;
    const distinctTickers = holdingsResult.state.holdings.size;
    hasMissingPrices = holdingsResult.priceCount < distinctTickers;
    const h = [...holdingsResult.state.holdings.values()];
    totalUnrealized = h.reduce((s, x) => s + (x.unrealized_pl || 0), 0);
    somePrices = h.some((x) => x.market_value !== undefined && x.market_value !== null);
  } catch (e: unknown) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Performance</h1>
        </div>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!hasTransactions) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Performance</h1>
        </div>
        <div className="card text-center py-12">
          <p className="text-neutral-500">Performance unavailable until enough transaction and price data exists.</p>
          <p className="text-sm text-neutral-600 mt-2">Add transactions (deposits, buys) and price observations to see performance metrics.</p>
        </div>
      </div>
    );
  }

  if (hasMissingPrices && nav > 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Performance</h1>
        </div>
        <div className="card text-center py-12">
          <p className="text-neutral-500">Performance unavailable until current prices are available for all open holdings.</p>
        </div>
      </div>
    );
  }

  const totalReturn = totalDeposits > 0 ? ((nav / totalDeposits) - 1) * 100 : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
        <h1 className="text-xl font-semibold">Performance</h1>
      </div>

      <div className="card">
        <h2 className="text-sm font-semibold mb-3">Returns</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <p className="metric-label">Simple Return</p>
            <p className={`text-lg font-mono font-semibold mt-0.5 ${totalReturn !== null && totalReturn >= 0 ? "text-green-400" : totalReturn !== null ? "text-red-400" : "text-neutral-400"}`}>
              {totalReturn !== null ? `${totalReturn >= 0 ? "+" : ""}${totalReturn.toFixed(2)}%` : "—"}
            </p>
          </div>
          <div>
            <p className="metric-label">SPY</p>
            <p className={`text-lg font-mono font-semibold mt-0.5 ${spyReturn !== null && spyReturn >= 0 ? "text-green-400" : "text-neutral-400"}`}>
              {spyReturn !== null ? `${spyReturn >= 0 ? "+" : ""}${spyReturn.toFixed(2)}%` : "—"}
            </p>
          </div>
          <div>
            <p className="metric-label">QQQ</p>
            <p className={`text-lg font-mono font-semibold mt-0.5 ${qqqReturn !== null && qqqReturn >= 0 ? "text-green-400" : "text-neutral-400"}`}>
              {qqqReturn !== null ? `${qqqReturn >= 0 ? "+" : ""}${qqqReturn.toFixed(2)}%` : "—"}
            </p>
          </div>
        </div>
        <p className="text-xs text-neutral-600 mt-2">Simple return = (NAV / total deposits) - 1. Weekly, monthly, QTD, YTD, and since-inception returns require daily valuation history.</p>
      </div>

      <div className="card">
        <h2 className="text-sm font-semibold mb-3">Account</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div><p className="metric-label">NAV</p><p className="text-lg font-mono font-semibold mt-0.5">${nav.toLocaleString()}</p></div>
          <div><p className="metric-label">Deposits</p><p className="text-lg font-mono font-semibold mt-0.5">${totalDeposits.toLocaleString()}</p></div>
          <div><p className="metric-label">Unrealized P/L</p><p className={`text-lg font-mono font-semibold mt-0.5 ${totalUnrealized >= 0 ? "text-green-400" : "text-red-400"}`}>{somePrices ? `$${totalUnrealized.toFixed(2)}` : "—"}</p></div>
          <div><p className="metric-label">Realized P/L</p><p className={`text-lg font-mono font-semibold mt-0.5 ${totalRealizedPL >= 0 ? "text-green-400" : "text-red-400"}`}>${totalRealizedPL.toFixed(2)}</p></div>
        </div>
      </div>
    </div>
  );
}
