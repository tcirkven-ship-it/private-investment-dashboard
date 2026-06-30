"use server";

import { createServerSupabase } from "./supabase";
import { revalidatePath } from "next/cache";
import { parse } from "csv-parse/sync";

interface ActionResult { error: string | null; message?: string; holdings?: number; modelId?: string; }

export async function loadNotebookModel(formData: FormData): Promise<ActionResult> {
  const ownerEmail = process.env.OWNER_EMAIL;
  if (!ownerEmail) return { error: "OWNER_EMAIL not configured." };
  if (!process.env.SUPABASE_SERVICE_ROLE_KEY) return { error: "SUPABASE_SERVICE_ROLE_KEY not configured." };

  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user || user.email?.toLowerCase() !== ownerEmail.toLowerCase()) return { error: "Owner access required." };

  const csvFile = formData.get("csv") as File;
  const manifestJson = formData.get("manifest") as string || null;

  if (!csvFile) return { error: "CSV file is required." };

  let csvText: string;
  try { csvText = await csvFile.text(); }
  catch { return { error: "Could not read CSV file." }; }

  // Parse CSV
  let rows: Record<string, unknown>[];
  try {
    rows = parse(csvText, { columns: true, skip_empty_lines: true }) as Record<string, unknown>[];
  } catch { return { error: "CSV parse error. Ensure valid CSV format." }; }

  // Validate exactly 30 rows
  if (rows.length !== 30) return { error: `Expected 30 holdings, found ${rows.length}.` };

  // Validate no duplicate tickers
  const tickers = rows.map((r) => String(r.ticker || "").trim().toUpperCase()).filter(Boolean);
  if (new Set(tickers).size !== 30) return { error: "Duplicate tickers found." };
  if (tickers.length !== 30) return { error: "Some rows have missing tickers." };

  // Validate required columns
  for (const col of ["ticker", "sector", "industry"]) {
    if (!rows[0] || !(col in rows[0])) return { error: `Missing required column: ${col}` };
  }

  // Validate B2_score column exists (case-insensitive)
  const firstRow = rows[0]!;
  const b2Col = Object.keys(firstRow).find(
    (k) => k.toLowerCase() === "b2_score" || k.toLowerCase() === "b2score"
  );
  if (!b2Col) return { error: "CSV missing B2_score column." };

  // Parse manifest if provided
  let manifest: Record<string, unknown> | null = null;
  if (manifestJson) {
    try { manifest = JSON.parse(manifestJson) as Record<string, unknown>; }
    catch { return { error: "Manifest JSON parse error." }; }
    if (manifest.model_id !== "M1_B2_QUALITY_VETO_N30") return { error: `Manifest model_id must be M1_B2_QUALITY_VETO_N30, got ${manifest.model_id}` };
    if (!manifest.as_of_date) return { error: "Manifest missing as_of_date." };
    if (!manifest.generated_at) return { error: "Manifest missing generated_at." };

    const asOf = String(manifest.as_of_date);
    const genDate = new Date(asOf);
    const now = new Date();
    if (isNaN(genDate.getTime())) return { error: `Invalid as_of_date: ${asOf}` };
    if (genDate > now) return { error: `as_of_date (${asOf}) is in the future.` };

    const genAt = new Date(String(manifest.generated_at));
    if (isNaN(genAt.getTime())) return { error: `Invalid generated_at: ${manifest.generated_at}` };
    if (genAt < genDate) return { error: `generated_at (${manifest.generated_at}) is before as_of_date (${asOf}).` };
  }

  const targetWeight = 1 / 30;
  const ts = Date.now().toString(36);
  const today = new Date().toISOString().split("T")[0];

  // Service client for writes
  const { createClient } = await import("@supabase/supabase-js");
  const db = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } },
  );

  // Upsert securities
  const secIds: Record<string, string> = {};
  for (let i = 0; i < tickers.length; i++) {
    const t = tickers[i];
    const { data: created } = await db.from("securities").upsert({
      ticker: t,
      sector: String(rows[i].sector || ""),
      industry: String(rows[i].industry || ""),
      is_active: true,
    }, { onConflict: "ticker" }).select("id").single();
    if (created) secIds[t] = created.id;
    else {
      const { data: existing } = await db.from("securities").select("id").eq("ticker", t).single();
      if (existing) secIds[t] = existing.id;
    }
  }

  // Model version
  let { data: mv } = await db.from("model_versions").select("id").eq("model_id", "M1_B2_QUALITY_VETO_N30").maybeSingle();
  if (!mv) {
    const d = new Date();
    const v = `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
    const { data: newMv } = await db.from("model_versions").insert({
      model_id: "M1_B2_QUALITY_VETO_N30", version: v,
      description: "Notebook-generated official model. Offline Python engine.",
    }).select("id").single();
    if (!newMv) return { error: "Failed to create model version." };
    mv = newMv;
  }

  // Snapshot with metadata
  const asOf = manifest?.as_of_date || today;
  const loadedAt = new Date().toISOString();
  const quarterLabel = manifest?.quarter_label || "";
  const { data: snapshot } = await db.from("model_snapshots").insert({
    model_version_id: mv.id, snapshot_id: `nb-${ts}`, status: "PUBLISHED",
    effective_date: asOf as string,
    universe_screened: 2205, eligible_count: 1070, valid_score_count: rows.length,
    warnings: JSON.stringify({
      generator: "offline notebook official generator",
      generation_mode: "offline_notebook_official_generator",
      source: "notebook",
      as_of_date: asOf,
      generated_at: manifest?.generated_at || "",
      loaded_at: loadedAt,
      quarter_label: quarterLabel,
      input_row_count: rows.length,
    }),
  }).select("id").single();
  if (!snapshot) return { error: "Failed to create snapshot." };

  // Holdings
  for (let i = 0; i < tickers.length; i++) {
    const sid = secIds[tickers[i]];
    if (!sid) continue;
    const r = rows[i];

    const qCol = Object.keys(r).find(
      (k) => k.toLowerCase() === "q_percentile" || k.toLowerCase() === "qpercentile" || k.toLowerCase() === "q_score"
    );
    const qComponentsCol = Object.keys(r).find(
      (k) => k.toLowerCase() === "q_components_ok" || k.toLowerCase() === "qcomponents_ok"
    );

    await db.from("model_snapshot_holdings").upsert({
      snapshot_id: snapshot.id, security_id: sid, rank: i + 1,
      target_weight: targetWeight,
      b2_score: parseFloat(String(r[b2Col] || "0")) || 0,
      quality_percentile: qCol ? (parseFloat(String(r[qCol] || "0")) || 0) : 0,
      quality_components_ok: qComponentsCol ? (parseInt(String(r[qComponentsCol] || "4")) || 4) : 4,
      inclusion_reason: `Notebook-generated. Loaded via app.`,
    }, { onConflict: "snapshot_id,security_id" });
  }

  revalidatePath("/dashboard");
  revalidatePath("/model");
  return { error: null, message: `Loaded ${tickers.length} holdings from notebook.`, holdings: tickers.length, modelId: "M1_B2_QUALITY_VETO_N30" };
}
