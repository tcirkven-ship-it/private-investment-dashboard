"use server";
import { createServerSupabase } from "@/lib/supabase";
import { revalidatePath } from "next/cache";

export async function saveOwnerDecision(portfolioId: string, snapshotId: string, securityId: string, ticker: string, recommendation: string, status: string, note: string) {
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user?.id) return { error: "Not authenticated" };

  // Check for existing decision with same snapshot + ticker
  const { data: existing } = await supabase.from("owner_decisions")
    .select("id")
    .eq("owner_id", user.id)
    .eq("decision_data->>snapshot_id", snapshotId)
    .eq("decision_data->>ticker", ticker)
    .maybeSingle();

  if (existing) {
    const { error } = await supabase.from("owner_decisions").update({
      decision_type: status,
      notes: note || null,
    }).eq("id", existing.id);
    if (error) return { error: error.message };
  } else {
    const { error } = await supabase.from("owner_decisions").insert({
      decision_type: status,
      decision_data: { portfolio_id: portfolioId, security_id: securityId, snapshot_id: snapshotId, ticker, recommendation },
      notes: note || null,
      owner_id: user.id,
    });
    if (error) return { error: error.message };
  }

  revalidatePath(`/portfolios/${portfolioId}/rebalance`);
  return { error: null };
}
