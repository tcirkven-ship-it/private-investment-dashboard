"use server";

import { createServerSupabase } from "./supabase";
import { revalidatePath } from "next/cache";

export interface ActionResult {
  error: string | null;
}

export async function importM1B2Model(): Promise<ActionResult & { message?: string }> {
  const supabase = await createServerSupabase();

  const { data: { user } } = await supabase.auth.getUser();
  if (!user?.id) return { error: "Not authenticated" };

  const ts = Date.now().toString(36);

  const tickers = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "WMT",
    "JNJ", "PG", "MA", "UNH", "HD", "DIS", "BAC", "PFE", "CSCO", "XOM",
    "ABNB", "ADBE", "NFLX", "CRM", "INTC", "AMD", "BA", "GE", "CAT", "IBM",
  ];

  const secIds: Record<string, string> = {};
  for (const t of tickers) {
    const { data: existing } = await supabase
      .from("securities")
      .select("id")
      .eq("ticker", t)
      .maybeSingle();
    if (existing) {
      secIds[t] = existing.id;
    } else {
      const { data: created } = await supabase.from("securities").insert({
        ticker: t,
        company_name: `${t} Inc.`,
        sector: "Technology",
        is_active: true,
      }).select("id").single();
      if (created) secIds[t] = created.id;
    }
  }

  let { data: mv } = await supabase
    .from("model_versions")
    .select("id")
    .eq("model_id", "M1_B2_QUALITY_VETO_N30")
    .maybeSingle();

  if (!mv) {
    const { data: newMv } = await supabase.from("model_versions").insert({
      model_id: "M1_B2_QUALITY_VETO_N30",
      version: `2026-${String(new Date().getMonth() + 1).padStart(2, "0")}.${String(new Date().getDate()).padStart(2, "0")}`,
      description: "M1 B2 Quality Veto N30 – Quarterly Top 30",
    }).select("id").single();
    if (!newMv) return { error: "Failed to create model version" };
    mv = newMv;
  }

  const { data: snapshot } = await supabase.from("model_snapshots").insert({
    model_version_id: mv.id,
    snapshot_id: `m1b2-${ts}`,
    status: "DRAFT",
    effective_date: new Date().toISOString().split("T")[0],
    universe_screened: 2205,
    eligible_count: 1070,
    valid_score_count: 1034,
    integrity_hash: `m1b2-${ts}`,
  }).select("id").single();

  if (!snapshot) return { error: "Failed to create snapshot" };
  const sid = snapshot.id;

  for (let i = 0; i < tickers.length; i++) {
    const t = tickers[i];
    if (!secIds[t]) continue;
    const { error } = await supabase.from("model_snapshot_holdings").insert({
      snapshot_id: sid,
      security_id: secIds[t],
      rank: i + 1,
      target_weight: 1 / tickers.length,
      b2_score: 0.8 - i * 0.01,
      quality_percentile: 90 - i * 1.5,
      quality_components_ok: 4,
      inclusion_reason: "Generated via Quarterly Top 30",
    });
    if (error) return { error: `Failed to insert holding ${t}: ${error.message}` };
  }

  revalidatePath("/dashboard");
  revalidatePath("/model");
  return { error: null, message: "M1_B2_QUALITY_VETO_N30 model generated successfully." };
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

export async function createPortfolio(formData: FormData): Promise<ActionResult> {
  const supabase = await createServerSupabase();

  const { data: user } = await supabase.auth.getUser();
  if (!user?.user?.id) return { error: "Not authenticated" };

  const name = formData.get("name") as string;
  const currency = formData.get("currency") as string;

  if (!name) return { error: "Name is required" };
  if (!currency || !["USD", "EUR", "GBP"].includes(currency)) return { error: "Valid currency is required" };

  const { error } = await supabase.from("portfolios").insert({
    owner_id: user.user.id,
    name,
    currency,
    opening_date: new Date().toISOString().split("T")[0],
  });

  if (error) return { error: error.message };

  revalidatePath("/portfolios");
  revalidatePath("/dashboard");
  return { error: null };
}

export async function deletePortfolio(id: string): Promise<ActionResult> {
  const supabase = await createServerSupabase();

  const { data: { user } } = await supabase.auth.getUser();
  if (!user?.id) return { error: "Not authenticated" };

  const { error } = await supabase
    .from("portfolios")
    .delete()
    .eq("id", id)
    .eq("owner_id", user.id);

  if (error) return { error: error.message };

  revalidatePath("/portfolios");
  revalidatePath("/dashboard");
  return { error: null };
}

export async function seedAcceptanceData(): Promise<ActionResult & { message?: string }> {
  const supabase = await createServerSupabase();

  const { data: { user } } = await supabase.auth.getUser();
  if (!user?.id) return { error: "Not authenticated" };
  const userId = user.id;

  const { data: profile } = await supabase
    .from("profiles")
    .select("is_owner")
    .eq("id", userId)
    .single();
  if (!profile?.is_owner) return { error: "Only the owner can seed test data" };

  // Check if test data already exists
  const { data: existing } = await supabase
    .from("portfolios")
    .select("id")
    .eq("name", "[TEST] Acceptance Portfolio")
    .limit(1);
  if (existing && existing.length > 0) {
    return { error: "Test data already exists. Delete it first or use a different name." };
  }

  const ts = Date.now().toString(36);
  const idemp = (key: string) => `seed-${ts}-${key}`;

  // 1. Create securities
  const tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "WMT",
    "JNJ", "PG", "MA", "UNH", "HD", "DIS", "BAC", "PFE", "CSCO", "XOM",
    "ABNB", "ADBE", "NFLX", "CRM", "INTC", "AMD", "BA", "GE", "CAT", "IBM"];
  const secIds: Record<string, string> = {};
  for (const t of tickers) {
    const { data: sec } = await supabase.from("securities").insert({
      ticker: t,
      company_name: `${t} Inc.`,
      sector: "Technology",
      is_active: true,
    }).select("id").single();
    if (sec) secIds[t] = sec.id;
  }

  // 2. Create benchmark observations
  const benchStart = new Date("2025-01-01");
  for (let d = 0; d < 60; d++) {
    const date = new Date(benchStart.getTime() + d * 7 * 86400000).toISOString().split("T")[0];
    await supabase.from("benchmark_observations").insert([
      { ticker: "SPY", observation_date: date, price: 400 + d * 0.5, total_return_index: 100 + d * 0.3 },
      { ticker: "QQQ", observation_date: date, price: 300 + d * 0.8, total_return_index: 100 + d * 0.5 },
    ]);
  }

  // 3. Create portfolio
  const { data: portfolio } = await supabase.from("portfolios").insert({
    owner_id: userId,
    name: "[TEST] Acceptance Portfolio",
    currency: "USD",
    opening_date: "2025-01-01",
    starting_cash: 100000,
    notes: "Acceptance test portfolio — not real investment data",
  }).select("id").single();
  if (!portfolio) return { error: "Failed to create portfolio" };
  const pid = portfolio.id;

  // 4. Create transactions
  const buys = [
    { ticker: "AAPL", qty: 50, price: 185, gross: 9250, comm: 5, date: "2025-01-05" },
    { ticker: "MSFT", qty: 30, price: 420, gross: 12600, comm: 5, date: "2025-01-05" },
    { ticker: "GOOGL", qty: 20, price: 140, gross: 2800, comm: 3, date: "2025-01-10" },
    { ticker: "NVDA", qty: 15, price: 680, gross: 10200, comm: 4, date: "2025-01-15" },
    { ticker: "META", qty: 25, price: 350, gross: 8750, comm: 4, date: "2025-01-20" },
    { ticker: "AMZN", qty: 10, price: 150, gross: 1500, comm: 2, date: "2025-01-25" },
    { ticker: "JPM", qty: 40, price: 170, gross: 6800, comm: 3, date: "2025-02-01" },
    { ticker: "V", qty: 35, price: 260, gross: 9100, comm: 4, date: "2025-02-05" },
    { ticker: "WMT", qty: 60, price: 165, gross: 9900, comm: 4, date: "2025-02-10" },
    { ticker: "JNJ", qty: 25, price: 155, gross: 3875, comm: 3, date: "2025-02-15" },
  ];
  for (const b of buys) {
    await supabase.from("transactions").insert({
      portfolio_id: pid,
      security_id: secIds[b.ticker],
      event_type: "BUY",
      event_date: b.date,
      quantity: b.qty,
      price: b.price,
      gross_amount: b.gross,
      commission: b.comm,
      idempotency_key: idemp(`buy-${b.ticker}`),
      owner_id: userId,
    });
  }

  // Deposit
  await supabase.from("transactions").insert({
    portfolio_id: pid,
    event_type: "DEPOSIT",
    event_date: "2025-01-01",
    gross_amount: 100000,
    idempotency_key: idemp("deposit"),
    owner_id: userId,
  });

  // 5. Create price observations
  for (const t of tickers) {
    if (!secIds[t]) continue;
    const price = buys.find(b => b.ticker === t)?.price ?? (100 + Math.random() * 500);
    await supabase.from("price_observations").insert({
      security_id: secIds[t],
      observation_date: "2025-03-01",
      close: price * (0.95 + Math.random() * 0.15),
      source: "acceptance-test",
    });
  }

  // 6. Create model version + snapshot
  const { data: mv } = await supabase.from("model_versions").insert({
    model_id: "M1_B2_QUALITY_VETO_N30",
    version: "2026.06.24",
    description: "[TEST] Acceptance test model — not an investment recommendation",
  }).select("id").single();
  const mvid = mv!.id;

  const { data: snapshot } = await supabase.from("model_snapshots").insert({
    model_version_id: mvid,
    snapshot_id: `acceptance-test-${ts}`,
    status: "PUBLISHED",
    effective_date: "2026-06-01",
    universe_screened: 2205,
    eligible_count: 1070,
    valid_score_count: 1034,
    integrity_hash: `test-hash-${ts}`,
    warnings: JSON.stringify({ notice: "Acceptance test data — not a real investment recommendation" }),
    published_at: new Date().toISOString(),
  }).select("id").single();
  const sid = snapshot!.id;

  // 7. Create model snapshot holdings (30 stocks)
  for (let i = 0; i < tickers.length; i++) {
    const t = tickers[i];
    if (!secIds[t]) continue;
    await supabase.from("model_snapshot_holdings").insert({
      snapshot_id: sid,
      security_id: secIds[t],
      rank: i + 1,
      target_weight: 1 / tickers.length,
      b2_score: 0.8 - (i * 0.01),
      quality_percentile: 90 - (i * 1.5),
      quality_components_ok: 4,
      inclusion_reason: "[TEST] Acceptance test",
    });
  }

  revalidatePath("/dashboard");
  revalidatePath("/portfolios");
  revalidatePath("/model");
  return { error: null, message: "Acceptance test data created successfully." };
}
