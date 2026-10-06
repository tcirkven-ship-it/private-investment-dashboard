import { createServerSupabase } from "@/lib/supabase";
import { loadHoldings } from "@/lib/route-loaders";
import { getLatestModelSnapshot } from "@/lib/supabase-queries";
import { computeInvestedCapital, totalPnl, totalReturnPct } from "@/lib/performance";
import Link from "next/link";
import HoldingsManager from "@/components/portfolios/HoldingsManager";
import RefreshPricesButton from "@/components/portfolios/RefreshPricesButton";
import PortfolioActivity from "@/components/portfolios/PortfolioActivity";
import DeletePortfolioButton from "@/components/portfolios/DeletePortfolioButton";
import RenamePortfolioButton from "@/components/portfolios/RenamePortfolioButton";

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
          <p className="text-neutral-500 mb-4">No portfolios yet.</p>
          <Link href="/portfolios/new" className="btn btn-primary">
            Create Portfolio
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
        <div className="alert alert-error">
          <p>{holdingsError || "Failed to load holdings"}</p>
        </div>
      </div>
    );
  }

  const { state } = holdingsData;
  const rawHoldings = [...state.holdings.values()];
  const holdings = rawHoldings.map((h) => ({
    ticker: h.ticker,
    quantity: h.quantity,
    total_cost: h.total_cost,
    average_cost: h.average_cost,
    market_value: h.market_value,
    current_price: h.current_price,
    unrealized_pl: h.unrealized_pl,
  }));
  const totalMarketValue = holdings.reduce((s, h) => s + (h.market_value || 0), 0);
  const totalCostBasis = holdings.reduce((s, h) => s + h.total_cost, 0);
  const totalUnrealized = holdings.reduce((s, h) => s + (h.unrealized_pl || 0), 0);
  const unrealizedPct = totalCostBasis > 0 ? (totalUnrealized / totalCostBasis) * 100 : 0;

  const invested = computeInvestedCapital(holdingsData.transactions);
  const currentValue = state.cash + totalMarketValue;
  const totalPnlValue = totalPnl(currentValue, invested.value);
  const totalReturn = totalReturnPct(totalPnlValue, invested.value);
  const money = (n: number) => `$${Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  return (
    <div className="space-y-5">
      <div className="page-header">
        <h1>
          Portfolio{portfolio.name ? `: ${portfolio.name}` : ""}
          <RenamePortfolioButton portfolioId={portfolio.id} currentName={portfolio.name || "Portfolio"} />
        </h1>
      </div>

      <Link href="/performance" className="card flex items-center justify-between gap-4 flex-wrap py-3">
        <div className="flex items-center gap-x-6 gap-y-1 flex-wrap text-sm">
          <span>
            <span className="text-neutral-500">Invested Capital: </span>
            <span className="font-mono tabular-nums">{money(invested.value)}</span>
            {invested.estimated && <span className="text-amber-400 text-xs ml-1">(estimated)</span>}
          </span>
          <span>
            <span className="text-neutral-500">Current Value: </span>
            <span className="font-mono tabular-nums">{money(currentValue)}</span>
          </span>
          <span>
            <span className="text-neutral-500">Total P&L: </span>
            <span className={`font-mono tabular-nums ${totalPnlValue >= 0 ? "metric-positive" : "metric-negative"}`}>
              {totalPnlValue >= 0 ? "+" : "−"}{money(totalPnlValue)}
            </span>
          </span>
          <span>
            <span className="text-neutral-500">Total Return: </span>
            <span className={`font-mono tabular-nums ${totalReturn === null ? "" : totalReturn >= 0 ? "metric-positive" : "metric-negative"}`}>
              {totalReturn === null ? "—" : `${totalReturn >= 0 ? "+" : "−"}${Math.abs(totalReturn).toFixed(2)}%`}
            </span>
          </span>
        </div>
        <span className="text-xs text-neutral-500">Performance &rarr;</span>
      </Link>

      {state.warnings.length > 0 && (
        <div className="alert alert-warning">
          <p className="font-medium">Holdings validation</p>
          {state.warnings.map((w, i) => (
            <p key={i} className="text-xs mt-1">{w}</p>
          ))}
        </div>
      )}

      <HoldingsManager
        portfolioId={portfolio.id}
        holdings={holdings}
        cash={state.cash}
        totalMarketValue={totalMarketValue}
        totalCostBasis={totalCostBasis}
        totalUnrealized={totalUnrealized}
        totalRealized={state.total_realized_pl}
        modelTickers={modelTickers}
        toolbarActions={
          <>
            <RefreshPricesButton portfolioId={portfolio.id} />
            <Link href="/compare" className="btn btn-ghost text-sm">
              Compare to Top 30 &rarr;
            </Link>
            <DeletePortfolioButton portfolioId={portfolio.id} portfolioName={portfolio.name} />
          </>
        }
      />

      <PortfolioActivity portfolioId={portfolio.id} />
    </div>
  );
}
