import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "outputs/final";
const registryCsv = await fs.readFile("research/experiment_registry.csv", "utf8");
const pre = JSON.parse(await fs.readFile("outputs/experiment_runs/EXP-0009/summary.json", "utf8"));
const holdout = JSON.parse(await fs.readFile("outputs/experiment_runs/EXP-0010/summary.json", "utf8"));
const robust = JSON.parse(await fs.readFile("outputs/experiment_runs/EXP-0010/robustness_audit.json", "utf8"));
const decision = JSON.parse(await fs.readFile("outputs/final/final_decision.json", "utf8"));

const workbook = await Workbook.fromCSV(registryCsv, { sheetName: "Experiment Registry" });
const cover = workbook.worksheets.add("Cover");
const gates = workbook.worksheets.add("Gate Review");
const results = workbook.worksheets.add("Stitched Results");
const candidates = workbook.worksheets.add("Candidate Stability");
const annual = workbook.worksheets.add("Annual Returns");
const sources = workbook.worksheets.add("Sources and Limits");

const navy = "#17365D";
const teal = "#0F766E";
const purple = "#7C3AED";
const paleBlue = "#D9EAF7";
const paleGreen = "#E2F0D9";
const paleRed = "#FCE8E6";
const paleYellow = "#FFF2CC";
const lightGray = "#E7E6E6";

for (const sheet of [cover, gates, results, candidates, annual, sources, workbook.worksheets.getItem("Experiment Registry")]) {
  sheet.showGridLines = false;
}

cover.getRange("A1:F1").merge();
cover.getRange("A1").values = [["Phase One — Final Research Decision"]];
cover.getRange("A2:F2").merge();
cover.getRange("A2").values = [["Recurring-contribution direct-stock strategy | Best-effort free-data generation"]];
cover.getRange("A4:B10").values = [
  ["Decision", decision.decision],
  ["Live active strategy approved", decision.approved_for_live_active_use],
  ["Primary candidate", decision.primary_candidate],
  ["Period", "2010-01-08 to 2026-06-18"],
  ["Final holdout", "2023-01-01 to 2026-06-18 — consumed once"],
  ["Evidence ceiling", decision.evidence_ceiling],
  ["Recommended status", decision.recommended_status],
];
cover.getRange("D4:E10").values = [
  ["Contributed", decision.stitched_metrics.total_contributed_usd],
  ["Strategy ending value", decision.stitched_metrics.strategy_ending_value_usd],
  ["Strategy annualized TWR", decision.stitched_metrics.strategy_annualized_twr],
  ["Strategy XIRR", decision.stitched_metrics.strategy_xirr],
  ["Maximum drawdown", decision.stitched_metrics.strategy_max_drawdown],
  ["Annualized turnover", decision.stitched_metrics.strategy_annualized_turnover],
  ["Holdout active vs QQQ", decision.holdout_metrics.active_twr_vs_qqq],
];
cover.getRange("A12:F12").merge();
cover.getRange("A12").values = [["FAIL means the active strategy is not approved. Attractive point estimates do not override survivorship, QQQ holdout, uncertainty, turnover, stability, and execution failures."]];
cover.getRange("A1:F1").format = { fill: navy, font: { bold: true, color: "#FFFFFF", size: 18 }, rowHeight: 30 };
cover.getRange("A2:F2").format = { fill: paleBlue, font: { italic: true, color: navy }, rowHeight: 22 };
cover.getRange("A4:A10").format = { fill: lightGray, font: { bold: true }, wrapText: true };
cover.getRange("B4:B10").format = { wrapText: true };
cover.getRange("D4:D10").format = { fill: teal, font: { bold: true, color: "#FFFFFF" }, wrapText: true };
cover.getRange("E4:E10").format = { fill: paleGreen, font: { bold: true } };
cover.getRange("E4:E5").format.numberFormat = "$#,##0;[Red]($#,##0);-";
cover.getRange("E6:E7").format.numberFormat = "0.00%;[Red](0.00%);-";
cover.getRange("E8:E10").format.numberFormat = "0.00%;[Red](0.00%);-";
cover.getRange("A12:F12").format = { fill: paleRed, font: { bold: true, color: "#9C0006" }, wrapText: true, rowHeight: 44 };
cover.getRange("A1:F12").format.borders = { preset: "outside", style: "thin", color: "#A6A6A6" };
cover.getRange("A1:A12").format.columnWidth = 26;
cover.getRange("B1:B12").format.columnWidth = 40;
cover.getRange("C1:C12").format.columnWidth = 4;
cover.getRange("D1:D12").format.columnWidth = 28;
cover.getRange("E1:E12").format.columnWidth = 18;
cover.getRange("F1:F12").format.columnWidth = 4;

const gateLabels = {
  twr_advantage_at_least_1pct_vs_spy: "Holdout TWR +1% vs SPY",
  twr_advantage_at_least_1pct_vs_qqq: "Holdout TWR +1% vs QQQ",
  xirr_advantage_at_least_1pct_vs_spy: "Holdout XIRR +1% vs SPY",
  xirr_advantage_at_least_1pct_vs_qqq: "Holdout XIRR +1% vs QQQ",
  positive_stressed_active_vs_spy: "Positive stressed active return vs SPY",
  positive_stressed_active_vs_qqq: "Positive stressed active return vs QQQ",
  volatility_not_above_1_2x_spy: "Volatility <= 1.2x SPY",
  drawdown_not_over_5pct_worse_than_spy: "Drawdown no more than 5% worse than SPY",
  annualized_turnover_at_or_below_100pct: "Annualized turnover <= 100%",
  definitive_data_integrity: "Definitive data integrity",
};
const gateNotes = {
  twr_advantage_at_least_1pct_vs_qqq: "Holdout active TWR was -0.83 pp.",
  xirr_advantage_at_least_1pct_vs_qqq: "Holdout XIRR advantage was -0.50 pp.",
  positive_stressed_active_vs_qqq: "Stressed holdout active TWR was -0.99 pp.",
  annualized_turnover_at_or_below_100pct: "Holdout turnover was 172%.",
  definitive_data_integrity: "Current holdings projected backward; delistings and PIT fundamentals unavailable.",
};
const gateRows = Object.entries(holdout.primary_gates).map(([key, value]) => [gateLabels[key] ?? key, value ? "PASS" : "FAIL", gateNotes[key] ?? ""]);
gates.getRange(`A1:C${gateRows.length + 1}`).values = [["Critical gate", "Status", "Evidence / note"], ...gateRows];
gates.freezePanes.freezeRows(1);
gates.getRange("A1:C1").format = { fill: navy, font: { bold: true, color: "#FFFFFF" }, rowHeight: 30 };
gates.getRange(`A2:C${gateRows.length + 1}`).format = { wrapText: true };
gates.getRange(`A1:C${gateRows.length + 1}`).format.borders = { preset: "inside", style: "thin", color: "#D9E2F3" };
gates.getRange(`B2:B${gateRows.length + 1}`).conditionalFormats.add("containsText", { text: "PASS", format: { fill: paleGreen, font: { bold: true, color: "#006100" } } });
gates.getRange(`B2:B${gateRows.length + 1}`).conditionalFormats.add("containsText", { text: "FAIL", format: { fill: paleRed, font: { bold: true, color: "#9C0006" } } });
gates.getRange("A:A").format.columnWidth = 40;
gates.getRange("B:B").format.columnWidth = 14;
gates.getRange("C:C").format.columnWidth = 66;
gates.tables.add(`A1:C${gateRows.length + 1}`, true, "GateReviewTable");

const resultSources = { Strategy: robust.strategy_metrics, SPY: robust.benchmark_metrics.SPY, QQQ: robust.benchmark_metrics.QQQ };
const resultRows = Object.entries(resultSources).map(([name, metrics]) => [name, metrics.total_contributed, metrics.ending_value, metrics.annualized_twr, metrics.xirr, metrics.annualized_volatility, metrics.max_drawdown, metrics.total_explicit_cost, name === "Strategy" ? metrics.annualized_gross_turnover : null]);
results.getRange("A1:I4").values = [["Portfolio", "Contributed", "Ending value", "Annualized TWR", "XIRR", "Volatility", "Max drawdown", "Explicit costs", "Turnover"], ...resultRows];
results.getRange("A6:C9").values = [
  ["Comparison", "Annualized TWR advantage", "XIRR advantage"],
  ["Strategy vs SPY", robust.comparisons.SPY.annualized_twr_advantage, robust.comparisons.SPY.xirr_advantage],
  ["Strategy vs QQQ", robust.comparisons.QQQ.annualized_twr_advantage, robust.comparisons.QQQ.xirr_advantage],
  ["Holdout strategy vs QQQ", holdout.candidate_results["C03-M"].comparisons.QQQ.annualized_twr_advantage, holdout.candidate_results["C03-M"].comparisons.QQQ.xirr_advantage],
];
results.getRange("A1:I1").format = { fill: teal, font: { bold: true, color: "#FFFFFF" }, rowHeight: 32, wrapText: true };
results.getRange("A6:C6").format = { fill: purple, font: { bold: true, color: "#FFFFFF" } };
results.getRange("B2:C4").format.numberFormat = "$#,##0;[Red]($#,##0);-";
results.getRange("D2:G4").format.numberFormat = "0.00%;[Red](0.00%);-";
results.getRange("H2:H4").format.numberFormat = "$#,##0;[Red]($#,##0);-";
results.getRange("I2:I4").format.numberFormat = "0.0%;[Red](0.0%);-";
results.getRange("B7:C9").format.numberFormat = "0.00%;[Red](0.00%);-";
results.getRange("A1:I4").format.borders = { preset: "inside", style: "thin", color: "#D9E2F3" };
results.getRange("A6:C9").format.borders = { preset: "inside", style: "thin", color: "#D9E2F3" };
results.getRange("A:A").format.columnWidth = 25;
results.getRange("B:I").format.columnWidth = 17;
results.tables.add("A1:I4", true, "StitchedResultsTable");

const candidateRows = Object.keys(pre.candidate_results).map((id) => {
  const preRow = pre.candidate_results[id];
  const holdRow = holdout.candidate_results[id];
  return [id, preRow.comparisons.QQQ.annualized_twr_advantage, holdRow.comparisons.QQQ.annualized_twr_advantage, preRow.comparisons.SPY.annualized_twr_advantage, holdRow.comparisons.SPY.annualized_twr_advantage, preRow.metrics.annualized_gross_turnover, holdRow.metrics.annualized_gross_turnover, preRow.metrics.max_drawdown, holdRow.metrics.max_drawdown];
});
candidates.getRange(`A1:I${candidateRows.length + 1}`).values = [["Candidate", "Pre vs QQQ", "Holdout vs QQQ", "Pre vs SPY", "Holdout vs SPY", "Pre turnover", "Holdout turnover", "Pre max DD", "Holdout max DD"], ...candidateRows];
candidates.freezePanes.freezeRows(1);
candidates.getRange("A1:I1").format = { fill: navy, font: { bold: true, color: "#FFFFFF" }, rowHeight: 34, wrapText: true };
candidates.getRange(`B2:I${candidateRows.length + 1}`).format.numberFormat = "0.00%;[Red](0.00%);-";
candidates.getRange(`A1:I${candidateRows.length + 1}`).format.borders = { preset: "inside", style: "thin", color: "#D9E2F3" };
candidates.getRange("A:A").format.columnWidth = 24;
candidates.getRange("B:I").format.columnWidth = 17;
candidates.tables.add(`A1:I${candidateRows.length + 1}`, true, "CandidateStabilityTable");

const annualRows = robust.calendar_consistency.annual_returns.map((row) => [row.date, row.strategy, row.SPY, row.QQQ, row.active_vs_SPY, row.active_vs_QQQ]);
annual.getRange(`A1:F${annualRows.length + 1}`).values = [["Year", "Strategy", "SPY", "QQQ", "Active vs SPY", "Active vs QQQ"], ...annualRows];
annual.getRange("A1:F1").format = { fill: teal, font: { bold: true, color: "#FFFFFF" }, rowHeight: 30 };
annual.getRange(`B2:F${annualRows.length + 1}`).format.numberFormat = "0.0%;[Red](0.0%);-";
annual.getRange(`A1:F${annualRows.length + 1}`).format.borders = { preset: "inside", style: "thin", color: "#D9E2F3" };
annual.getRange("A:A").format.columnWidth = 12;
annual.getRange("B:F").format.columnWidth = 18;
annual.tables.add(`A1:F${annualRows.length + 1}`, true, "AnnualReturnsTable");

const sourceRows = [
  ["OEF current universe", "2026-06-18", "https://www.ishares.com/us/products/239723/ishares-sp-100-etf", "Current membership projected backward; survivor biased"],
  ["Prices/actions", "Retrieved 2026-06-21", "https://ranaroussi.github.io/yfinance/index.html", "Unofficial personal-use client; no delisting/security master"],
  ["S&P reference", "Through 2026-06-18", "https://fred.stlouisfed.org/series/SP500", "Price-only diagnostic; SPY is investable total-return proxy"],
  ["Nasdaq-100 reference", "Through 2026-06-18", "https://fred.stlouisfed.org/series/NASDAQXNDX", "Theoretical total-return index; QQQ is investable proxy"],
  ["IBKR commissions", "Verified 2026-06-21", "https://www.interactivebrokers.com/en/pricing/commissions-stocks.php?re=amer", "Account/residence eligibility can differ"],
  ["IBKR fractional/MOC", "Verified 2026-06-21", "https://www.interactivebrokers.com/campus/trading-lessons/ibkr-desktop-market-on-close-order/", "Reviewed MOC workflow does not support fractional shares"],
];
sources.getRange(`A1:D${sourceRows.length + 1}`).values = [["Item", "As of", "Source", "Critical limitation"], ...sourceRows];
sources.getRange("A1:D1").format = { fill: navy, font: { bold: true, color: "#FFFFFF" }, rowHeight: 30 };
sources.getRange(`A2:D${sourceRows.length + 1}`).format = { wrapText: true };
sources.getRange(`A1:D${sourceRows.length + 1}`).format.borders = { preset: "inside", style: "thin", color: "#D9E2F3" };
sources.getRange("A:A").format.columnWidth = 26;
sources.getRange("B:B").format.columnWidth = 20;
sources.getRange("C:C").format.columnWidth = 66;
sources.getRange("D:D").format.columnWidth = 58;
sources.tables.add(`A1:D${sourceRows.length + 1}`, true, "SourcesTable");

const registry = workbook.worksheets.getItem("Experiment Registry");
registry.freezePanes.freezeRows(1);
registry.getRange("A1:AJ1").format = { fill: navy, font: { bold: true, color: "#FFFFFF" }, wrapText: true, rowHeight: 42 };
registry.getRange("A2:AJ11").format = { wrapText: true };
registry.getRange("B2:B11").format.numberFormat = "yyyy-mm-dd hh:mm";
registry.getRange("A1:AJ11").format.borders = { preset: "inside", style: "thin", color: "#D9E2F3" };
registry.getRange("A1:AJ11").format.autofitColumns();
registry.getRange("A:A").format.columnWidth = 14;
registry.getRange("B:B").format.columnWidth = 22;
registry.getRange("J:K").format.columnWidth = 40;
registry.getRange("Q:Q").format.columnWidth = 34;
registry.getRange("AB:AC").format.columnWidth = 34;
registry.getRange("AG:AJ").format.columnWidth = 36;
registry.tables.add("A1:AJ11", true, "FinalExperimentRegistryTable");

const coverInspect = await workbook.inspect({ kind: "table", sheetId: "Cover", range: "A1:F12", include: "values,formulas", tableMaxRows: 12, tableMaxCols: 6, maxChars: 5000 });
console.log(coverInspect.ndjson);
const errorInspect = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "final formula error scan" });
console.log(errorInspect.ndjson);

for (const [sheetName, range] of [
  ["Cover", "A1:F12"],
  ["Gate Review", `A1:C${gateRows.length + 1}`],
  ["Stitched Results", "A1:I9"],
  ["Candidate Stability", `A1:I${candidateRows.length + 1}`],
  ["Annual Returns", `A1:F${annualRows.length + 1}`],
  ["Sources and Limits", `A1:D${sourceRows.length + 1}`],
  ["Experiment Registry", "A1:L11"],
]) {
  const preview = await workbook.render({ sheetName, range, scale: 1.25, format: "png" });
  await fs.writeFile(`${outputDir}/workbook_${sheetName.toLowerCase().replaceAll(" ", "_")}.png`, new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(`${outputDir}/phase_one_research_results.xlsx`);
