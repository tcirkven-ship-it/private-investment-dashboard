"use server";

import { createServerSupabase } from "@/lib/supabase";
import { revalidatePath } from "next/cache";

export async function deleteTransaction(txId: string, portfolioId: string) {
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user?.id) return { error: "Not authenticated" };

  const { error } = await supabase.from("transactions").delete().eq("id", txId).eq("owner_id", user.id);
  if (error) return { error: error.message };

  revalidatePath(`/portfolios/${portfolioId}/transactions`);
  revalidatePath(`/portfolios/${portfolioId}/holdings`);
  revalidatePath(`/portfolios/${portfolioId}/rebalance`);
  revalidatePath(`/portfolios/${portfolioId}/performance`);
  revalidatePath("/dashboard");
  return { error: null };
}
