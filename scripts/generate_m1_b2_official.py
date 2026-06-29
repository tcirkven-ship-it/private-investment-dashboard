"""Official M1_B2_QUALITY_VETO_N30 generation from committed factor snapshot.
Reads only m1_b2_factor_input.csv (no daily QVP dependency).
Applies Quality Veto + sector/industry caps to produce validated Top 30.
"""
from __future__ import annotations
import json, sys, csv
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest.price_walkforward import write_json

MODEL_ID = "M1_B2_QUALITY_VETO_N30"
INPUT_FILE = ROOT / "outputs/quarterly/m1_b2_factor_input.csv"
Q_FACTORS = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]
QUALITY_VETO_THRESHOLD = 0.10
SECTOR_CAP = 7
INDUSTRY_CAP = 4
TARGET_COUNT = 30
TARGET_WEIGHT = round(100.0 / TARGET_COUNT, 4)

def main():
    output_dir = ROOT / "outputs/quarterly"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_FILE)
    print(f"Input: {len(df)} tickers from {INPUT_FILE.name}")

    for qf in Q_FACTORS:
        if qf not in df.columns:
            df[f"q_{qf}"] = 0
        else:
            df[f"q_{qf}"] = df[qf].notna().astype(int)
    df["Q_components_ok"] = sum(df[f"q_{f}"] for f in Q_FACTORS)

    # Quality Veto: exclude bottom 10% by Q_score
    df = df.dropna(subset=["Q_score"]).copy()
    df["q_rank"] = df["Q_score"].rank(pct=True)
    excluded = df[df["q_rank"] <= QUALITY_VETO_THRESHOLD]
    qualified = df[df["q_rank"] > QUALITY_VETO_THRESHOLD].copy()
    print(f"Quality veto: {len(excluded)} excluded, {len(qualified)} remain")

    # Select top 30 by B2_score with sector/industry caps
    qualified = qualified.sort_values("B2_score", ascending=False)
    selected = []
    sector_counts, industry_counts = {}, {}
    for _, row in qualified.iterrows():
        t = str(row["ticker"]).strip().upper()
        sector = str(row.get("sector", "Unknown"))
        industry = str(row.get("industry", "Unknown"))
        sc = sector_counts.get(sector, 0)
        ic = industry_counts.get(industry, 0)
        if sc >= SECTOR_CAP: continue
        if ic >= INDUSTRY_CAP: continue
        selected.append(row)
        sector_counts[sector] = sc + 1
        industry_counts[industry] = ic + 1
        if len(selected) >= TARGET_COUNT: break

    # Validate
    errors = []
    if len(selected) != TARGET_COUNT: errors.append(f"Expected {TARGET_COUNT}, got {len(selected)}")
    tickers = [str(r["ticker"]).strip().upper() for r in selected]
    if len(set(tickers)) != len(tickers): errors.append("Duplicate tickers")
    for s, c in sector_counts.items():
        if c > SECTOR_CAP: errors.append(f"Sector {s}: {c} > {SECTOR_CAP}")
    for i, c in industry_counts.items():
        if c > INDUSTRY_CAP: errors.append(f"Industry {i}: {c} > {INDUSTRY_CAP}")
    ok = len(errors) == 0

    if not ok:
        for e in errors: print(f"VALIDATION ERROR: {e}")
        return 1
    print(f"VALIDATION PASSED: {len(selected)} holdings, {len(sector_counts)} sectors")

    # Write CSV
    csv_path = output_dir / "m1_b2_quality_veto_targets.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "B2_score", "Q_percentile", "Q_components_ok", "target_pct", "sector", "industry", "is_missing_q"])
        for r in selected:
            t = str(r["ticker"]).strip().upper()
            q_pct = round(float(r["q_rank"]) * 100, 4)
            q_ok = int(r.get("Q_components_ok", 4))
            w.writerow([t, f"{float(r['B2_score']):.4f}", f"{q_pct:.4f}", q_ok, f"{TARGET_WEIGHT:.4f}",
                        str(r.get("sector", "")), str(r.get("industry", "")), "False"])

    # Manifest
    manifest = {
        "model_id": MODEL_ID,
        "generation_mode": "official_factor_snapshot",
        "source_factor_file": str(INPUT_FILE.name),
        "source_snapshot": str(df.iloc[0].get("source_snapshot", "unknown")) if len(df) > 0 else "unknown",
        "input_row_count": len(df),
        "b2_formula": "mean of M12_1, M6_1, TREND200",
        "quality_formula": f"mean of {', '.join(Q_FACTORS)}",
        "quality_veto_threshold": f"{QUALITY_VETO_THRESHOLD*100}%",
        "sector_cap": str(SECTOR_CAP),
        "industry_cap": str(INDUSTRY_CAP),
        "holdings": len(selected),
        "validation_passed": ok,
        "tickers": [str(r["ticker"]).strip().upper() for r in selected],
        "sectors": {str(k): int(v) for k, v in sector_counts.items()},
        "industries": {str(k): int(v) for k, v in industry_counts.items()},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(output_dir / "m1_b2_manifest.json", manifest)

    print(f"\n{MODEL_ID} Generated:")
    print(f"  Holdings: {len(selected)}")
    print(f"  Tickers: {', '.join(tickers[:10])}...")
    print(f"  CSV: {csv_path}")
    print(f"  Manifest: {output_dir / 'm1_b2_manifest.json'}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
