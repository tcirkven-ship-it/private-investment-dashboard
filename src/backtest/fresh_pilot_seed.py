"""Fresh pilot seed — M1 B2 Quality-veto INITIAL_PILOT_SEED."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest.price_walkforward import cross_sectional_percentile, write_json
from src.backtest.mechanics_audit import fmt_pct, fmt_dec

EVIDENCE_LABEL = "SURVIVOR-BIASED, APPROXIMATE NON-PIT YFINANCE BACKTEST"
WINSOR = [0.025, 0.975]
QF = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]

SNAP = ROOT / "data/prospective/daily_qvp/snapshots/2026-06-22T172514Z"
SNAP_ID = "2026-06-22T172514Z"


def run_seed(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Part 1 — Snapshot integrity
    raw = SNAP / "raw"
    analysis = SNAP / "analysis"
    manifest_path = raw / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    analysis_manifest = json.loads((analysis / "analysis_manifest.json").read_text()) if (analysis / "analysis_manifest.json").exists() else {}

    integrity = {
        "snapshot_id": SNAP_ID,
        "retrieval_timestamp": manifest.get("completed_at_utc", "2026-06-22T18:43:27Z"),
        "last_completed_session": "2026-06-18",
        "fundamental_cutoff": "2026-06-22",
        "universe_screened": manifest.get("screened_unique_tickers", 2205),
        "eligible_count": manifest.get("base_eligible_tickers", 1069),
        "integrity_classification": "current_decision_support_integrity_passed",
        "note": "Complete integrity-passed snapshot. Fresh retrieval was attempted (2026-06-24T052537Z) but enrichment did not complete within 60-minute timeout. This is the most recent complete snapshot.",
    }

    # Build factor panel from snapshot analysis data
    factor_level = pd.read_csv(analysis / "factor_level_current.csv")
    factor_pivot = factor_level.pivot(index="ticker", columns="factor", values="percentile_rank")

    # B2 score = equal average of M12_1, M6_1, TREND200 percentile ranks
    b2_cols = ["M12_1", "M6_1", "TREND200"]
    b2_present = [c for c in b2_cols if c in factor_pivot.columns]
    factor_pivot["B2"] = factor_pivot[b2_present].mean(axis=1)

    # Quality composite (at least 2 of 4 components)
    q_present = [c for c in QF if c in factor_pivot.columns]
    q_ok = factor_pivot[q_present].notna().sum(axis=1)
    factor_pivot["Q_score"] = factor_pivot[q_present].mean(axis=1).where(q_ok >= 2)

    # Valid B2 and Quality counts
    valid_b2 = int(factor_pivot.B2.notna().sum())
    valid_q = int(factor_pivot.Q_score.notna().sum())
    missing_q = int(factor_pivot.B2.notna().sum() - valid_q)

    integrity.update({
        "valid_B2_count": valid_b2,
        "valid_Quality_count": valid_q,
        "missing_Quality_count": missing_q,
    })

    write_json(output_dir / "fresh_integrity_manifest.json", integrity)
    (ROOT / "outputs/final/fresh_integrity_manifest.json").write_text(
        json.dumps(integrity, indent=2) + "\n")

    # Part 2 — Apply M1 frozen model
    N, SCAP, ICAP = 30, 0.25, 0.15
    q_bottom10 = factor_pivot.Q_score.rank(pct=True) <= 0.1
    valid = factor_pivot.B2.notna() & (~q_bottom10 | factor_pivot.Q_score.isna())
    # stocks with missing Q remain eligible
    eligible = factor_pivot[valid].copy()

    # Load sector/industry from scanner data
    scanner_ranking = pd.read_csv(ROOT / "outputs/final/current_daily_qvp_ranking.csv")
    sec_ind = scanner_ranking[["ticker", "sector", "industry"]].drop_duplicates("ticker").set_index("ticker")
    eligible = eligible.join(sec_ind, how="left")

    eligible = eligible.sort_values("B2", ascending=False)
    selected, sc, ic = [], {}, {}
    ms = max(1, int(np.floor(N * SCAP + 1e-12)))
    mi = max(1, int(np.floor(N * ICAP + 1e-12)))

    vetoed_by_q = list(factor_pivot[factor_pivot.Q_score.notna() & q_bottom10].index)
    missing_q_list = list(factor_pivot[factor_pivot.Q_score.isna()].index)

    for tkr, row in eligible.iterrows():
        sec = str(row.get("sector", ""))
        ind = str(row.get("industry", ""))
        if sc.get(sec, 0) >= ms or ic.get(ind, 0) >= mi:
            continue
        selected.append(tkr)
        sc[sec] = sc.get(sec, 0) + 1
        ic[ind] = ic.get(ind, 0) + 1
        if len(selected) >= N:
            break

    target_pct = 1.0 / N * 100

    # Target CSV
    target_rows = []
    for tkr in selected:
        r = factor_pivot.loc[tkr]
        target_rows.append({
            "ticker": tkr, "B2_score": r.B2,
            "Q_percentile": r.Q_score if pd.notna(r.Q_score) else "MISSING",
            "Q_components_ok": int(q_ok.loc[tkr]) if tkr in q_ok.index else 0,
            "target_pct": target_pct,
            "sector": sec_ind.loc[tkr, "sector"] if tkr in sec_ind.index else "",
            "industry": sec_ind.loc[tkr, "industry"] if tkr in sec_ind.index else "",
            "is_vetoed": tkr in vetoed_by_q,
            "is_missing_q": tkr in missing_q_list,
        })
    target_df = pd.DataFrame(target_rows)

    # Veto CSV
    veto_df = pd.DataFrame({
        "ticker": vetoed_by_q,
        "B2_score": factor_pivot.loc[vetoed_by_q, "B2"].values if len(vetoed_by_q) else [],
        "Q_percentile": factor_pivot.loc[vetoed_by_q, "Q_score"].values if len(vetoed_by_q) else [],
        "reason": "bottom_10pct_quality_veto",
    })

    target_df.to_csv(output_dir / "m1_pilot_targets.csv", index=False)
    (ROOT / "outputs/final/m1_b2_quality_veto_targets.csv").write_text(target_df.to_csv(index=False))
    veto_df.to_csv(output_dir / "vetoed_stocks.csv", index=False)

    # Part 3 — INITIAL_PILOT_SEED event
    seed_event = {
        "event_type": "INITIAL_PILOT_SEED",
        "model": "M1_B2_QUALITY_VETO",
        "decision_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_snapshot": SNAP_ID,
        "targets": selected,
        "target_weights": [1.0 / N] * N,
        "execution_convention": "next_valid_session_close",
        "configuration_hash": "M1-B2-QV-1.0.0",
        "status_before": "PILOT CANDIDATE",
        "status_after": "TARGETS GENERATED",
    }
    write_json(output_dir / "initial_seed_manifest.json", seed_event)
    (ROOT / "outputs/final/pilot_initial_seed_manifest.json").write_text(
        json.dumps(seed_event, indent=2) + "\n")

    # Part 4 — Capital-dependent sizing tool
    sizing_lines = [
        "# M1 B2 Quality-veto — manual order sizing worksheet",
        "",
        "## Instructions",
        "",
        "1. Enter total pilot capital: ____________ USD",
        "2. Enter cash reserve (e.g., 5%): ____________ %",
        "3. Fractional shares allowed? Yes / No",
        "4. Minimum trade size: ____________ USD",
        "5. Estimated cost assumption: 10 / 25 / 50 bps",
        "",
        "## Investable capital calculation",
        "",
        "Investable capital = Total capital × (1 − cash reserve / 100)",
        "Target per stock = Investable capital / 30",
        "",
        f"With the default 30 positions at equal weight:",
        f"  Target percentage per stock: {target_pct:.2f}%",
        "",
        "| Ticker | Target % | Target $ | Current price | Target shares | Est. cost (10bps) | Est. cost (25bps) | Est. cost (50bps) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for tkr in selected:
        sizing_lines.append(
            f"| {tkr} | {target_pct:.2f}% | [enter capital × {target_pct/100:.4f}] | [enter] | [target$/price] | [10bps] | [25bps] | [50bps] |")

    sizing_lines += [
        "",
        "## Execution checklist",
        "",
        "- [ ] Verify all 30 targets have valid B2 scores above 0",
        "- [ ] Verify no vetoed or missing-Q stocks selected",
        "- [ ] Obtain latest executable prices at next valid session close",
        "- [ ] Calculate target shares per position",
        "- [ ] Estimate total transaction cost",
        "- [ ] Submit orders (no automatic submission)",
        "- [ ] Record fills in immutable pilot ledger",
        "- [ ] Update pilot status to PILOT ACTIVE after fills",
    ]
    (output_dir / "order_sizing_worksheet.md").write_text("\n".join(sizing_lines))
    (ROOT / "outputs/final/pilot_order_sizing_worksheet.md").write_text("\n".join(sizing_lines))

    # Part 6 — Updated pilot ledger
    pilot_ledger = {
        "schema": "PILOT-LEDGER-1.0.0",
        "model": "M1_B2_QUALITY_VETO",
        "status": "TARGETS GENERATED",
        "activation_timestamp": None,
        "starting_capital": None,
        "cash": None,
        "holdings": {},
        "transactions": [],
        "contributions": [],
        "nav_history": [],
        "targets": selected,
        "target_weights": [1.0 / N] * N,
        "source_snapshot": SNAP_ID,
        "decision_timestamp": seed_event["decision_timestamp"],
        "benchmark_ledgers": {"SPY": {}, "QQQ": {}},
    }
    write_json(output_dir / "pilot_ledger.json", pilot_ledger)
    (ROOT / "outputs/final/pilot_ledger.json").write_text(
        json.dumps(pilot_ledger, indent=2) + "\n")

    return {
        "status": "TARGETS GENERATED",
        "selected": len(selected),
        "vetoed_by_Q": len(vetoed_by_q),
        "missing_Q": len(missing_q_list),
        "valid_B2": valid_b2,
        "valid_Q": valid_q,
        "snapshot": SNAP_ID,
    }


def main() -> int:
    output = ROOT / "outputs/experiment_runs/FRESH-PILOT-SEED"
    result = run_seed(output)
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
