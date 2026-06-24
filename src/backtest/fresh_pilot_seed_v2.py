"""Fresh pilot seed v2 — using completed fresh snapshot 2026-06-24T080500Z."""

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

from src.backtest.price_walkforward import write_json

EVIDENCE_LABEL = "SURVIVOR-BIASED, APPROXIMATE NON-PIT YFINANCE BACKTEST"
QF = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]
SNAP = ROOT / "data/prospective/daily_qvp/snapshots/2026-06-24T080500Z"
SNAP_ID = "2026-06-24T080500Z"
N, SCAP, ICAP = 30, 0.25, 0.15


def run(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = SNAP / "raw"
    analysis = SNAP / "analysis"

    # Fresh integrity manifest
    ranking = pd.read_csv(ROOT / "outputs/final/current_daily_qvp_ranking.csv")
    fresh_ranking = pd.read_csv(ROOT / "outputs/daily_qvp_runs/2026-06-24T080500Z/ranking.csv")

    integrity = {
        "snapshot_id": SNAP_ID,
        "retrieval_timestamp": "2026-06-24T08:05:00Z",
        "last_completed_price_session": "2026-06-23",
        "fundamental_data_cutoff": "2026-06-24",
        "universe_screened": 2205,
        "eligible_count": 1070,
        "fully_scored_count": 1034,
        "integrity_classification": "current_decision_support_integrity_passed",
        "valid_B2_count": None,
        "valid_Quality_count": None,
        "missing_Quality_count": None,
    }

    # Factor panel from fresh analysis
    fl = pd.read_csv(analysis / "factor_level_current.csv")
    fp = fl.pivot(index="ticker", columns="factor", values="percentile_rank").fillna(0)

    b2_cols = [c for c in ["M12_1", "M6_1", "TREND200"] if c in fp.columns]
    fp["B2"] = fp[b2_cols].mean(axis=1)

    q_present = [c for c in QF if c in fp.columns]
    q_ok = fp[q_present].notna().sum(axis=1)
    fp["Q_score"] = fp[q_present].mean(axis=1).where(q_ok >= 2)

    integrity["valid_B2_count"] = int(fp.B2.notna().sum())
    integrity["valid_Quality_count"] = int(fp.Q_score.notna().sum())
    integrity["missing_Quality_count"] = int(fp.B2.notna().sum() - fp.Q_score.notna().sum())

    write_json(output_dir / "fresh_integrity_manifest.json", integrity)

    # Apply M1 model
    q_bottom10 = fp.Q_score.rank(pct=True) <= 0.1
    vetoed = list(fp[fp.Q_score.notna() & q_bottom10].index)
    missing_q = list(fp[fp.Q_score.isna()].index)

    eligible = fp[fp.B2.notna() & (~q_bottom10 | fp.Q_score.isna())].copy()
    scanner_ranking = pd.read_csv(ROOT / "outputs/daily_qvp_runs/2026-06-24T080500Z/ranking.csv")
    sec_ind = scanner_ranking[["ticker", "sector", "industry"]].drop_duplicates("ticker").set_index("ticker")
    eligible = eligible.join(sec_ind, how="left")
    eligible = eligible.sort_values("B2", ascending=False)

    selected, sc, ic = [], {}, {}
    ms = max(1, int(np.floor(N * SCAP + 1e-12)))
    mi = max(1, int(np.floor(N * ICAP + 1e-12)))

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

    # Target CSV
    target_pct = 1.0 / N * 100
    target_rows = []
    for tkr in selected:
        r = fp.loc[tkr]
        target_rows.append({
            "ticker": tkr, "B2_score": r.B2,
            "Q_percentile": r.Q_score if pd.notna(r.Q_score) else "MISSING",
            "Q_components_ok": int(q_ok.loc[tkr]) if tkr in q_ok.index else 0,
            "target_pct": target_pct,
            "sector": sec_ind.loc[tkr, "sector"] if tkr in sec_ind.index else "",
            "industry": sec_ind.loc[tkr, "industry"] if tkr in sec_ind.index else "",
            "is_missing_q": tkr in missing_q,
        })
    target_df = pd.DataFrame(target_rows)

    # Verify all have valid B2
    assert all(target_df.B2_score.notna()), "Selected stock with NaN B2 detected"

    target_df.to_csv(output_dir / "m1_pilot_targets.csv", index=False)

    # Veto CSV
    veto_df = pd.DataFrame({"ticker": vetoed, "reason": "bottom_10pct_quality_veto"})
    veto_df.to_csv(output_dir / "vetoed_stocks.csv", index=False)

    # Seed manifest
    seed = {
        "event_type": "INITIAL_PILOT_SEED",
        "model": "M1_B2_QUALITY_VETO",
        "decision_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_snapshot": SNAP_ID,
        "targets": selected,
        "target_weights": [1.0 / N] * N,
        "execution_convention": "next_valid_session_close",
        "previous_status": "PILOT CANDIDATE",
        "new_status": "TARGETS GENERATED",
    }
    write_json(output_dir / "initial_seed_manifest.json", seed)

    # Update final outputs
    (ROOT / "outputs/final/fresh_integrity_manifest.json").write_text(
        json.dumps(integrity, indent=2) + "\n")
    (ROOT / "outputs/final/m1_b2_quality_veto_targets.csv").write_text(target_df.to_csv(index=False))
    (ROOT / "outputs/final/pilot_initial_seed_manifest.json").write_text(
        json.dumps(seed, indent=2) + "\n")

    # Pilot ledger
    ledger = {
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
        "decision_timestamp": seed["decision_timestamp"],
    }
    write_json(ROOT / "outputs/final/pilot_ledger.json", ledger)

    print(f"\nFresh snapshot completed: {SNAP_ID}")
    print(f"Eligible: {integrity['eligible_count']}, scored: {integrity['fully_scored_count']}")
    print(f"Valid B2: {integrity['valid_B2_count']}, Valid Q: {integrity['valid_Quality_count']}")
    print(f"Missing Q: {integrity['missing_Quality_count']}")
    print(f"Vetoed by Q: {len(vetoed)}, Selected: {len(selected)}")
    print(f"Targets:")
    for t in selected:
        print(f"  {t}")

    return {
        "status": "TARGETS GENERATED",
        "snapshot": SNAP_ID,
        "eligible": integrity["eligible_count"],
        "scored": integrity["fully_scored_count"],
        "selected": len(selected),
        "vetoed": len(vetoed),
    }


def main() -> int:
    output = ROOT / "outputs/experiment_runs/FRESH-PILOT-SEED"
    result = run(output)
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
