import { createServerSupabase } from "@/lib/supabase";
import { loadHoldings } from "@/lib/route-loaders";
import { getLatestModelSnapshot } from "@/lib/supabase-queries";
import Link from "next/link";
import HoldingsManager from "@/components/portfolios/HoldingsManager";
import RefreshPricesButton from "@/components/portfolios/RefreshPricesButton";
import PortfolioActivity from "@/components/portfolios/PortfolioActivity";
import DeletePortfolioButton from "@/components/portfolios/DeletePortfolioButton";

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
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">{holdingsError || "Failed to load holdings"}</p>
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">
          Portfolio{portfolio.name ? `: ${portfolio.name}` : ""}
        </h1>
        <DeletePortfolioButton portfolioId={portfolio.id} portfolioName={portfolio.name} />
      </div>

      <div className="flex items-center gap-4">
        <RefreshPricesButton portfolioId={portfolio.id} />
        <Link href="/compare" className="btn-ghost text-sm">
          Compare to Top 30 &rarr;
        </Link>
      </div>

      <HoldingsManager
        portfolioId={portfolio.id}
        holdings={holdings}
        cash={state.cash}
        totalMarketValue={totalMarketValue}
        totalCostBasis={totalCostBasis}
        totalUnrealized={totalUnrealized}
        modelTickers={modelTickers}
      />

      <PortfolioActivity portfolioId={portfolio.id} />
    </div>
  );
}
