import { createServerSupabase } from "@/lib/supabase";
import { deriveHoldings, totalNav } from "@/lib/holdings";
import Link from "next/link";
import { ArrowLeft, Download } from "lucide-react";

export default async function HoldingsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createServerSupabase();

  const { data: transactions, error: txError } = await supabase
    .from("transactions")
    .select("id, event_type, event_date, quantity, price, gross_amount, commission, tax_amount, security:security_id(ticker)")
    .eq("portfolio_id", id)
    .is("corrected_by", null)
    .order("event_date", { ascending: true });

  const { data: prices } = await supabase
    .from("price_observations")
    .select("security:security_id(ticker), adj_close, observation_date")
    .order("observation_date", { ascending: false })
    .limit(1000);

  // Build price map (latest price per ticker)
  const priceMap = new Map<string, number>();
  // Derive holdings from transactions
  const txs = (transactions || []).map((t: any) => ({
    event_type: t.event_type,
    event_date: t.event_date,
    ticker: t.security?.ticker || "",
    quantity: t.quantity || 0,
    price: t.price || 0,
    gross_amount: t.gross_amount,
    commission: t.commission || 0,
    tax_amount: t.tax_amount || 0,
    corrected_by: undefined,
  }));

  const state = deriveHoldings(txs, priceMap);
  const nav = totalNav(state);

  const csvLine = [
    "Ticker,Quantity,Avg Cost,Market Value,Unrealized,Weight",
    ...[...state.holdings.values()].map(h =>
      `${h.ticker},${h.quantity},${h.average_cost.toFixed(2)},${(h.market_value || 0).toFixed(2)},${(h.unrealized_pl || 0).toFixed(2)},${h.market_value ? (h.market_value / nav * 100).toFixed(1) : 0}%`
    ),
  ].join("\n");

  if (txError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Holdings</h1>
        </div>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">Error: {txError.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <div>
            <h1 className="text-xl font-semibold">Holdings</h1>
            <p className="text-sm text-neutral-500">NAV: ${nav.toLocaleString()}</p>
          </div>
        </div>
        <a href={`data:text/csv;charset=utf-8,${encodeURIComponent(csvLine)}`}
           download="holdings.csv" className="btn-secondary"><Download className="w-4 h-4 mr-1" />CSV</a>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card"><p className="metric-label">Cash</p><p className="metric-value mt-1">${state.cash.toLocaleString()}</p></div>
        <div className="card"><p className="metric-label">Invested</p><p className="metric-value mt-1">${(nav - state.cash).toLocaleString()}</p></div>
        <div className="card"><p className="metric-label">Realized</p><p className={`metric-value mt-1 ${state.total_realized_pl >= 0 ? "text-green-400" : "text-red-400"}`}>${state.total_realized_pl.toFixed(0)}</p></div>
        <div className="card"><p className="metric-label">Dividends</p><p className="metric-value mt-1 text-blue-400">${state.total_dividends.toFixed(0)}</p></div>
      </div>

      {state.holdings.size === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No holdings.</p>
          <p className="text-sm text-neutral-600 mt-2">Add transactions on the Transactions page.</p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="table-header">Ticker</th>
                <th className="table-header text-right">Qty</th>
                <th className="table-header text-right">Avg Cost</th>
                <th className="table-header text-right">Mkt Value</th>
                <th className="table-header text-right">Unrealized</th>
                <th className="table-header text-right">Weight</th>
              </tr>
            </thead>
            <tbody>
              {[...state.holdings.values()].sort((a, b) => (b.market_value || 0) - (a.market_value || 0)).map((h) => (
                <tr key={h.ticker} className="border-b border-neutral-800/50">
                  <td className="table-cell-text font-semibold">{h.ticker}</td>
                  <td className="table-cell text-right">{h.quantity.toFixed(3)}</td>
                  <td className="table-cell text-right">${h.average_cost.toFixed(2)}</td>
                  <td className="table-cell text-right">${(h.market_value || 0).toLocaleString()}</td>
                  <td className={`table-cell text-right ${(h.unrealized_pl || 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                    ${(h.unrealized_pl || 0).toFixed(2)}
                  </td>
                  <td className="table-cell text-right">{h.market_value ? (h.market_value / nav * 100).toFixed(1) : 0}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
