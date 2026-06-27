import { createServerSupabase } from "@/lib/supabase";
import { deriveHoldings, totalNav } from "@/lib/holdings";
import type { Transaction } from "@/lib/holdings";
import type { PriceRow } from "@/lib/types";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default async function HoldingsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createServerSupabase();

  const [txResult, priceResult] = await Promise.all([
    supabase
      .from("transactions")
      .select("id, event_type, event_date, quantity, price, gross_amount, commission, tax_amount, security:security_id(ticker)")
      .eq("portfolio_id", id as string)
      .is("corrected_by", null)
      .order("event_date", { ascending: true }),
    supabase
      .from("price_observations")
      .select("close, observation_date, security:security_id(ticker)")
      .order("observation_date", { ascending: false })
      .limit(2000),
  ]);

  if (txResult.error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Holdings</h1>
        </div>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">Error loading transactions: {txResult.error.message}</p>
        </div>
      </div>
    );
  }

  // Build price map from observations (latest price per ticker)
  const priceMap = new Map<string, number>();
  if (priceResult.data) {
    for (const row of priceResult.data as any[]) {
      const ticker: string | undefined = row.security?.ticker;
      if (ticker && !priceMap.has(ticker) && row.close) {
        priceMap.set(ticker, Number(row.close));
      }
    }
  }

  // Map DB rows to Transaction type
  const txs: Transaction[] = (txResult.data || []).map((t: any) => ({
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <div>
            <h1 className="text-xl font-semibold">Holdings</h1>
            <p className="text-sm text-neutral-500">
              NAV: ${nav.toLocaleString()}
              {priceMap.size === 0 ? " · prices unavailable" : ""}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card"><p className="metric-label">Cash</p><p className="metric-value mt-1">${state.cash.toLocaleString()}</p></div>
        <div className="card"><p className="metric-label">Invested</p><p className="metric-value mt-1">${(nav - state.cash).toLocaleString()}</p></div>
        <div className="card"><p className="metric-label">Realized P/L</p><p className={`metric-value mt-1 ${state.total_realized_pl >= 0 ? "text-green-400" : "text-red-400"}`}>${state.total_realized_pl.toFixed(2)}</p></div>
        <div className="card"><p className="metric-label">Dividends</p><p className="metric-value mt-1 text-blue-400">${state.total_dividends.toFixed(2)}</p></div>
      </div>

      {state.holdings.size === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No holdings.</p>
          <p className="text-sm text-neutral-600 mt-2">Add transactions on the Transactions page.</p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="table-header">Ticker</th>
                  <th className="table-header text-right">Qty</th>
                  <th className="table-header text-right">Avg Cost</th>
                  <th className="table-header text-right">Price</th>
                  <th className="table-header text-right">Mkt Value</th>
                  <th className="table-header text-right">Unrealized</th>
                  <th className="table-header text-right">Weight</th>
                </tr>
              </thead>
              <tbody>
                {[...state.holdings.values()]
                  .sort((a, b) => (b.market_value || 0) - (a.market_value || 0))
                  .map((h) => {
                    const weight = h.market_value ? (h.market_value / nav) * 100 : 0;
                    return (
                      <tr key={h.ticker} className="border-b border-neutral-800/50">
                        <td className="table-cell-text font-semibold">{h.ticker}</td>
                        <td className="table-cell text-right">{h.quantity.toFixed(3)}</td>
                        <td className="table-cell text-right">${h.average_cost.toFixed(2)}</td>
                        <td className="table-cell text-right">{h.current_price ? `$${h.current_price.toFixed(2)}` : "—"}</td>
                        <td className="table-cell text-right">{h.market_value ? `$${h.market_value.toLocaleString()}` : "—"}</td>
                        <td className={`table-cell text-right ${(h.unrealized_pl || 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {h.unrealized_pl !== undefined ? `$${h.unrealized_pl.toFixed(2)}` : "—"}
                        </td>
                        <td className="table-cell text-right">{weight > 0 ? `${weight.toFixed(1)}%` : "—"}</td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
