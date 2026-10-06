import { loadRebalance } from "@/lib/route-loaders";
import { createServerSupabase } from "@/lib/supabase";
import Link from "next/link";
import { ArrowLeft, AlertTriangle } from "lucide-react";
import DecisionCell from "./DecisionCell";

const STATUS_STYLE: Record<string, string> = {
  Buy: "bg-green-500/10 text-green-400",
  Sell: "bg-red-500/10 text-red-400",
  Add: "bg-green-500/10 text-green-400",
  Reduce: "bg-red-500/10 text-red-400",
  Hold: "bg-neutral-800 text-neutral-300",
};

const GROUP_ORDER = ["Sell", "Buy", "Reduce", "Add", "Hold"] as const;
const GROUP_LABELS: Record<string, string> = {
  Sell: "Sell — holdings not in current Top 30",
  Buy: "Buy — Top 30 names missing from portfolio",
  Reduce: "Reduce — holdings above target",
  Add: "Add — holdings below target",
  Hold: "Hold — near target",
};

type DecisionInfo = { status: string; note: string };

export default async function RebalancePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let data: Awaited<ReturnType<typeof loadRebalance>> | null = null;
  let error: string | null = null;

  try {
    data = await loadRebalance(id as string);
  } catch (e: unknown) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-icon btn-ghost"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Rebalance Instructions</h1>
        </div>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!data || data.modelDate === "") {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-icon btn-ghost"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Rebalance Instructions</h1>
        </div>
        <div className="card text-center py-12">
          <p className="text-neutral-500">No Quarterly Top 30 generated yet. Generate one first.</p>
        </div>
      </div>
    );
  }

  if (data.comparisons.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-icon btn-ghost"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Rebalance Instructions</h1>
        </div>
        <div className="card text-center py-12">
          <p className="text-neutral-500">No portfolio holdings yet.</p>
        </div>
      </div>
    );
  }

  // ─── Load owner decisions ───────────────────────────────────────
  const decisionByTicker = new Map<string, DecisionInfo>();
  let userId = "";

  try {
    const supabase = await createServerSupabase();
    const { data: { user } } = await supabase.auth.getUser();
    if (user?.id) {
      userId = user.id;
      const { data: decisions } = await supabase
        .from("owner_decisions")
        .select("*")
        .eq("owner_id", userId)
        .eq("decision_data->>snapshot_id", data.snapshotId);
      if (decisions) {
        for (const d of decisions) {
          const dd = d.decision_data as Record<string, unknown> | null;
          const ticker = typeof dd?.ticker === "string" ? dd.ticker : "";
          if (ticker) {
            decisionByTicker.set(ticker, {
              status: typeof d.decision_type === "string" ? d.decision_type : "",
              note: typeof d.notes === "string" ? d.notes : "",
            });
          }
        }
      }
    }
  } catch {
    // Non-critical — proceed without decisions
  }

  // ─── Compute personal plan targets ──────────────────────────────
  let includedCount = 0;
  for (const c of data.comparisons) {
    const d = decisionByTicker.get(c.ticker);
    if (d && (d.status === "planned" || d.status === "executed")) {
      includedCount++;
    }
  }

  const personalTarget = new Map<string, string>();
  for (const c of data.comparisons) {
    const d = decisionByTicker.get(c.ticker);
    if (!d || d.status === "") {
      personalTarget.set(c.ticker, "—");
    } else if (d.status === "planned" || d.status === "executed") {
      const pct = includedCount > 0 ? (1 / includedCount) * 100 : 0;
      personalTarget.set(c.ticker, pct.toFixed(2) + "%");
    } else {
      personalTarget.set(c.ticker, "0.00%");
    }
  }

  const planSummary = includedCount > 0
    ? `${includedCount} name${includedCount !== 1 ? "s" : ""} included · ${(100 / includedCount).toFixed(2)}% each`
    : "No names planned";

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/portfolios/${id}`} className="btn-icon btn-ghost"><ArrowLeft className="w-4 h-4" /></Link>
        <div>
          <h1 className="text-xl font-semibold">Rebalance Instructions</h1>
          <p className="text-sm text-neutral-500">Model date: {data.modelDate}{data.hasPrices ? ` · NAV: $${data.nav.toLocaleString()}` : ""}</p>
        </div>
      </div>

      {!data.hasPrices && (
        <div className="flex items-center gap-2 text-sm text-amber-400 bg-amber-500/10 rounded px-3 py-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          Prices unavailable — rebalance instructions are approximate
        </div>
      )}

      <div className="flex items-center gap-3 text-sm text-neutral-400 bg-neutral-900/50 rounded px-3 py-2">
        <span className="text-neutral-500">Your plan:</span>
        <span className="text-neutral-300">{planSummary}</span>
      </div>

      <div className="card p-0 overflow-hidden">
        {GROUP_ORDER.map((group) => {
          const items = data.comparisons.filter((c) => c.action === group);
          if (items.length === 0) return null;
          return (
            <div key={group}>
              <div className="px-4 py-2 bg-neutral-900/50 border-b border-neutral-800">
                <span className={`text-xs font-semibold px-2 py-0.5 rounded ${STATUS_STYLE[group]}`}>{group}</span>
                <span className="text-xs text-neutral-500 ml-2">{GROUP_LABELS[group]} ({items.length})</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px]">
                  <thead>
                    <tr className="border-b border-neutral-800">
                      <th className="table-header">Ticker</th>
                      <th className="table-header text-right">Current %</th>
                      <th className="table-header text-right">Model Target %</th>
                      <th className="table-header text-right">Your Plan %</th>
                      {data.hasPrices && (
                        <>
                          <th className="table-header text-right">Current $</th>
                          <th className="table-header text-right">Target $</th>
                          <th className="table-header text-right">Diff $</th>
                          <th className="table-header text-right">~Shares</th>
                        </>
                      )}
                      <th className="table-header">Decision</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((c) => {
                      const decision = decisionByTicker.get(c.ticker);
                      const planPct = personalTarget.get(c.ticker);
                      const planWeight = planPct && planPct !== "—" && planPct !== "0.00%" ? parseFloat(planPct) / 100 : null;
                      const planTargetVal = data.hasPrices && data.nav > 0 && planWeight ? planWeight * data.nav : null;
                      const planDiff = planTargetVal !== null && c.currentValue !== null ? planTargetVal - c.currentValue : null;
                      const approxShares = data.hasPrices && planDiff !== null && c.currentPrice !== null && c.currentPrice > 0
                        ? Math.abs(planDiff) / c.currentPrice : null;
                      return (
                        <tr key={c.ticker} className="border-b border-neutral-800/50">
                          <td className="table-cell-text font-semibold">{c.ticker}</td>
                          <td className="table-cell text-right">{c.currentWeight}%</td>
                          <td className="table-cell text-right">{c.targetWeight}%</td>
                          <td className="table-cell text-right">{personalTarget.get(c.ticker)}</td>
                          {data.hasPrices && (
                            <>
                              <td className="table-cell text-right">{c.currentValue !== null ? `$${c.currentValue.toLocaleString()}` : "—"}</td>
                              <td className="table-cell text-right">{planTargetVal !== null ? `$${planTargetVal.toLocaleString()}` : c.targetValue !== null ? `$${c.targetValue.toLocaleString()}` : "—"}</td>
                              <td className={`table-cell text-right font-mono ${planDiff !== null && planDiff > 0 ? "text-green-400" : planDiff !== null && planDiff < 0 ? "text-red-400" : ""}`}>
                                {planDiff !== null ? `${planDiff >= 0 ? "+" : ""}$${Math.abs(planDiff).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "—"}
                              </td>
                              <td className="table-cell text-right font-mono text-neutral-400">{approxShares !== null ? `~${approxShares.toFixed(1)}` : "—"}</td>
                            </>
                          )}
                          <td className="table-cell">
                            <DecisionCell
                              key={`${c.ticker}-${decision?.status ?? "none"}-${decision?.note ?? ""}`}
                              portfolioId={id}
                              snapshotId={data.snapshotId}
                              securityId={c.security_id}
                              ticker={c.ticker}
                              recommendation={c.action}
                              initialStatus={decision?.status ?? ""}
                              initialNote={decision?.note ?? ""}
                            />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}
      </div>

      <div className="text-xs text-neutral-500 text-center">
        Manual decision support only. No orders are placed.
      </div>
    </div>
  );
}
