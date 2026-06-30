import { createServerSupabase } from "@/lib/supabase";
import { loadHoldings } from "@/lib/route-loaders";
import { getLatestModelSnapshot } from "@/lib/supabase-queries";
import Link from "next/link";
import { Plus } from "lucide-react";
import RefreshPricesButton from "@/components/portfolios/RefreshPricesButton";

export default async function PortfoliosPage() {
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();

  const { data: portfolios } = await supabase
    .from("portfolios")
    .select("id, name")
    .eq("owner_id", user?.id)
    .order("created_at", { ascending: false });

  if (!portfolios || portfolios.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Portfolio</h1>
        <div className="card text-center py-12">
          <p className="text-neutral-500">No portfolios yet.</p>
          <Link href="/portfolios/new" className="btn-primary mt-4 inline-flex items-center">
            <Plus className="w-4 h-4 mr-1.5" /> Create Portfolio
          </Link>
        </div>
      </div>
    );
  }

  const portfolio = portfolios[0];

  let holdingsData: Awaited<ReturnType<typeof loadHoldings>> | null = null;
  let holdingsError: string | null = null;
  try {
    holdingsData = await loadHoldings(portfolio.id);
  } catch (e: unknown) {
    holdingsError = e instanceof Error ? e.message : "Unknown error";
  }

  const modelResult = await getLatestModelSnapshot();
  const modelTickers = new Set<string>();
  if (modelResult.data?.holdings) {
    for (const h of modelResult.data.holdings) {
      if (h.security?.ticker) modelTickers.add(h.security.ticker);
    }
  }

  if (holdingsError || !holdingsData) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Portfolio{portfolio.name ? `: ${portfolio.name}` : ""}</h1>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">{holdingsError || "Failed to load holdings"}</p>
        </div>
      </div>
    );
  }

  const { state, nav } = holdingsData;
  const holdings = [...state.holdings.values()];
  const totalMarketValue = holdings.reduce((s, h) => s + (h.market_value || 0), 0);
  const totalCostBasis = holdings.reduce((s, h) => s + h.total_cost, 0);
  const totalUnrealized = holdings.reduce((s, h) => s + (h.unrealized_pl || 0), 0);
  const unrealizedPct = totalCostBasis > 0 ? (totalUnrealized / totalCostBasis) * 100 : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">
        Portfolio{portfolio.name ? `: ${portfolio.name}` : ""}
      </h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="metric-label">Total Market Value</p>
          <p className="metric-value mt-1">${totalMarketValue.toLocaleString()}</p>
        </div>
        <div className="card">
          <p className="metric-label">Cash</p>
          <p className="metric-value mt-1">${state.cash.toLocaleString()}</p>
        </div>
        <div className="card">
          <p className="metric-label">Total Cost Basis</p>
          <p className="metric-value mt-1">${totalCostBasis.toLocaleString()}</p>
        </div>
        <div className="card">
          <p className="metric-label">Unrealized P/L</p>
          <p className={`metric-value mt-1 ${totalUnrealized >= 0 ? "text-green-400" : "text-red-400"}`}>
            ${totalUnrealized.toFixed(2)}
            <span className="text-sm ml-1">
              ({unrealizedPct >= 0 ? "+" : ""}{unrealizedPct.toFixed(2)}%)
            </span>
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <RefreshPricesButton />
        <Link href="/compare" className="btn-ghost text-sm">
          Compare to Top 30 &rarr;
        </Link>
      </div>

      {state.holdings.size === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No holdings yet.</p>
          <p className="text-sm text-neutral-600 mt-2">
            Add transactions to get started.
          </p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="table-header">Ticker</th>
                  <th className="table-header text-right">Shares</th>
                  <th className="table-header text-right">Avg Cost</th>
                  <th className="table-header text-right">Current Price</th>
                  <th className="table-header text-right">Market Value</th>
                  <th className="table-header text-right">Unrealized P/L</th>
                  <th className="table-header text-right">Unrealized P/L %</th>
                  <th className="table-header text-right">In Top 30?</th>
                </tr>
              </thead>
              <tbody>
                {holdings
                  .sort((a, b) => (b.market_value || 0) - (a.market_value || 0))
                  .map((h) => {
                    const uplPct = h.total_cost > 0 ? ((h.unrealized_pl || 0) / h.total_cost) * 100 : 0;
                    return (
                      <tr key={h.ticker} className="border-b border-neutral-800/50">
                        <td className="table-cell-text font-semibold">{h.ticker}</td>
                        <td className="table-cell text-right">{h.quantity.toFixed(3)}</td>
                        <td className="table-cell text-right">${h.average_cost.toFixed(2)}</td>
                        <td className="table-cell text-right">
                          {h.current_price ? `$${h.current_price.toFixed(2)}` : "—"}
                        </td>
                        <td className="table-cell text-right">
                          {h.market_value ? `$${h.market_value.toLocaleString()}` : "—"}
                        </td>
                        <td className={`table-cell text-right ${(h.unrealized_pl || 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {h.unrealized_pl !== undefined ? `$${h.unrealized_pl.toFixed(2)}` : "—"}
                        </td>
                        <td className={`table-cell text-right ${uplPct >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {h.unrealized_pl !== undefined ? `${uplPct >= 0 ? "+" : ""}${uplPct.toFixed(2)}%` : "—"}
                        </td>
                        <td className="table-cell text-right">
                          {modelTickers.size > 0
                            ? (modelTickers.has(h.ticker) ? "Yes" : "No")
                            : "—"}
                        </td>
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
