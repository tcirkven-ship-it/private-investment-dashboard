import { loadHoldings, loadBenchmarkReturns } from "@/lib/route-loaders";
import { createServerSupabase } from "@/lib/supabase";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import RecordSnapshotButton from "./RecordSnapshotButton";

function getPeriodStart(days: number, monthStart: boolean, quarterStart: boolean, yearStart: boolean): string | null {
  const now = new Date();
  if (yearStart) return `${now.getFullYear()}-01-01`;
  if (quarterStart) { const q = Math.floor(now.getMonth() / 3) * 3; return `${now.getFullYear()}-${String(q + 1).padStart(2, "0")}-01`; }
  if (monthStart) return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
  const d = new Date(now.getTime() - days * 86400000);
  return d.toISOString().split("T")[0];
}

function calcPeriodReturn(currentNav: number, startSnap: { total_value: number } | null): number | null {
  if (!startSnap || startSnap.total_value <= 0) return null;
  return (currentNav / startSnap.total_value - 1) * 100;
}

export default async function PerformancePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let error: string | null = null;
  let nav = 0;
  let totalDeposits = 0;
  let totalRealizedPL = 0;
  let totalDividends = 0;
  let totalUnrealized = 0;
  let spyReturn: number | null = null;
  let qqqReturn: number | null = null;
  let hasTransactions = false;
  let hasMissingPrices = false;
  let somePrices = false;
  let sinceInceptionReturn: number | null = null;

  // Period returns
  let weekly: number | null = null;
  let monthly: number | null = null;
  let qtd: number | null = null;
  let ytd: number | null = null;
  let weeklyMsg: string | null = null;
  let monthlyMsg: string | null = null;
  let qtdMsg: string | null = null;
  let ytdMsg: string | null = null;
  let snapshots: Array<{ id: string; valuation_date: string; total_value: number; cash_balance: number }> = [];

  try {
    const supabase = await createServerSupabase();
    const [holdingsResult, benchResult, snapResult] = await Promise.all([
      loadHoldings(id as string),
      loadBenchmarkReturns(),
      supabase.from("portfolio_valuations")
        .select("id, valuation_date, total_value, cash_balance")
        .eq("portfolio_id", id as string)
        .order("valuation_date", { ascending: false })
        .limit(20),
    ]);

    nav = holdingsResult.nav;
    totalDeposits = holdingsResult.state.total_deposits;
    totalRealizedPL = holdingsResult.state.total_realized_pl;
    totalDividends = holdingsResult.state.total_dividends;
    spyReturn = benchResult.spyReturn;
    qqqReturn = benchResult.qqqReturn;
    hasTransactions = holdingsResult.transactions.length > 0;
    const holdings = [...holdingsResult.state.holdings.values()];
    const distinctTickers = holdingsResult.state.holdings.size;
    hasMissingPrices = holdingsResult.priceCount < distinctTickers;
    totalUnrealized = holdings.reduce((s, x) => s + (x.unrealized_pl || 0), 0);
    somePrices = holdings.some((x) => x.market_value !== undefined && x.market_value !== null);
    snapshots = (snapResult.data || []) as typeof snapshots;

    if (nav > 0 && totalDeposits > 0 && !hasMissingPrices) {
      sinceInceptionReturn = (nav / totalDeposits - 1) * 100;
    }

    if (nav > 0 && !hasMissingPrices) {
      // Weekly: find snapshot at or before 7 days ago
      const wStart = getPeriodStart(7, false, false, false);
      const mStart = getPeriodStart(0, true, false, false);
      const qStart = getPeriodStart(0, false, true, false);
      const yStart = getPeriodStart(0, false, false, true);

      const findBefore = (targetDate: string | null) => {
        if (!targetDate) return null;
        return snapshots.find((s) => s.valuation_date <= targetDate) || null;
      };

      const wSnap = findBefore(wStart);
      const mSnap = findBefore(mStart);
      const qSnap = findBefore(qStart);
      const ySnap = findBefore(yStart);

      weekly = calcPeriodReturn(nav, wSnap);
      monthly = calcPeriodReturn(nav, mSnap);
      qtd = calcPeriodReturn(nav, qSnap);
      ytd = calcPeriodReturn(nav, ySnap);

      if (weekly === null) weeklyMsg = "No valuation snapshot from at least 7 days ago.";
      else weeklyMsg = "Simple return, not cash-flow adjusted";
      if (monthly === null) monthlyMsg = "No valuation snapshot from month start.";
      else monthlyMsg = "Simple return, not cash-flow adjusted";
      if (qtd === null) qtdMsg = "No valuation snapshot from quarter start.";
      else qtdMsg = "Simple return, not cash-flow adjusted";
      if (ytd === null) ytdMsg = "No valuation snapshot from year start.";
      else ytdMsg = "Simple return, not cash-flow adjusted";
    }
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
        <div className="card border-red-500/30 bg-red-500/5"><p className="text-sm text-red-400">{error}</p></div>
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
          <p className="text-neutral-500">Performance unavailable until transactions exist.</p>
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

  const displayReturn = (val: number | null, msg?: string | null) => {
    if (val === null) return <p className="text-neutral-500 text-xs mt-0.5">{msg || "Unavailable"}</p>;
    return (
      <>
        <p className={`text-lg font-mono font-semibold tabular-nums mt-0.5 ${val >= 0 ? "text-green-400" : "text-red-400"}`}>
          {val >= 0 ? "+" : ""}{val.toFixed(2)}%
        </p>
        {msg && <p className="text-neutral-600 text-xs">{msg}</p>}
      </>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Performance</h1>
        </div>
        <RecordSnapshotButton portfolioId={id as string} />
      </div>

      <div className="card">
        <h2 className="text-sm font-semibold mb-3">Period Returns</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div><p className="metric-label">Weekly</p>{displayReturn(weekly, weeklyMsg)}</div>
          <div><p className="metric-label">Monthly</p>{displayReturn(monthly, monthlyMsg)}</div>
          <div><p className="metric-label">QTD</p>{displayReturn(qtd, qtdMsg)}</div>
          <div><p className="metric-label">YTD</p>{displayReturn(ytd, ytdMsg)}</div>
          <div><p className="metric-label">Since Inception</p>{displayReturn(sinceInceptionReturn, sinceInceptionReturn !== null ? "Simple return = NAV / deposits" : null)}</div>
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-neutral-800">
          <div><p className="metric-label">SPY</p><p className={`text-lg font-mono font-semibold mt-0.5 ${spyReturn !== null && spyReturn >= 0 ? "text-green-400" : "text-neutral-400"}`}>{spyReturn !== null ? `${spyReturn >= 0 ? "+" : ""}${spyReturn.toFixed(2)}%` : "—"}</p></div>
          <div><p className="metric-label">QQQ</p><p className={`text-lg font-mono font-semibold mt-0.5 ${qqqReturn !== null && qqqReturn >= 0 ? "text-green-400" : "text-neutral-400"}`}>{qqqReturn !== null ? `${qqqReturn >= 0 ? "+" : ""}${qqqReturn.toFixed(2)}%` : "—"}</p></div>
        </div>
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

      <div className="card">
        <h2 className="text-sm font-semibold mb-3">Valuation History</h2>
        {snapshots.length === 0 ? (
          <p className="text-sm text-neutral-500">No valuation snapshots recorded yet. Use the Record button above to create your first snapshot.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-neutral-800"><th className="table-header">Date</th><th className="table-header text-right">NAV</th><th className="table-header text-right">Cash</th></tr></thead>
              <tbody>
                {snapshots.map((s) => (
                  <tr key={s.id} className="border-b border-neutral-800/50">
                    <td className="table-cell-text">{s.valuation_date}</td>
                    <td className="table-cell text-right">${s.total_value.toLocaleString()}</td>
                    <td className="table-cell text-right">${s.cash_balance.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
