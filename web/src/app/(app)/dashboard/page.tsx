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
      const [portfolioRes, modelRes, profileRes, portListRes] = await Promise.all([
        supabase.from("portfolios").select("*", { count: "exact", head: true }).eq("owner_id", user.id),
        supabase.from("model_snapshots").select("*", { count: "exact", head: true }).eq("status", "PUBLISHED"),
        supabase.from("profiles").select("is_owner").eq("id", user.id).single(),
        supabase.from("portfolios").select("id, name, opening_date, starting_cash, notes").eq("owner_id", user.id).order("created_at", { ascending: false }),
      ]);

      if (portfolioRes.error) {
        error = `Failed to load portfolios: ${portfolioRes.error.message}`;
      } else if (modelRes.error) {
        error = `Failed to load model: ${modelRes.error.message}`;
      } else {
        data = {
          portfolioCount: portfolioRes.count ?? 0,
          modelPublished: (modelRes.count ?? 0) > 0,
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
