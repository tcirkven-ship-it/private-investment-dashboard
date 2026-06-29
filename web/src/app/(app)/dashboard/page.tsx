import { createServerSupabase } from "@/lib/supabase";
import { getLatestModelSnapshot, getModelCounts } from "@/lib/supabase-queries";
import DashboardClient from "./DashboardClient";
import type { DashboardData } from "./DashboardClient";

export const metadata = { title: "Dashboard — Investment Dashboard" };

function computeNextReviewWindow(): string {
  const d = new Date();
  const q = Math.floor(d.getMonth() / 3);
  const months = ["March", "June", "September", "December"];
  const qEnd = months[q];
  const year = q === 3 && d.getMonth() >= 9 ? d.getFullYear() + 1 : d.getFullYear();
  return `Next review window: after final trading session of ${qEnd} ${year}`;
}

export default async function DashboardPage() {
  let data: DashboardData | null = null;
  let error: string | null = null;
  let portfolios: Array<{ id: string; name: string; opening_date: string; starting_cash: number | null; notes: string | null }> = [];

  try {
    const supabase = await createServerSupabase();
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      error = "Not authenticated";
    } else {
      const [portCountRes, modelResult, modelCounts, portListRes] = await Promise.all([
        supabase.from("portfolios").select("*", { count: "exact", head: true }).eq("owner_id", user.id),
        getLatestModelSnapshot(),
        getModelCounts(),
        supabase.from("portfolios").select("id, name, opening_date, starting_cash, notes").eq("owner_id", user.id).order("created_at", { ascending: false }),
      ]);

      if (portCountRes.error) {
        error = `Failed to load portfolios: ${portCountRes.error.message}`;
      } else {
        const model = modelResult.data;
        const portfolioIds = (portListRes.data || []).map((p) => p.id);

        let priceCount = 0;
        let hasValuation = false;
        if (portfolioIds.length > 0) {
          const [pcRes, vcRes] = await Promise.all([
            supabase.from("price_observations").select("*", { count: "exact", head: true }),
            supabase.from("portfolio_valuations").select("*", { count: "exact", head: true }).in("portfolio_id", portfolioIds),
          ]);
          priceCount = pcRes.count ?? 0;
          hasValuation = (vcRes.count ?? 0) > 0;
        }

        let nextAction = "";
        const hasModel = model !== null;
        const hasPortfolio = (portCountRes.count ?? 0) > 0;
        if (!hasModel) {
          nextAction = "Generate Quarterly Top 30";
        } else if (hasPortfolio && priceCount === 0) {
          nextAction = "Add missing prices";
        } else if (priceCount > 0 && !hasValuation) {
          nextAction = "Record valuation snapshot";
        } else if (hasModel && hasPortfolio) {
          nextAction = "Review rebalance instructions";
        }

        data = {
          portfolioCount: portCountRes.count ?? 0,
          hasModel,
          modelStatus: model?.status ?? null,
          modelDate: model?.effective_date ?? null,
          holdingsCount: model?.holdings?.length ?? 0,
          modelPublished: modelCounts.published > 0,
          modelDraft: modelCounts.draft > 0,
          nextAction,
          nextReviewWindow: computeNextReviewWindow(),
        };
        portfolios = (portListRes.data || []) as typeof portfolios;
      }
    }
  } catch (e) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  return <DashboardClient data={data} error={error} portfolios={portfolios} />;
}
