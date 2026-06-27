import { createServerSupabase } from "@/lib/supabase";
import { deriveHoldings, totalNav } from "@/lib/holdings";
import type { Transaction } from "@/lib/holdings";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default async function PerformancePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createServerSupabase();

  const [txResult, spyResult, qqqResult] = await Promise.all([
    supabase
      .from("transactions")
      .select("event_type, event_date, gross_amount, commission, quantity, price, security:security_id(ticker)")
      .eq("portfolio_id", id as string)
      .is("corrected_by", null)
      .order("event_date", { ascending: true }),
    supabase
      .from("benchmark_observations")
      .select("observation_date, total_return_index")
      .eq("ticker", "SPY")
      .order("observation_date", { ascending: false })
      .limit(2),
    supabase
      .from("benchmark_observations")
      .select("observation_date, total_return_index")
      .eq("ticker", "QQQ")
      .order("observation_date", { ascending: false })
      .limit(2),
  ]);

  if (txResult.error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Performance</h1>
        </div>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">Error: {txResult.error.message}</p>
        </div>
      </div>
    );
  }

  const txs: Transaction[] = (txResult.data || []).map((t: any) => ({
    event_type: t.event_type, event_date: t.event_date,
    ticker: t.security?.ticker || "", quantity: t.quantity || 0,
    price: t.price || 0, gross_amount: t.gross_amount,
    commission: t.commission || 0, tax_amount: 0,
    corrected_by: undefined,
  }));

  const state = deriveHoldings(txs);
  const nav = totalNav(state);
  const totalDeposits = state.total_deposits;
  const totalReturn = totalDeposits > 0 ? ((nav / totalDeposits) - 1) * 100 : 0;

  // Benchmark returns
  const spyRet = spyResult.data && spyResult.data.length >= 2
    ? (Number(spyResult.data[0].total_return_index) / Number(spyResult.data[1].total_return_index) - 1) * 100
    : null;
  const qqqRet = qqqResult.data && qqqResult.data.length >= 2
    ? (Number(qqqResult.data[0].total_return_index) / Number(qqqResult.data[1].total_return_index) - 1) * 100
    : null;

  if (spyResult.error) console.error("SPY query error:", spyResult.error.message);
  if (qqqResult.error) console.error("QQQ query error:", qqqResult.error.message);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
        <h1 className="text-xl font-semibold">Performance</h1>
      </div>

      {/* Percentage metrics */}
      <div className="card">
        <h2 className="text-sm font-semibold mb-3">Returns</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <p className="metric-label">Simple Return</p>
            <p className={`text-lg font-mono font-semibold mt-0.5 ${totalReturn >= 0 ? "text-green-400" : "text-red-400"}`}>
              {totalReturn >= 0 ? "+" : ""}{totalReturn.toFixed(2)}%
            </p>
          </div>
          <div>
            <p className="metric-label">SPY (latest 2 obs)</p>
            <p className={`text-lg font-mono font-semibold mt-0.5 ${spyRet !== null && spyRet >= 0 ? "text-green-400" : "text-neutral-400"}`}>
              {spyRet !== null ? `${spyRet >= 0 ? "+" : ""}${spyRet.toFixed(2)}%` : "—"}
            </p>
          </div>
          <div>
            <p className="metric-label">QQQ (latest 2 obs)</p>
            <p className={`text-lg font-mono font-semibold mt-0.5 ${qqqRet !== null && qqqRet >= 0 ? "text-green-400" : "text-neutral-400"}`}>
              {qqqRet !== null ? `${qqqRet >= 0 ? "+" : ""}${qqqRet.toFixed(2)}%` : "—"}
            </p>
          </div>
        </div>
        <p className="text-xs text-neutral-600 mt-2">Simple return = (NAV / total deposits) − 1. TWR and XIRR require daily valuation history.</p>
      </div>

      {/* Currency metrics */}
      <div className="card">
        <h2 className="text-sm font-semibold mb-3">Account</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="metric-label">NAV</p>
            <p className="text-lg font-mono font-semibold mt-0.5">${nav.toLocaleString()}</p>
          </div>
          <div>
            <p className="metric-label">Deposits</p>
            <p className="text-lg font-mono font-semibold mt-0.5">${totalDeposits.toLocaleString()}</p>
          </div>
          <div>
            <p className="metric-label">Realized P/L</p>
            <p className={`text-lg font-mono font-semibold mt-0.5 ${state.total_realized_pl >= 0 ? "text-green-400" : "text-red-400"}`}>
              ${state.total_realized_pl.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="metric-label">Dividends</p>
            <p className="text-lg font-mono font-semibold mt-0.5 text-blue-400">${state.total_dividends.toFixed(2)}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
