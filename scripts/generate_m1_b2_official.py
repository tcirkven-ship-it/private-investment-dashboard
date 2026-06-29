"""Official M1_B2_QUALITY_VETO_N30 quarterly generation.
Reads the committed factor input file (B2 + Quality scores per ticker),
applies Quality Veto + sector/industry caps, produces validated Top 30.
"""
from __future__ import annotations
import json, sys, csv
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest.price_walkforward import write_json

MODEL_ID = "M1_B2_QUALITY_VETO_N30"
FACTOR_FILE = ROOT / "outputs/quarterly/m1_b2_factor_input.csv"
SECTOR_FILE = ROOT / "outputs/final/current_daily_qvp_ranking.csv"

def main():
    output_dir = ROOT / "outputs/quarterly"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load factor data
    df = pd.read_csv(FACTOR_FILE)
    print(f"Factor input: {len(df)} tickers")

    # Apply Quality Veto: exclude bottom 10% by Q_score
    df = df.dropna(subset=["Q_score"]).copy()
    df["q_rank"] = df["Q_score"].rank(pct=True)
    excluded = df[df["q_rank"] <= 0.10]
    qualified = df[df["q_rank"] > 0.10].copy()
    print(f"Quality veto: {len(excluded)} excluded (bottom 10%), {len(qualified)} remain")

    # Load sector/industry from ranking CSV
    sectors = pd.DataFrame()
    for sp in [SECTOR_FILE]:
        if sp.exists():
            sec = pd.read_csv(sp)
            sectors = sec[["ticker", "sector", "industry"]].drop_duplicates("ticker").set_index("ticker")
            break
    if sectors.empty:
        print("WARNING: No sector/industry data — caps will not be enforced")

    # Select top 30 by B2_score with sector cap 25%, industry cap 15%
    qualified = qualified.sort_values("B2_score", ascending=False)
    selected = []
    sector_counts = {}
    industry_counts = {}
    for _, row in qualified.iterrows():
        ticker = str(row["ticker"]).strip().upper()
        sector = str(sectors.loc[ticker, "sector"]) if ticker in sectors.index else "Unknown"
        industry = str(sectors.loc[ticker, "industry"]) if ticker in sectors.index else "Unknown"
        sc = sector_counts.get(sector, 0)
        ic = industry_counts.get(industry, 0)
        if sc >= 7: continue
        if ic >= 4: continue
        selected.append({
            "ticker": ticker,
            "b2_score": float(row["B2_score"]),
            "quality_percentile": round(float(row["q_rank"]) * 100, 4),
            "sector": sector,
            "industry": industry,
        })
        sector_counts[sector] = sc + 1
        industry_counts[industry] = ic + 1
        if len(selected) >= 30: break

    # Validate
    errors = []
    if len(selected) != 30: errors.append(f"Expected 30, got {len(selected)}")
    tickers = [h["ticker"] for h in selected]
    if len(set(tickers)) != len(tickers): errors.append("Duplicate tickers")
    for s, c in sector_counts.items():
        if c > 7: errors.append(f"Sector cap: {s} has {c} > 7")
    for i, c in industry_counts.items():
        if c > 4: errors.append(f"Industry cap: {i} has {c} > 4")
    ok = len(errors) == 0

    if not ok:
        for e in errors: print(f"VALIDATION ERROR: {e}")
        return 1

    print(f"VALIDATION PASSED: {len(selected)} holdings, {len(sector_counts)} sectors, {len(industry_counts)} industries")

    # Write CSV
    target = round(100.0 / 30, 4)
    csv_path = output_dir / "m1_b2_quality_veto_targets.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "B2_score", "Q_percentile", "Q_components_ok", "target_pct", "sector", "industry", "is_missing_q"])
        for h in selected:
            w.writerow([h["ticker"], f"{h['b2_score']:.4f}", f"{h['quality_percentile']:.4f}",
                        4, f"{target:.4f}", h["sector"], h["industry"], "False"])

    manifest = {
        "model_id": MODEL_ID, "holdings": len(selected),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "validation_passed": ok, "tickers": [h["ticker"] for h in selected],
        "sectors": dict(sector_counts), "industries": dict(industry_counts),
        "source_factor_file": str(FACTOR_FILE.name),
    }
    write_json(manifest, output_dir / "m1_b2_manifest.json")

    print(f"\nM1_B2_QUALITY_VETO_N30 Generated:")
    print(f"  Holdings: {len(selected)}")
    print(f"  Tickers: {', '.join(h['ticker'] for h in selected[:10])}...")
    print(f"  CSV: {csv_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
