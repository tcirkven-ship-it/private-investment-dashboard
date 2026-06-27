"use server";

import { createServerSupabase } from "./supabase";
import { revalidatePath } from "next/cache";

export interface ActionResult {
  error: string | null;
}

export async function insertTransaction(formData: FormData): Promise<ActionResult> {
  const supabase = await createServerSupabase();
  const portfolioId = formData.get("portfolio_id") as string;
  const eventType = formData.get("event_type") as string;
  const eventDate = formData.get("event_date") as string;
  const grossAmount = parseFloat(formData.get("gross_amount") as string) || 0;
  const idempotencyKey = `tx-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

  if (!portfolioId || !eventType || !eventDate) {
    return { error: "Missing required fields" };
  }

  const { data: user } = await supabase.auth.getUser();
  if (!user?.user?.id) return { error: "Not authenticated" };

  const quantity = parseFloat(formData.get("quantity") as string) || 0;
  const price = parseFloat(formData.get("price") as string) || 0;
  const commission = parseFloat(formData.get("commission") as string) || 0;

  const payload: Record<string, unknown> = {
    portfolio_id: portfolioId,
    event_type: eventType,
    event_date: eventDate,
    gross_amount: grossAmount,
    quantity: quantity || null,
    price: price || null,
    commission: commission || 0,
    idempotency_key: idempotencyKey,
    owner_id: user.user.id,
  };

  const ticker = formData.get("ticker") as string;
  if (ticker) {
    // Find or create security
    const { data: sec } = await supabase
      .from("securities")
      .select("id")
      .eq("ticker", ticker.toUpperCase())
      .maybeSingle();
    if (sec) {
      payload.security_id = sec.id;
    }
  }

  const { error } = await supabase.from("transactions").insert(payload);
  if (error) return { error: error.message };

  revalidatePath(`/portfolios/${portfolioId}`);
  return { error: null };
}
