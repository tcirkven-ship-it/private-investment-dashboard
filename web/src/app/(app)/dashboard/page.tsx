import { createServerSupabase } from "@/lib/supabase";
import { getLatestModelSnapshot, getModelCounts } from "@/lib/supabase-queries";
import DashboardClient from "./DashboardClient";
import type { DashboardData } from "./DashboardClient";

export const metadata = { title: "Dashboard — Investment Dashboard" };

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
        data = {
          portfolioCount: portCountRes.count ?? 0,
          hasModel: model !== null,
          modelStatus: model?.status ?? null,
          modelDate: model?.effective_date ?? null,
          holdingsCount: model?.holdings?.length ?? 0,
          modelPublished: modelCounts.published > 0,
          modelDraft: modelCounts.draft > 0,
        };
        portfolios = (portListRes.data || []) as typeof portfolios;
      }
    }
  } catch (e) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  return <DashboardClient data={data} error={error} portfolios={portfolios} />;
}
