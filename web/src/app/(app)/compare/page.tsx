import { createServerSupabase } from "@/lib/supabase";
import { loadHoldings } from "@/lib/route-loaders";
import { getLatestModelSnapshot } from "@/lib/supabase-queries";
import Link from "next/link";

export default async function ComparePage() {
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
        <h1 className="text-2xl font-semibold">Compare</h1>
        <div className="card text-center py-12">
          <p className="text-neutral-500">No portfolio holdings yet.</p>
          <p className="text-sm text-neutral-600 mt-2">
            <Link href="/portfolios" className="text-blue-400 hover:text-blue-300 underline">
              Go to Portfolio &rarr; Add Holding
            </Link>
          </p>
        </div>
      </div>
    );
  }

  const portfolio = portfolios[0];

  let holdingsResult: Awaited<ReturnType<typeof loadHoldings>>;
  try {
    holdingsResult = await loadHoldings(portfolio.id);
  } catch {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Compare</h1>
        <div className="card text-center py-12">
          <p className="text-neutral-500">No portfolio holdings yet.</p>
          <p className="text-sm text-neutral-600 mt-2">
            <Link href="/portfolios" className="text-blue-400 hover:text-blue-300 underline">
              Go to Portfolio &rarr; Add Holding
            </Link>
          </p>
        </div>
      </div>
    );
  }

  const modelResult = await getLatestModelSnapshot();
  const model = modelResult.data;

  if (modelResult.error || !model) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Compare</h1>
        <div className="card text-center py-12">
          <p className="text-neutral-500">No official model loaded yet.</p>
          <p className="text-sm text-neutral-600 mt-2">
            <Link href="/model" className="text-blue-400 hover:text-blue-300 underline">
              Go to Top 30 &rarr; Load Notebook-Generated Top 30
            </Link>
          </p>
        </div>
      </div>
    );
  }

  const { state } = holdingsResult;
  const ownedTickers = new Set(state.holdings.keys());

  const modelMap = new Map<string, { rank: number; b2_score: number | null; sector: string | null; industry: string | null; company: string | null }>();
  for (const h of model.holdings) {
    const ticker = h.security?.ticker;
    if (ticker) {
      modelMap.set(ticker, {
        rank: h.rank,
        b2_score: h.b2_score,
        sector: h.security?.sector ?? null,
        industry: h.security?.industry ?? null,
        company: h.security?.company_name ?? null,
      });
    }
  }

  const modelTickers = new Set(modelMap.keys());

  const keepTickers = [...ownedTickers].filter((t) => modelTickers.has(t));
  const buyTickers = [...modelTickers].filter((t) => !ownedTickers.has(t));
  const sellTickers = [...ownedTickers].filter((t) => !modelTickers.has(t));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Compare</h1>
        <p className="text-sm text-neutral-500 mt-1">
          {portfolio.name} vs {model.model_version?.model_id || "Top 30"}
          {" "}&mdash; {model.effective_date || ""}
        </p>
      </div>

      <div className="card p-0 overflow-hidden">
        <h2 className="text-sm font-semibold p-4 pb-2 border-b border-neutral-800">
          Already Own / In Top 30
          <span className="text-neutral-500 font-normal ml-2">({keepTickers.length})</span>
        </h2>
        {keepTickers.length === 0 ? (
          <p className="p-4 text-sm text-neutral-500">No portfolio holdings match the latest Top 30.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="table-header">Ticker</th>
                  <th className="table-header text-right">Shares</th>
                  <th className="table-header text-right">Current Value</th>
                  <th className="table-header text-right">Rank</th>
                  <th className="table-header text-right">B2 Score</th>
                </tr>
              </thead>
              <tbody>
                {keepTickers
                  .sort((a, b) => (modelMap.get(a)?.rank ?? 99) - (modelMap.get(b)?.rank ?? 99))
                  .map((ticker) => {
                    const h = state.holdings.get(ticker)!;
                    const m = modelMap.get(ticker);
                    return (
                      <tr key={ticker} className="border-b border-neutral-800/50">
                        <td className="table-cell-text font-semibold">{ticker}</td>
                        <td className="table-cell text-right">{h.quantity.toFixed(3)}</td>
                        <td className="table-cell text-right">
                          {h.market_value ? `$${h.market_value.toLocaleString()}` : "—"}
                        </td>
                        <td className="table-cell text-right">{m?.rank ?? "—"}</td>
                        <td className="table-cell text-right">{m?.b2_score?.toFixed(3) ?? "—"}</td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card p-0 overflow-hidden">
        <h2 className="text-sm font-semibold p-4 pb-2 border-b border-neutral-800">
          New in Top 30 / Consider Buying
          <span className="text-neutral-500 font-normal ml-2">({buyTickers.length})</span>
        </h2>
        {buyTickers.length === 0 ? (
          <p className="p-4 text-sm text-neutral-500">Your portfolio covers all Top 30 stocks.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="table-header">Rank</th>
                  <th className="table-header">Ticker</th>
                  <th className="table-header">Company</th>
                  <th className="table-header text-right">B2 Score</th>
                  <th className="table-header">Sector</th>
                  <th className="table-header">Industry</th>
                </tr>
              </thead>
              <tbody>
                {buyTickers
                  .sort((a, b) => (modelMap.get(a)?.rank ?? 99) - (modelMap.get(b)?.rank ?? 99))
                  .map((ticker) => {
                    const m = modelMap.get(ticker)!;
                    return (
                      <tr key={ticker} className="border-b border-neutral-800/50">
                        <td className="table-cell-text text-neutral-500">{m.rank}</td>
                        <td className="table-cell-text font-semibold">{ticker}</td>
                        <td className="table-cell-text text-sm text-neutral-400">{m.company ?? "—"}</td>
                        <td className="table-cell text-right">{m.b2_score?.toFixed(3) ?? "—"}</td>
                        <td className="table-cell-text text-sm">{m.sector ?? "—"}</td>
                        <td className="table-cell-text text-sm text-neutral-400">{m.industry ?? "—"}</td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card p-0 overflow-hidden">
        <h2 className="text-sm font-semibold p-4 pb-2 border-b border-neutral-800">
          Owned but Not in Top 30 / Consider Selling
          <span className="text-neutral-500 font-normal ml-2">({sellTickers.length})</span>
        </h2>
        {sellTickers.length === 0 ? (
          <p className="p-4 text-sm text-neutral-500">All holdings are in the Top 30.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="table-header">Ticker</th>
                  <th className="table-header text-right">Shares</th>
                  <th className="table-header text-right">Current Value</th>
                  <th className="table-header text-right">Unrealized P/L</th>
                  <th className="table-header">Reason</th>
                </tr>
              </thead>
              <tbody>
                {sellTickers
                  .sort((a, b) => (state.holdings.get(b)?.market_value || 0) - (state.holdings.get(a)?.market_value || 0))
                  .map((ticker) => {
                    const h = state.holdings.get(ticker)!;
                    return (
                      <tr key={ticker} className="border-b border-neutral-800/50">
                        <td className="table-cell-text font-semibold">{ticker}</td>
                        <td className="table-cell text-right">{h.quantity.toFixed(3)}</td>
                        <td className="table-cell text-right">
                          {h.market_value ? `$${h.market_value.toLocaleString()}` : "—"}
                        </td>
                        <td className={`table-cell text-right ${(h.unrealized_pl || 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {h.unrealized_pl !== undefined ? `$${h.unrealized_pl.toFixed(2)}` : "—"}
                        </td>
                        <td className="table-cell-text text-sm text-neutral-400">Not in latest Top 30</td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
