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

  // Validate required score columns exist (case-insensitive)
  const firstRow = rows[0]!;
  const b2Col = Object.keys(firstRow).find(
    (k) => k.toLowerCase() === "b2_score" || k.toLowerCase() === "b2score"
  );
  if (!b2Col) return { error: "CSV missing B2_score column." };

  const qCol = Object.keys(firstRow).find(
    (k) => k.toLowerCase() === "q_percentile" || k.toLowerCase() === "qpercentile" || k.toLowerCase() === "q_score" || k.toLowerCase() === "quality_percentile"
  );
  if (!qCol) return { error: "CSV missing Q_percentile column." };

  // Check for metadata columns (warn if missing)
  const metadataMissing: string[] = [];
  for (const col of ["model_id", "as_of_date", "generated_at", "rank", "sector", "industry"]) {
    if (!firstRow || !(col in firstRow || Object.keys(firstRow).some(k => k.toLowerCase() === col.toLowerCase())))
      metadataMissing.push(col);
  }
  const hasB2 = b2Col !== undefined;
  const hasQ = qCol !== undefined;
  if (!hasB2) metadataMissing.push("B2_score");
  if (!hasQ) metadataMissing.push("Q_percentile");

  const csvCompanyCol = Object.keys(firstRow).find(
    (k) => k.toLowerCase() === "company" || k.toLowerCase() === "company_name"
  );
  const hasCompanyCol = csvCompanyCol !== undefined;

  // Parse manifest if provided, otherwise read metadata from CSV columns
  let manifest: Record<string, unknown> | null = null;
  if (manifestJson) {
    try { manifest = JSON.parse(manifestJson) as Record<string, unknown>; }
    catch { return { error: "Manifest JSON parse error." }; }
  }

  // Read metadata from CSV columns (first row)
  const first = rows[0];
  const csvAsOf = String(first?.as_of_date || "");
  const csvGenAt = String(first?.generated_at || "");
  const csvModelId = String(first?.model_id || "");
  const csvQuarter = String(first?.quarter_label || "");
  const csvSource = String(first?.source || "");
  const csvCompany = String(first?.company || "");

  const today = new Date().toISOString().split("T")[0];

  // Validate model_id
  const finalModelId = csvModelId || (manifest?.model_id as string) || "";
  if (finalModelId && finalModelId !== "M1_B2_QUALITY_VETO_N30") return { error: `model_id must be M1_B2_QUALITY_VETO_N30, got ${finalModelId}` };
  const asOf = csvAsOf || (manifest?.as_of_date as string) || today;
  const genAt = csvGenAt || (manifest?.generated_at as string) || "";
  const quarterLabel = csvQuarter || (manifest?.quarter_label as string) || "";
  const source = csvSource || (manifest?.source as string) || "offline notebook official generator";

  // Validate dates
  const genDate = new Date(asOf);
  if (isNaN(genDate.getTime())) return { error: `Invalid as_of_date: ${asOf}` };
  if (genDate > new Date()) return { error: `as_of_date (${asOf}) is in the future.` };
  if (genAt) {
    const ga = new Date(genAt);
    if (isNaN(ga.getTime())) return { error: `Invalid generated_at: ${genAt}` };
  }

  const targetWeight = 1 / 30;
  const ts = Date.now().toString(36);

  // Service client for writes
  const { createClient } = await import("@supabase/supabase-js");
  const db = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } },
  );

  // Upsert securities (include company name if CSV provides it)
  const secIds: Record<string, string> = {};
  for (let i = 0; i < tickers.length; i++) {
    const t = tickers[i];
    const companyName = hasCompanyCol ? String(rows[i][csvCompanyCol] || "") : "";
    const upsertData: Record<string, unknown> = {
      ticker: t,
      sector: String(rows[i].sector || ""),
      industry: String(rows[i].industry || ""),
      is_active: true,
    };
    if (companyName) upsertData.company_name = companyName;
    const { data: created } = await db.from("securities").upsert(
      upsertData, { onConflict: "ticker" }
    ).select("id").single();
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
  const loadedAt = new Date().toISOString();
  const fileName = csvFile.name ? String(csvFile.name) : "uploaded file";
  const { data: snapshot } = await db.from("model_snapshots").insert({
    model_version_id: mv.id, snapshot_id: `nb-${ts}`, status: "PUBLISHED",
    effective_date: asOf as string,
    universe_screened: 2205, eligible_count: 1070, valid_score_count: rows.length,
    warnings: {
      generator: source,
      generation_mode: "offline_notebook_official_generator",
      source: source,
      model_id: finalModelId || "M1_B2_QUALITY_VETO_N30",
      as_of_date: asOf,
      generated_at: genAt,
      loaded_at: loadedAt,
      quarter_label: quarterLabel,
      input_row_count: rows.length,
      file_name: fileName,
      csv_company: csvCompany || undefined,
      metadata_missing: metadataMissing.length > 0 ? metadataMissing : undefined,
      company_warning: !hasCompanyCol ? "Company names missing from CSV — ticker-only display used." : undefined,
    },
  }).select("id").single();
  if (!snapshot) return { error: "Failed to create snapshot." };

  // Holdings
  for (let i = 0; i < tickers.length; i++) {
    const sid = secIds[tickers[i]];
    if (!sid) continue;
    const r = rows[i];

    const qCol = Object.keys(r).find(
      (k) => k.toLowerCase() === "q_percentile" || k.toLowerCase() === "qpercentile" || k.toLowerCase() === "q_score" || k.toLowerCase() === "quality_percentile"
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

  revalidatePath("/model");
  return { error: null, message: `Loaded ${tickers.length} holdings from notebook.`, holdings: tickers.length, modelId: "M1_B2_QUALITY_VETO_N30" };
}
