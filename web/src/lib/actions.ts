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
  const currency = formData.get("currency") as string || "USD";

  if (!name) {
    return { error: "Portfolio name is required" };
  }

  const { error: portErr, data: portfolio } = await supabase.from("portfolios").insert({
    owner_id: user.user.id,
    name,
    currency,
    opening_date: new Date().toISOString().split("T")[0],
  }).select("id").single();

  if (portErr) return { error: portErr.message };

  revalidatePath("/portfolios");
  revalidatePath("/dashboard");
  return { error: null };
}

export async function deletePortfolio(portfolioId: string): Promise<ActionResult> {
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user?.id) return { error: "Not authenticated" };
  const { error } = await supabase.from("portfolios").delete().eq("id", portfolioId).eq("owner_id", user.id);
  if (error) return { error: error.message };
  revalidatePath("/portfolios");
  revalidatePath("/dashboard");
  return { error: null };
}

export async function correctTransaction(transactionId: string, portfolioId: string): Promise<ActionResult> {
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user?.id) return { error: "Not authenticated" };
  const { error } = await supabase.from("transactions").update({
    corrected_by: transactionId,
  }).eq("id", transactionId).eq("owner_id", user.id);
  if (error) return { error: error.message };
  revalidatePath(`/portfolios/${portfolioId}`);
  return { error: null };
}

export async function importM1B2Model(): Promise<ActionResult & { message?: string }> {
  const supabase = await createServerSupabase();

  const { data: { user } } = await supabase.auth.getUser();
  if (!user?.id) return { error: "Not authenticated" };

  const { data: profile } = await supabase
    .from("profiles")
    .select("is_owner")
    .eq("id", user.id)
    .single();
  if (!profile?.is_owner) return { error: "Only the owner can import the official model" };

  // Clean up existing DRAFT snapshots to allow re-import via Refresh
  const { data: existingMVs } = await supabase
    .from("model_versions")
    .select("id")
    .eq("model_id", "M1_B2_QUALITY_VETO_N30");
  if (existingMVs && existingMVs.length > 0) {
    const mvIds = existingMVs.map(mv => mv.id);
    const { data: draftSnapshots } = await supabase
      .from("model_snapshots")
      .select("id")
      .in("model_version_id", mvIds)
      .eq("status", "DRAFT");
    if (draftSnapshots && draftSnapshots.length > 0) {
      const snapIds = draftSnapshots.map(s => s.id);
      await supabase.from("model_snapshot_holdings").delete().in("snapshot_id", snapIds);
      await supabase.from("model_snapshots").delete().in("id", snapIds);
    }
    await supabase.from("model_snapshots").update({ model_version_id: null }).in("model_version_id", mvIds);
    await supabase.from("model_versions").delete().in("id", mvIds);
  }

  const M1_TICKERS: Array<{ ticker: string; sector: string; industry: string; b2_score: number; quality_percentile: number }> = [
    { ticker: "MU", sector: "Technology", industry: "Semiconductors", b2_score: 0.9879, quality_percentile: 0.6988 },
    { ticker: "DOCN", sector: "Technology", industry: "Software - Infrastructure", b2_score: 0.9879, quality_percentile: 0.3376 },
    { ticker: "BE", sector: "Industrials", industry: "Electrical Equipment & Parts", b2_score: 0.9879, quality_percentile: 0.2551 },
    { ticker: "VICR", sector: "Technology", industry: "Electronic Components", b2_score: 0.9879, quality_percentile: 0.7532 },
    { ticker: "TTMI", sector: "Technology", industry: "Electronic Components", b2_score: 0.9879, quality_percentile: 0.2789 },
    { ticker: "MXL", sector: "Technology", industry: "Semiconductors", b2_score: 0.9879, quality_percentile: 0.3268 },
    { ticker: "WDC", sector: "Technology", industry: "Computer Hardware", b2_score: 0.9879, quality_percentile: 0.7498 },
    { ticker: "SYRE", sector: "Healthcare", industry: "Biotechnology", b2_score: 0.9832, quality_percentile: 0.2908 },
    { ticker: "POWL", sector: "Industrials", industry: "Electrical Equipment & Parts", b2_score: 0.9788, quality_percentile: 0.8923 },
    { ticker: "STRL", sector: "Industrials", industry: "Engineering & Construction", b2_score: 0.9782, quality_percentile: 0.7891 },
    { ticker: "AMD", sector: "Technology", industry: "Semiconductors", b2_score: 0.9757, quality_percentile: 0.5869 },
    { ticker: "AGX", sector: "Industrials", industry: "Engineering & Construction", b2_score: 0.9579, quality_percentile: 0.7991 },
    { ticker: "GTX", sector: "Consumer Cyclical", industry: "Auto Parts", b2_score: 0.9570, quality_percentile: 0.5789 },
    { ticker: "MYRG", sector: "Industrials", industry: "Engineering & Construction", b2_score: 0.9480, quality_percentile: 0.6905 },
    { ticker: "FIX", sector: "Industrials", industry: "Engineering & Construction", b2_score: 0.9458, quality_percentile: 0.8797 },
    { ticker: "MTRN", sector: "Basic Materials", industry: "Other Industrial Metals & Mining", b2_score: 0.9393, quality_percentile: 0.4153 },
    { ticker: "ELVN", sector: "Healthcare", industry: "Biotechnology", b2_score: 0.9380, quality_percentile: 0.2972 },
    { ticker: "VRT", sector: "Industrials", industry: "Electrical Equipment & Parts", b2_score: 0.9287, quality_percentile: 0.8084 },
    { ticker: "BTSG", sector: "Healthcare", industry: "Health Information Services", b2_score: 0.9227, quality_percentile: 0.3984 },
    { ticker: "KGS", sector: "Energy", industry: "Oil & Gas Equipment & Services", b2_score: 0.9227, quality_percentile: 0.4196 },
    { ticker: "MOD", sector: "Consumer Cyclical", industry: "Auto Parts", b2_score: 0.9209, quality_percentile: 0.5017 },
    { ticker: "INSW", sector: "Energy", industry: "Oil & Gas Midstream", b2_score: 0.9209, quality_percentile: 0.7768 },
    { ticker: "SPHR", sector: "Communication Services", industry: "Entertainment", b2_score: 0.9100, quality_percentile: 0.5579 },
    { ticker: "IRDM", sector: "Communication Services", industry: "Telecom Services", b2_score: 0.9090, quality_percentile: 0.5305 },
    { ticker: "TXG", sector: "Healthcare", industry: "Health Information Services", b2_score: 0.9087, quality_percentile: 0.6542 },
    { ticker: "TWST", sector: "Healthcare", industry: "Diagnostics & Research", b2_score: 0.9078, quality_percentile: 0.4071 },
    { ticker: "WTTR", sector: "Energy", industry: "Oil & Gas Equipment & Services", b2_score: 0.9056, quality_percentile: 0.4607 },
    { ticker: "EWTX", sector: "Healthcare", industry: "Biotechnology", b2_score: 0.8953, quality_percentile: 0.2642 },
    { ticker: "COCO", sector: "Consumer Defensive", industry: "Beverages - Non-Alcoholic", b2_score: 0.8922, quality_percentile: 0.8192 },
    { ticker: "KALU", sector: "Basic Materials", industry: "Aluminum", b2_score: 0.8900, quality_percentile: 0.4110 },
  ];

  const ts = Date.now().toString(36);
  const targetWeight = 1 / 30;

  // Create securities
  const secIds: Record<string, string> = {};
  for (const h of M1_TICKERS) {
    const { data: sec } = await supabase.from("securities").upsert({
      ticker: h.ticker,
      sector: h.sector,
      industry: h.industry,
      is_active: true,
    }, { onConflict: "ticker" }).select("id").single();
    if (sec) secIds[h.ticker] = sec.id;
  }

  // Create model version
  const { data: mv } = await supabase.from("model_versions").insert({
    model_id: "M1_B2_QUALITY_VETO_N30",
    version: "2026.06.24",
    description: "M1 B2 QUALITY VETO N30 — Decision support, not investment advice. Source: outputs/final/m1_b2_quality_veto_targets.csv",
  }).select("id").single();
  const mvid = mv!.id;

  // Create snapshot as DRAFT
  const { data: snapshot } = await supabase.from("model_snapshots").insert({
    model_version_id: mvid,
    snapshot_id: `m1-b2-${ts}`,
    status: "DRAFT",
    effective_date: "2026-06-23",
    universe_screened: 1070,
    eligible_count: 1070,
    valid_score_count: 1070,
    warnings: JSON.stringify({ notice: "Decision support only — not investment advice" }),
  }).select("id").single();
  const sid = snapshot!.id;

  // Create 30 holdings
  for (let i = 0; i < M1_TICKERS.length; i++) {
    const h = M1_TICKERS[i];
    if (!secIds[h.ticker]) continue;
    await supabase.from("model_snapshot_holdings").insert({
      snapshot_id: sid,
      security_id: secIds[h.ticker],
      rank: i + 1,
      target_weight: targetWeight,
      b2_score: h.b2_score,
      quality_percentile: h.quality_percentile,
      quality_components_ok: 4,
      inclusion_reason: "M1 B2 Quality Veto — unconstrained top 30",
    });
  }

  revalidatePath("/model");
  return { error: null, message: "M1_B2_QUALITY_VETO_N30 generated as DRAFT." };
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

  const { data: existing } = await supabase
    .from("portfolios")
    .select("id")
    .eq("name", "[TEST] Acceptance Portfolio")
    .limit(1);
  if (existing && existing.length > 0) {
    return { error: "Test data already exists. Delete it first." };
  }

  const ts = Date.now().toString(36);
  const idemp = (key: string) => `seed-${ts}-${key}`;

  // Use the official M1_B2 model tickers
  const M1_TICKERS = ["MU", "DOCN", "BE", "VICR", "TTMI", "MXL", "WDC", "SYRE", "POWL", "STRL",
    "AMD", "AGX", "GTX", "MYRG", "FIX", "MTRN", "ELVN", "VRT", "BTSG", "KGS",
    "MOD", "INSW", "SPHR", "IRDM", "TXG", "TWST", "WTTR", "EWTX", "COCO", "KALU"];

  const secIds: Record<string, string> = {};
  for (const t of M1_TICKERS) {
    const { data: sec } = await supabase.from("securities").insert({
      ticker: t,
      sector: "Acceptance Test",
      is_active: true,
    }).select("id").single();
    if (sec) secIds[t] = sec.id;
  }

  // Benchmark observations
  const benchStart = new Date("2025-01-01");
  for (let d = 0; d < 60; d++) {
    const date = new Date(benchStart.getTime() + d * 7 * 86400000).toISOString().split("T")[0];
    await supabase.from("benchmark_observations").insert([
      { ticker: "SPY", observation_date: date, price: 400 + d * 0.5, total_return_index: 100 + d * 0.3 },
      { ticker: "QQQ", observation_date: date, price: 300 + d * 0.8, total_return_index: 100 + d * 0.5 },
    ]);
  }

  // Create portfolio
  const { data: portfolio } = await supabase.from("portfolios").insert({
    owner_id: userId,
    name: "[TEST] Acceptance Portfolio",
    currency: "USD",
    opening_date: "2025-01-01",
    starting_cash: 100000,
    notes: "[TEST] Acceptance test portfolio — not real investment data",
  }).select("id").single();
  if (!portfolio) return { error: "Failed to create portfolio" };
  const pid = portfolio.id;

  // Deposit
  await supabase.from("transactions").insert({
    portfolio_id: pid,
    event_type: "DEPOSIT",
    event_date: "2025-01-01",
    gross_amount: 100000,
    idempotency_key: idemp("deposit"),
    owner_id: userId,
  });

  // Buy transactions using real M1_B2 tickers
  const buys = M1_TICKERS.slice(0, 10).map((t, i) => ({
    ticker: t,
    qty: 10 + i * 5,
    price: 50 + Math.random() * 200,
    gross: 0,
    comm: 3,
    date: "2025-01-05",
  }));
  for (const b of buys) {
    b.gross = Math.round(b.qty * b.price * 100) / 100;
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

  // Price observations
  for (const t of M1_TICKERS) {
    if (!secIds[t]) continue;
    await supabase.from("price_observations").insert({
      security_id: secIds[t],
      observation_date: "2025-03-01",
      close: 50 + Math.random() * 300,
      source: "acceptance-test",
    });
  }

  // Create model version + snapshot
  const { data: mv } = await supabase.from("model_versions").insert({
    model_id: "M1_B2_QUALITY_VETO_N30",
    version: `test-${ts}`,
    description: "[TEST] Acceptance test — not an investment recommendation",
  }).select("id").single();
  const mvid = mv!.id;

  const { data: snapshot } = await supabase.from("model_snapshots").insert({
    model_version_id: mvid,
    snapshot_id: `acceptance-test-${ts}`,
    status: "PUBLISHED",
    effective_date: "2026-06-01",
    universe_screened: 1070,
    eligible_count: 1070,
    valid_score_count: 1070,
    integrity_hash: `test-hash-${ts}`,
    warnings: JSON.stringify({ notice: "[TEST] Acceptance test only — not investment advice" }),
    published_at: new Date().toISOString(),
  }).select("id").single();
  const sid = snapshot!.id;

  // Model holdings using official Top 30
  for (let i = 0; i < M1_TICKERS.length; i++) {
    const t = M1_TICKERS[i];
    if (!secIds[t]) continue;
    await supabase.from("model_snapshot_holdings").insert({
      snapshot_id: sid,
      security_id: secIds[t],
      rank: i + 1,
      target_weight: 1 / M1_TICKERS.length,
      b2_score: 0.9 - (i * 0.005),
      quality_percentile: 85 - (i * 1.5),
      quality_components_ok: 4,
      inclusion_reason: "[TEST] Acceptance test",
    });
  }

  revalidatePath("/dashboard");
  revalidatePath("/portfolios");
  revalidatePath("/model");
  return { error: null, message: "[TEST] Acceptance data created using M1_B2 model tickers." };
}
