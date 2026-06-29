"""Official M1_B2_QUALITY_VETO_N30 quarterly generation wrapper.
Runs fresh_pilot_seed_v2.py logic against the latest committed snapshot.
"""
from __future__ import annotations
import json, sys, os, csv
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest.price_walkforward import write_json

QF = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]
EVIDENCE_LABEL = "SURVIVOR-BIASED, APPROXIMATE NON-PIT YFINANCE BACKTEST"

def find_latest_snapshot():
    """Find the latest committed snapshot in data/prospective/daily_qvp/snapshots."""
    snap_dir = ROOT / "data/prospective/daily_qvp/snapshots"
    dirs = sorted([d for d in snap_dir.iterdir() if d.is_dir() and (d / "analysis").exists()],
                  key=lambda d: d.name, reverse=True)
    if not dirs:
        raise FileNotFoundError(f"No valid snapshots found in {snap_dir}")
    return dirs[0]

def load_factor_panel(snap_path):
    fl = pd.read_csv(snap_path / "analysis" / "factor_level_current.csv")
    fl.rename(columns={"symbol": "ticker"}, inplace=True, errors="ignore")
    fp = fl.pivot_table(index="ticker", columns="factor", values="score", aggfunc="first").copy()
    fp["B2"] = fp[["M12_1", "M6_1", "TREND200"]].mean(axis=1)
    fp["Q_score"] = fp[QF].mean(axis=1)
    return fp

def apply_quality_veto(fp):
    fp = fp.dropna(subset=["B2", "Q_score"]).copy()
    q_bottom10 = fp["Q_score"].rank(pct=True) <= 0.1
    print(f"Quality veto: {q_bottom10.sum()} stocks in bottom 10% excluded")
    return fp[~q_bottom10]

def load_sector_industry():
    """Try to load sector/industry from available sources."""
    ranking_paths = [
        ROOT / "outputs/daily_qvp_runs/2026-06-24T080500Z/ranking.csv",
        ROOT / "outputs/final/current_daily_qvp_ranking.csv",
    ]
    for rp in ranking_paths:
        if rp.exists():
            df = pd.read_csv(rp)
            return df[["ticker", "sector", "industry"]].drop_duplicates("ticker").set_index("ticker")
    return pd.DataFrame()

def select_top30(fp, sec_ind):
    """Apply sector cap 25%, industry cap 15%, select top 30 by B2."""
    eligible = fp.sort_values("B2", ascending=False).copy()
    selected, sector_counts, industry_counts = [], {}, {}
    for ticker, row in eligible.iterrows():
        sector = sec_ind.loc[ticker, "sector"] if ticker in sec_ind.index else "Unknown"
        industry = sec_ind.loc[ticker, "industry"] if ticker in sec_ind.index else "Unknown"
        sc = sector_counts.get(sector, 0)
        ic = industry_counts.get(industry, 0)
        if sc >= 7: continue
        if ic >= 4: continue
        selected.append({"ticker": ticker, "b2_score": row["B2"], "quality_score": row["Q_score"],
                         "sector": sector, "industry": industry})
        sector_counts[sector] = sc + 1
        industry_counts[industry] = ic + 1
        if len(selected) >= 30: break
    return selected

def validate(selected):
    """Validate output meets all M1_B2 requirements."""
    errors = []
    if len(selected) != 30: errors.append(f"Expected 30 holdings, got {len(selected)}")
    tickers = [h["ticker"] for h in selected]
    if len(set(tickers)) != len(tickers): errors.append("Duplicate tickers")
    for h in selected:
        if not h["ticker"]: errors.append("Missing ticker")
    # Check sector cap
    from collections import Counter
    sc = Counter(h["sector"] for h in selected)
    for s, c in sc.items():
        if c > 7: errors.append(f"Sector {s} has {c} > max 7 (25% cap)")
    ic = Counter(h["industry"] for h in selected)
    for i, c in ic.items():
        if c > 4: errors.append(f"Industry {i} has {c} > max 4 (15% cap)")
    if errors:
        for e in errors: print(f"VALIDATION ERROR: {e}")
        return False
    print(f"VALIDATION: {len(selected)} holdings, {len(sc)} sectors, {len(ic)} industries — PASSED")
    return True

def main():
    output_dir = ROOT / "outputs/quarterly"
    output_dir.mkdir(parents=True, exist_ok=True)

    snap = find_latest_snapshot()
    print(f"Snapshot: {snap.name}")

    fp = load_factor_panel(snap)
    fp = apply_quality_veto(fp)
    sec_ind = load_sector_industry()
    selected = select_top30(fp, sec_ind)
    ok = validate(selected)

    # Write output
    target_pct = round(100.0 / max(len(selected), 1), 4)
    csv_path = output_dir / "m1_b2_quality_veto_targets.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "B2_score", "Q_percentile", "Q_components_ok", "target_pct", "sector", "industry", "is_missing_q"])
        for h in selected:
            h_row = fp.loc[h["ticker"]] if h["ticker"] in fp.index else pd.Series()
            q_comp = sum(1 for q in QF if h_row.get(q, 0) > 0)
            q_pct = round((h["quality_score"] * 100), 4)
            w.writerow([h["ticker"], round(h["b2_score"], 4), q_pct, q_comp, target_pct,
                        h["sector"], h["industry"], "False"])

    # Metadata
    manifest = {
        "model_id": "M1_B2_QUALITY_VETO_N30",
        "snapshot": snap.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "holdings": len(selected),
        "validation_passed": ok,
        "tickers": [h["ticker"] for h in selected],
        "evidence_label": EVIDENCE_LABEL
    }
    write_json(manifest, output_dir / "m1_b2_manifest.json")

    print(f"\nOutput: {csv_path} ({len(selected)} holdings)")
    print(f"Tickers: {', '.join(h['ticker'] for h in selected[:5])}...")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
