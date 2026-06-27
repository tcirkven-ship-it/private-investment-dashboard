import { createServerSupabase } from "@/lib/supabase";
import DashboardClient from "./DashboardClient";
import type { DashboardData } from "./DashboardClient";

export const metadata = { title: "Dashboard — Investment Dashboard" };

export default async function DashboardPage() {
  let data: DashboardData | null = null;
  let error: string | null = null;

  try {
    const supabase = await createServerSupabase();
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      error = "Not authenticated";
    } else {
      const { count: portfolioCount, error: portErr } = await supabase
        .from("portfolios")
        .select("*", { count: "exact", head: true })
        .eq("owner_id", user.id);

      if (portErr) {
        error = `Failed to load portfolios: ${portErr.message}`;
      } else {
        const { count: modelCount, error: modelErr } = await supabase
          .from("model_snapshots")
          .select("*", { count: "exact", head: true })
          .eq("status", "PUBLISHED");

        if (modelErr) {
          error = `Failed to load model: ${modelErr.message}`;
        } else {
          data = {
            portfolioCount: portfolioCount ?? 0,
            modelPublished: (modelCount ?? 0) > 0,
          };
        }
      }
    }
  } catch (e) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  return <DashboardClient data={data} error={error} />;
}
