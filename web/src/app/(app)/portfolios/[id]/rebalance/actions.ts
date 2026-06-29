"use server";
import { createServerSupabase } from "@/lib/supabase";
import { revalidatePath } from "next/cache";

export async function saveOwnerDecision(portfolioId: string, snapshotId: string, securityId: string, ticker: string, recommendation: string, status: string, note: string) {
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user?.id) return { error: "Not authenticated" };

  const { error } = await supabase.from("owner_decisions").upsert({
    decision_type: status,
    decision_data: { portfolio_id: portfolioId, security_id: securityId, snapshot_id: snapshotId, ticker, recommendation },
    notes: note || null,
    owner_id: user.id,
  }, { onConflict: "owner_id,decision_data" });
  
  if (error) return { error: error.message };
  revalidatePath(`/portfolios/${portfolioId}/rebalance`);
  return { error: null };
}
