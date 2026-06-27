import { createServerSupabase } from "@/lib/supabase";
import { deriveHoldings, totalNav } from "@/lib/holdings";
import Link from "next/link";
import { ArrowLeft, Download } from "lucide-react";

export default async function PerformancePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createServerSupabase();

  const { data: transactions, error } = await supabase
    .from("transactions")
    .select("event_type, event_date, gross_amount, commission, quantity, price, security:security_id(ticker)")
    .eq("portfolio_id", id)
    .is("corrected_by", null)
    .order("event_date", { ascending: true });

  // Get benchmark data
  const { data: spyData } = await supabase
    .from("benchmark_observations")
    .select("observation_date, total_return_index")
    .eq("ticker", "SPY")
    .order("observation_date", { ascending: false })
    .limit(2);

  const { data: qqqData } = await supabase
    .from("benchmark_observations")
    .select("observation_date, total_return_index")
    .eq("ticker", "QQQ")
    .order("observation_date", { ascending: false })
    .limit(2);

  // Calculate SPY return from total return index
  const spyRet = spyData && spyData.length >= 2
    ? (spyData[0].total_return_index / spyData[1].total_return_index - 1) * 100
    : null;
  const qqqRet = qqqData && qqqData.length >= 2
    ? (qqqData[0].total_return_index / qqqData[1].total_return_index - 1) * 100
    : null;

  // Derive current state from transactions
  const txs = (transactions || []).map((t: any) => ({
    event_type: t.event_type, event_date: t.event_date,
    ticker: t.security?.ticker || "", quantity: t.quantity || 0,
    price: t.price || 0, gross_amount: t.gross_amount,
    commission: t.commission || 0, tax_amount: 0,
    corrected_by: undefined,
  }));
  const state = deriveHoldings(txs);
  const nav = totalNav(state);
  const totalReturn = state.total_deposits > 0 ? (nav / state.total_deposits - 1) * 100 : 0;

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Performance</h1>
        </div>
        <div className="card border-red-500/30 bg-red-500/5"><p className="text-sm text-red-400">Error: {error.message}</p></div>
      </div>
    );
  }

  const periods = [
    { label: "Total Return", value: totalReturn },
    { label: "Deposits", value: state.total_deposits },
    { label: "Realized P/L", value: state.total_realized_pl },
    { label: "Dividends", value: state.total_dividends },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Performance</h1>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {periods.map((p) => (
          <div key={p.label} className="card">
            <p className="metric-label">{p.label}</p>
            <p className={`metric-value mt-1 ${p.value >= 0 ? "text-green-400" : "text-red-400"}`}>
              {typeof p.value === "number" && p.label !== "Deposits"
                ? `${p.value >= 0 ? "+" : ""}${p.value.toFixed(2)}%`
                : `$${p.value.toLocaleString()}`}
            </p>
          </div>
        ))}
      </div>

      <div className="card">
        <h2 className="text-sm font-semibold mb-4">Benchmark Comparison</h2>
        <div className="grid grid-cols-3 gap-6">
          <div>
            <p className="metric-label">Portfolio</p>
            <p className={`text-lg font-mono font-semibold mt-0.5 ${totalReturn >= 0 ? "text-green-400" : "text-red-400"}`}>
              {totalReturn >= 0 ? "+" : ""}{totalReturn.toFixed(2)}%
            </p>
          </div>
          <div>
            <p className="metric-label">SPY</p>
            <p className={`text-lg font-mono font-semibold mt-0.5 ${spyRet && spyRet >= 0 ? "text-green-400" : "text-neutral-400"}`}>
              {spyRet !== null ? `${spyRet >= 0 ? "+" : ""}${spyRet.toFixed(2)}%` : "—"}
            </p>
          </div>
          <div>
            <p className="metric-label">QQQ</p>
            <p className={`text-lg font-mono font-semibold mt-0.5 ${qqqRet && qqqRet >= 0 ? "text-green-400" : "text-neutral-400"}`}>
              {qqqRet !== null ? `${qqqRet >= 0 ? "+" : ""}${qqqRet.toFixed(2)}%` : "—"}
            </p>
          </div>
        </div>
      </div>

      <div className="card">
        <p className="text-sm text-neutral-500">
          Calculations use the production holdings engine. TWR and XIRR require additional
          daily valuation data. Benchmark returns are from the most recent available price
          observations.
        </p>
      </div>
    </div>
  );
}
