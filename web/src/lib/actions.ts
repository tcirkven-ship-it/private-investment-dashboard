"use server";

import { createServerSupabase } from "./supabase";
import { revalidatePath } from "next/cache";
import { loadHoldings } from "./route-loaders";
import { parse } from "csv-parse/sync";
import { readFileSync, existsSync } from "fs";
import { resolve } from "path";

const YH_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/";

type RefreshResult = { ok: number; failed: string[]; errors: string[] };

export interface ActionResult {
  error: string | null;
}

const M1_CSV_PATH = resolve(process.cwd(), "data", "m1_b2_quality_veto_targets.csv");

type M1Row = { ticker: string; sector: string; industry: string; b2_score: number; quality_percentile: number };

function parseM1B2CSV(): { rows: M1Row[]; error?: string } {
  if (!existsSync(M1_CSV_PATH)) {
    return { rows: [], error: `File not found: ${M1_CSV_PATH}. Ensure the research output exists.` };
  }
  try {
    const raw = readFileSync(M1_CSV_PATH, "utf-8");
    const records = parse(raw, { columns: true, skip_empty_lines: true }) as Record<string, string>[];
    if (records.length !== 30) return { rows: [], error: `Expected 30 rows in CSV, found ${records.length}` };
    const rows: M1Row[] = [];
    const seen = new Set<string>();
    for (const r of records) {
      const t = (r.ticker || "").trim().toUpperCase();
      if (!t) return { rows: [], error: "Missing ticker in CSV row" };
      if (seen.has(t)) return { rows: [], error: `Duplicate ticker: ${t}` };
      seen.add(t);
      rows.push({
        ticker: t,
        sector: (r.sector || "").trim(),
        industry: (r.industry || "").trim(),
        b2_score: parseFloat(r.B2_score || "0"),
        quality_percentile: parseFloat(r.Q_percentile || "0"),
      });
    }
    return { rows };
  } catch (e) {
    return { rows: [], error: `CSV parse error: ${e instanceof Error ? e.message : "Unknown"}` };
  }
}

export async function importM1B2Model(): Promise<ActionResult & { message?: string }> {
  const ownerEmail = process.env.OWNER_EMAIL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  // Diagnostic: env present without values
  console.log("OWNER_EMAIL present:", ownerEmail ? "yes" : "no");
  console.log("SUPABASE_SERVICE_ROLE_KEY present:", serviceKey ? "yes" : "no");

  if (!ownerEmail) return { error: "OWNER_EMAIL env var not configured." };
  if (!serviceKey) return { error: "SUPABASE_SERVICE_ROLE_KEY env var not configured." };

  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return { error: "Not authenticated. Please sign in again." };

  console.log("current user present:", "yes");
  console.log("current user email matches owner:", user.email?.toLowerCase() === ownerEmail.toLowerCase() ? "yes" : "no");

  if (user.email?.toLowerCase() !== ownerEmail.toLowerCase()) {
    return { error: "Owner access required." };
  }

  const parsed = parseM1B2CSV();
  if (parsed.error) return { error: parsed.error };

  // Service client for model writes (RLS bypass)
  const { createClient } = await import("@supabase/supabase-js");
  const db = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    serviceKey,
    { auth: { autoRefreshToken: false, persistSession: false } },
  );

  const rows = parsed.rows;
  const ts = Date.now().toString(36);
  const targetWeight = 1 / 30;

  // Upsert securities
  const secIds: Record<string, string> = {};
  for (const r of rows) {
    const { data: created } = await db.from("securities").upsert({
      ticker: r.ticker,
      sector: r.sector,
      industry: r.industry,
      is_active: true,
    }, { onConflict: "ticker" }).select("id").single();
    if (created) secIds[r.ticker] = created.id;
    else {
      const { data: existing } = await db.from("securities").select("id").eq("ticker", r.ticker).single();
      if (existing) secIds[r.ticker] = existing.id;
    }
  }

  // Create new DRAFT snapshot (preserve history)
  let { data: mv } = await db.from("model_versions").select("id").eq("model_id", "M1_B2_QUALITY_VETO_N30").maybeSingle();
  if (!mv) {
    const d = new Date();
    const v = `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
    const { data: newMv, error: mvErr } = await db.from("model_versions").insert({
      model_id: "M1_B2_QUALITY_VETO_N30",
      version: v,
      description: "Decision support only. Not investment advice. Source: m1_b2_quality_veto_targets.csv",
    }).select("id").single();
    if (mvErr) return { error: `Failed to create model version: ${mvErr.message}` };
    if (!newMv) return { error: "Failed to create model version" };
    mv = newMv;
  }

  // Create DRAFT snapshot
  const { data: snapshot, error: snapErr } = await db.from("model_snapshots").insert({
    model_version_id: mv.id,
    snapshot_id: `m1b2-${ts}`,
    status: "DRAFT",
    effective_date: new Date().toISOString().split("T")[0],
    universe_screened: 2205,
    eligible_count: 1070,
    valid_score_count: 1034,
    warnings: JSON.stringify({ source_file: "m1_b2_quality_veto_targets.csv", ticker_count: rows.length }),
  }).select("id").single();
  if (snapErr) return { error: `Failed to create snapshot: ${snapErr.message}` };
  if (!snapshot) return { error: "Failed to create snapshot" };
  const sid = snapshot.id;

  // Insert 30 holdings
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i];
    const secId = secIds[r.ticker];
    if (!secId) continue;
    await db.from("model_snapshot_holdings").upsert({
      snapshot_id: sid,
      security_id: secId,
      rank: i + 1,
      target_weight: targetWeight,
      b2_score: r.b2_score,
      quality_percentile: r.quality_percentile,
      quality_components_ok: 4,
      inclusion_reason: "M1 B2 Quality Veto. Source: m1_b2_quality_veto_targets.csv",
    }, { onConflict: "snapshot_id,security_id" });
  }

  revalidatePath("/dashboard");
  revalidatePath("/model");
  return { error: null, message: `M1_B2_QUALITY_VETO_N30 generated with ${rows.length} stocks from research output.` };
}

export async function upsertPrice(formData: FormData): Promise<ActionResult> {
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user?.id) return { error: "Not authenticated" };

  const ticker = (formData.get("ticker") as string)?.toUpperCase().trim();
  const date = formData.get("date") as string;
  const close = parseFloat(formData.get("close") as string);
  if (!ticker || !date || isNaN(close)) return { error: "Ticker, date, and price are required" };

  // Use service client for price writes (RLS may not allow owner insert yet)
  const { createClient } = await import("@supabase/supabase-js");
  const db = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } },
  );

  const { data: sec } = await db.from("securities").select("id").eq("ticker", ticker).maybeSingle();
  if (!sec) return { error: `Security ${ticker} not found. Generate the Quarterly Top 30 first or add the security.` };

  const { error } = await db.from("price_observations").upsert({
    security_id: sec.id,
    observation_date: date,
    close,
    source: "manual",
  }, { onConflict: "security_id,observation_date" });

  if (error) return { error: error.message };
  revalidatePath("/portfolios");
  revalidatePath("/dashboard");
  return { error: null };
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

  // Recalculate gross for BUY/SELL from quantity × price (do not trust client)
  const calcGross = ["BUY", "SELL"].includes(eventType) ? quantity * price : grossAmount;

  const payload: Record<string, unknown> = {
    portfolio_id: portfolioId,
    event_type: eventType,
    event_date: eventDate,
    gross_amount: calcGross,
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

  // Delete transactions first, then portfolio
  const { error: txErr } = await supabase.from("transactions").delete().eq("portfolio_id", id);
  if (txErr) return { error: `Failed to delete transactions: ${txErr.message}` };

  const { error } = await supabase.from("portfolios").delete().eq("id", id).eq("owner_id", user.id);
  if (error) return { error: error.message };

  revalidatePath("/portfolios");
  revalidatePath("/dashboard");
  return { error: null };
}

export async function recordValuationSnapshot(portfolioId: string): Promise<ActionResult & { nav?: number; date?: string }> {
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user?.id) return { error: "Not authenticated" };

  const result = await loadHoldings(portfolioId);
  if (result.state.holdings.size > 0) {
    const h = [...result.state.holdings.values()];
    const missing = h.some((x) => x.market_value === undefined || x.market_value === null);
    if (missing) return { error: "Cannot record snapshot: some holdings lack current prices. Add prices first." };
  }

  const today = new Date().toISOString().split("T")[0];
  const { createClient } = await import("@supabase/supabase-js");
  const db = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } },
  );

  const { error } = await db.from("portfolio_valuations").upsert({
    portfolio_id: portfolioId,
    valuation_date: today,
    total_value: result.nav,
    cash_balance: result.state.cash,
    total_deposits: result.state.total_deposits,
    total_withdrawals: result.state.total_withdrawals,
  }, { onConflict: "portfolio_id,valuation_date" });

  if (error) return { error: error.message };
  revalidatePath(`/portfolios/${portfolioId}/performance`);
  return { error: null, nav: result.nav, date: today };
}

export async function refreshClosingPrices(): Promise<ActionResult & { message?: string; ok?: number; failed?: number }> {
  const ownerEmail = process.env.OWNER_EMAIL;
  if (!ownerEmail) return { error: "OWNER_EMAIL not configured." };

  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user || user.email?.toLowerCase() !== ownerEmail.toLowerCase()) return { error: "Owner access required." };
  if (!process.env.SUPABASE_SERVICE_ROLE_KEY) return { error: "SUPABASE_SERVICE_ROLE_KEY not configured." };

  // Collect tickers: Top 30 model holdings + portfolio holdings
  const [{ data: modelHoldings }, { data: securities }] = await Promise.all([
    supabase.from("model_snapshots").select("id").order("created_at", { ascending: false }).limit(1).maybeSingle(),
    supabase.from("securities").select("ticker, id"),
  ]);
  const tickers: string[] = [];
  const secMap = new Map<string, string>();
  if (securities) for (const s of securities) { secMap.set(s.ticker, s.id); tickers.push(s.ticker); }

  // Also add SPY, QQQ for benchmarks
  if (!tickers.includes("SPY")) tickers.push("SPY");
  if (!tickers.includes("QQQ")) tickers.push("QQQ");
  const uniqueTickers = [...new Set(tickers)];

  const today = new Date().toISOString().split("T")[0];
  const { createClient } = await import("@supabase/supabase-js");
  const db = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!, { auth: { autoRefreshToken: false, persistSession: false } });

  let ok = 0;
  const failed: string[] = [];
  const errors: string[] = [];

  for (const t of uniqueTickers) {
    try {
      const resp = await fetch(`${YH_CHART_URL}${encodeURIComponent(t)}?range=5d&interval=1d`);
      if (!resp.ok) { failed.push(t); errors.push(`HTTP ${resp.status}`); continue; }
      const json = await resp.json();
      const result = json?.chart?.result?.[0];
      const close = result?.indicators?.quote?.[0]?.close?.slice(-1)[0];
      if (!close) { failed.push(t); errors.push("No close price"); continue; }
      const secId = secMap.get(t);
      if (!secId) { failed.push(t); errors.push("No security_id"); continue; }
      const { error } = await db.from("price_observations").upsert({
        security_id: secId, observation_date: today, close, source: "yahoo-auto",
      }, { onConflict: "security_id,observation_date" });
      if (error) { failed.push(t); errors.push(error.message); }
      else ok++;
    } catch (e) { failed.push(t); errors.push(e instanceof Error ? e.message : "Unknown"); }
  }

  revalidatePath("/dashboard"); revalidatePath("/portfolios"); revalidatePath("/model");
  return { error: null, message: `Prices refreshed: ${ok}. Failed: ${failed.length}`, ok, failed: failed.length };
}

export async function deleteAllAppData(
  confirm?: boolean,
): Promise<ActionResult & { counts?: Record<string, number> }> {
  const ownerEmail = process.env.OWNER_EMAIL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!ownerEmail) return { error: "OWNER_EMAIL env var not configured." };
  if (!serviceKey) return { error: "SUPABASE_SERVICE_ROLE_KEY env var not configured." };

  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return { error: "Not authenticated." };
  if (user.email?.toLowerCase() !== ownerEmail.toLowerCase()) {
    return { error: "Owner access required." };
  }

  const { createClient } = await import("@supabase/supabase-js");
  const db = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    serviceKey,
    { auth: { autoRefreshToken: false, persistSession: false } },
  );

  const tables = [
    "owner_decisions",
    "rebalance_lines",
    "rebalance_events",
    "model_publication_events",
    "portfolio_valuations",
    "transactions",
    "model_snapshot_holdings",
    "model_snapshots",
    "model_versions",
    "price_observations",
    "benchmark_observations",
    "data_imports",
    "audit_events",
    "portfolios",
    "securities",
    "app_settings",
  ];

  const counts: Record<string, number> = {};

  for (const table of tables) {
    const { count, error: countErr } = await db
      .from(table)
      .select("*", { count: "exact", head: true });
    if (!countErr) {
      counts[table] = count ?? 0;
    } else {
      counts[table] = -1;
    }
  }

  if (!confirm) {
    return { error: null, counts };
  }

  for (const table of tables) {
    const { error: delErr } = await db.from(table).delete().neq("id", "00000000-0000-0000-0000-000000000000");
    if (delErr) {
      return { error: `Failed to delete from ${table}: ${delErr.message}`, counts };
    }
  }

  revalidatePath("/dashboard");
  revalidatePath("/portfolios");
  revalidatePath("/model");
  revalidatePath("/compare");
  revalidatePath("/settings");
  return { error: null, counts };
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
