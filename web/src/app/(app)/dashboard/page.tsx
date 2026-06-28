import { createServerSupabase } from "@/lib/supabase";
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
      const [portfolioRes, modelRes, profileRes, portListRes, publishedModelRes, draftModelRes] = await Promise.all([
        supabase.from("portfolios").select("*", { count: "exact", head: true }).eq("owner_id", user.id),
        supabase.from("model_snapshots").select("*", { count: "exact", head: true }).eq("status", "PUBLISHED"),
        supabase.from("profiles").select("is_owner").eq("id", user.id).single(),
        supabase.from("portfolios").select("id, name, opening_date, starting_cash, notes").eq("owner_id", user.id).order("created_at", { ascending: false }),
        supabase.from("model_snapshots").select("id, effective_date, model_version_id").eq("status", "PUBLISHED").order("effective_date", { ascending: false }).limit(1).maybeSingle(),
        supabase.from("model_snapshots").select("id, effective_date, model_version_id").eq("status", "DRAFT").order("effective_date", { ascending: false }).limit(1).maybeSingle(),
      ]);

      if (portfolioRes.error) {
        error = `Failed to load portfolios: ${portfolioRes.error.message}`;
      } else if (modelRes.error) {
        error = `Failed to load model: ${modelRes.error.message}`;
      } else {
        const activeSnapshot = publishedModelRes.data || draftModelRes.data;
        let holdingsCount = 0;
        if (activeSnapshot) {
          const { count: hCount } = await supabase
            .from("model_snapshot_holdings")
            .select("*", { count: "exact", head: true })
            .eq("snapshot_id", activeSnapshot.id);
          holdingsCount = hCount ?? 0;
        }

        let modelStatus: string | null = null;
        if (publishedModelRes.data) {
          modelStatus = "PUBLISHED";
        } else if (draftModelRes.data) {
          modelStatus = "DRAFT";
        }

        data = {
          portfolioCount: portfolioRes.count ?? 0,
          modelPublished: (modelRes.count ?? 0) > 0,
          modelStatus,
          modelName: activeSnapshot ? "M1_B2_QUALITY_VETO_N30" : null,
          modelDate: activeSnapshot?.effective_date || null,
          holdingsCount,
          isOwner: profileRes.data?.is_owner === true,
        };
        portfolios = (portListRes.data || []) as typeof portfolios;
      }
    }
  } catch (e) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  return <DashboardClient data={data} error={error} portfolios={portfolios} />;
}
