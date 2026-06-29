"""Official M1_B2_QUALITY_VETO_N30 quarterly generation.
Reads the committed daily QVP ranking CSV (1070+ stocks with scores, sectors, industries).
Applies Quality Veto + sector/industry caps to produce the official Top 30.
"""
from __future__ import annotations
import json, sys, os, csv
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest.price_walkforward import write_json

EVIDENCE_LABEL = "SURVIVOR-BIASED, APPROXIMATE NON-PIT YFINANCE BACKTEST — COMMITTED SNAPSHOT DATA"
MODEL_ID = "M1_B2_QUALITY_VETO_N30"

def load_ranking():
    """Load the committed ranking CSV with all scores, sectors, industries."""
    paths = [
        ROOT / "outputs/final/current_daily_qvp_ranking.csv",
        ROOT / "outputs/daily_qvp_runs/2026-06-24T080500Z/ranking.csv",
    ]
    for p in paths:
        if p.exists():
            df = pd.read_csv(p)
            print(f"Loaded ranking: {p.name} ({len(df)} stocks)")
            return df
    raise FileNotFoundError("No ranking CSV found. Expected outputs/final/current_daily_qvp_ranking.csv")

def apply_quality_veto(df):
    """Exclude bottom 10% by quality_score."""
    df = df.dropna(subset=["quality_score"]).copy()
    df["q_rank"] = df["quality_score"].rank(pct=True)
    excluded = df[df["q_rank"] <= 0.10]
    qualified = df[df["q_rank"] > 0.10].copy()
    print(f"Quality veto: {len(excluded)} excluded (bottom 10%), {len(qualified)} remain")
    return qualified

def apply_caps(df_score_col="YF-QVP_percentile"):
    """Select top 30 by score with sector cap 25%, industry cap 15%."""
    def run(qualified, score_col):
        qualified = qualified.sort_values(score_col, ascending=False)
        selected = []
        sector_counts = {}
        industry_counts = {}
        for _, row in qualified.iterrows():
            ticker = str(row.get("ticker", "")).strip().upper()
            if not ticker: continue
            sector = str(row.get("sector", "Unknown"))
            industry = str(row.get("industry", "Unknown"))
            sc = sector_counts.get(sector, 0)
            ic = industry_counts.get(industry, 0)
            if sc >= 7: continue
            if ic >= 4: continue
            selected.append({
                "ticker": ticker,
                "b2_score": float(row.get("YF-QVP_percentile", row.get("qvp_score", 0))),
                "quality_percentile": round(float(row.get("quality_score", 0)) * 100, 4),
                "quality_components_ok": 4,
                "sector": sector,
                "industry": industry,
                "target_pct": round(100.0 / 30, 4),
                "is_missing_q": "False",
                "company": str(row.get("company_name", ticker)),
            })
            sector_counts[sector] = sc + 1
            industry_counts[industry] = ic + 1
            if len(selected) >= 30: break
        return selected, sector_counts, industry_counts

    return run

def validate(selected):
    errors = []
    if len(selected) != 30: errors.append(f"Expected 30, got {len(selected)}")
    tickers = [h["ticker"] for h in selected]
    if len(set(tickers)) != len(tickers): errors.append("Duplicate tickers")
    sc = Counter(h["sector"] for h in selected)
    for s, c in sc.items():
        if c > 7: errors.append(f"Sector cap: {s} has {c} > 7")
    ic = Counter(h["industry"] for h in selected)
    for i, c in ic.items():
        if c > 4: errors.append(f"Industry cap: {i} has {c} > 4")
    if errors:
        for e in errors: print(f"VALIDATION ERROR: {e}")
        return False
    print(f"VALIDATION PASSED: {len(selected)} holdings, {len(sc)} sectors, {len(ic)} industries")
    return True

def main():
    output_dir = ROOT / "outputs/quarterly"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_ranking()
    qualified = apply_quality_veto(df)
    select, sector_counts, industry_counts = apply_caps()(qualified, "YF-QVP_percentile")
    ok = validate(select)

    # Write CSV
    csv_path = output_dir / "m1_b2_quality_veto_targets.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "B2_score", "Q_percentile", "Q_components_ok", "target_pct", "sector", "industry", "is_missing_q"])
        for h in select:
            w.writerow([h["ticker"], f"{h['b2_score']:.4f}", f"{h['quality_percentile']:.4f}",
                        h["quality_components_ok"], f"{h['target_pct']:.4f}", h["sector"], h["industry"], h["is_missing_q"]])

    manifest = {
        "model_id": MODEL_ID, "holdings": len(select),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "validation_passed": ok, "tickers": [h["ticker"] for h in select],
        "sectors": dict(sector_counts), "industries": dict(industry_counts),
        "source_csv": "outputs/final/current_daily_qvp_ranking.csv",
        "evidence_label": EVIDENCE_LABEL,
    }
    write_json(manifest, output_dir / "m1_b2_manifest.json")

    print(f"\nOutput: {csv_path} ({len(select)} holdings)")
    print(f"Tickers: {', '.join(h['ticker'] for h in select[:10])}...")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
