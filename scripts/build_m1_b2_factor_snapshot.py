"""Stage 1 — Official M1_B2_QUALITY_VETO_N30 Factor Snapshot Builder.
Builds a small committed factor input CSV from the raw factor panel.
Run locally after each quarter-end closing session.
"""
from __future__ import annotations
import argparse, sys, hashlib, csv
from pathlib import Path
from datetime import datetime, timezone, date
import pandas as pd
import numpy as np
import json

ROOT = Path(__file__).resolve().parents[1]
B2_FACTORS = ["M12_1", "M6_1", "TREND200"]
Q_FACTORS = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]
MIN_ELIGIBLE = 500
MAX_SNAPSHOT_AGE_DAYS_AFTER_ASOF = 21

def parse_snapshot_date(snapshot_id: str) -> date:
    """Extract the calendar date from a snapshot id like 2026-07-01T053352Z."""
    try:
        return date.fromisoformat(snapshot_id[:10])
    except ValueError as e:
        raise RuntimeError(f"Cannot parse snapshot date from snapshot id '{snapshot_id}': {e}")

def validate_freshness(snapshot_id: str, as_of_date: str) -> None:
    """Hard fail if the snapshot does not cover the requested as_of_date or is too old."""
    snap_date = parse_snapshot_date(snapshot_id)
    asof = date.fromisoformat(as_of_date)
    if snap_date < asof:
        raise RuntimeError(
            f"STALE SNAPSHOT: snapshot {snapshot_id} (data date {snap_date}) predates requested "
            f"as_of_date {asof}. A snapshot must be taken on or after the quarter-end session. "
            f"Run a fresh data pull (Stage 0 / full run) for this quarter."
        )
    age = (snap_date - asof).days
    if age > MAX_SNAPSHOT_AGE_DAYS_AFTER_ASOF:
        raise RuntimeError(
            f"STALE SNAPSHOT: snapshot {snapshot_id} (data date {snap_date}) is {age} days after "
            f"as_of_date {asof} (max {MAX_SNAPSHOT_AGE_DAYS_AFTER_ASOF}). Run a fresh data pull."
        )

def build_factor_input(snapshot_id: str, output_dir: Path, ranking_csv: Path | None = None, as_of_date: str | None = None):
    """Build the M1_B2 factor input CSV from raw factor panel for a given snapshot."""
    if as_of_date:
        validate_freshness(snapshot_id, as_of_date)

    factor_panel = ROOT / f"data/prospective/daily_qvp/snapshots/{snapshot_id}/analysis/factor_level_current.csv"
    if not factor_panel.exists():
        raise FileNotFoundError(f"Factor panel not found: {factor_panel}\nRun the daily scanner first to generate this file.")

    if ranking_csv is None:
        ranking_csv = ROOT / "outputs/final/current_daily_qvp_ranking.csv"
    if not ranking_csv.exists():
        raise FileNotFoundError(f"Ranking CSV not found: {ranking_csv}")

    print(f"Stage 1: Building M1_B2 factor snapshot from {snapshot_id}")
    print(f"  Factor panel: {factor_panel}")
    print(f"  Ranking: {ranking_csv}")

    fp = pd.read_csv(factor_panel)
    ranking = pd.read_csv(ranking_csv)
    sec = ranking[["ticker", "sector", "industry", "company_name"]].drop_duplicates("ticker").set_index("ticker")

    needed = B2_FACTORS + Q_FACTORS
    filtered = fp[fp["factor"].isin(needed)].copy()
    pivoted = filtered.pivot_table(index="ticker", columns="factor", values="percentile_rank", aggfunc="first").reset_index()

    ticker_count = pivoted["ticker"].nunique()
    if ticker_count < MIN_ELIGIBLE:
        raise RuntimeError(f"Only {ticker_count} tickers — below integrity floor of {MIN_ELIGIBLE}")

    # Merge sector/industry/company
    pivoted["sector"] = pivoted["ticker"].map(sec["sector"]).fillna("Unknown")
    pivoted["industry"] = pivoted["ticker"].map(sec["industry"]).fillna("Unknown")
    pivoted["company"] = pivoted["ticker"].map(sec["company_name"]).fillna("")

    # Quality component availability
    for qf in Q_FACTORS:
        pivoted[f"q_{qf}"] = (pivoted[qf].notna() if qf in pivoted.columns else 0).astype(int)
    pivoted["Q_components_ok"] = sum(pivoted[f"q_{f}"] for f in Q_FACTORS)

    pivoted["B2_score"] = pivoted[B2_FACTORS].mean(axis=1, skipna=True)
    pivoted["Q_score"] = pivoted[Q_FACTORS].mean(axis=1, skipna=True)
    pivoted["source_snapshot"] = snapshot_id
    pivoted["generated_at"] = datetime.now(timezone.utc).isoformat()
    as_of_date = as_of_date if as_of_date else snapshot_id[:10]
    pivoted["as_of_date"] = as_of_date

    out_cols = ["ticker", "company", "sector", "industry"] + B2_FACTORS + Q_FACTORS + ["B2_score", "Q_score", "Q_components_ok", "source_snapshot", "generated_at", "as_of_date"]
    out_cols = [c for c in out_cols if c in pivoted.columns]

    today = date.today().isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    outfile = output_dir / f"m1_b2_factor_input_{today}.csv"
    pivoted[out_cols].to_csv(outfile, index=False)

    raw_panel_sha = ""
    with open(factor_panel, "rb") as f:
        raw_panel_sha = hashlib.sha256(f.read()).hexdigest()[:12]

    with open(outfile, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()[:12]
    size_kb = outfile.stat().st_size / 1024

    # Missing data counts
    b2_missing = pivoted[B2_FACTORS].isna().any(axis=1).sum()
    q_missing = pivoted[Q_FACTORS].isna().all(axis=1).sum()
    sector_missing = (pivoted["sector"] == "Unknown").sum()

    # Manifest
    manifest = {
        "stage": "1",
        "snapshot_id": snapshot_id,
        "snapshot_date": str(parse_snapshot_date(snapshot_id)),
        "as_of_date": as_of_date,
        "freshness_max_days_after_asof": MAX_SNAPSHOT_AGE_DAYS_AFTER_ASOF,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "factor_panel_source": str(factor_panel),
        "factor_panel_sha256_12": raw_panel_sha,
        "ranking_source": str(ranking_csv),
        "ticker_count": int(ticker_count),
        "b2_formula": "mean(M12_1, M6_1, TREND200)",
        "quality_formula": "mean(ROA, GPA, FCF_MARGIN, DEBT_ASSETS)",
        "output_file": str(outfile.name),
        "size_kb": int(size_kb),
        "sha256_12": sha,
        "b2_missing_count": int(b2_missing),
        "q_missing_count": int(q_missing),
        "sector_missing_count": int(sector_missing),
        "B2_factors_present": all(f in pivoted.columns for f in B2_FACTORS),
        "Q_factors_present": all(f in pivoted.columns for f in Q_FACTORS),
        "integrity_floor": MIN_ELIGIBLE,
    }
    manifest_path = output_dir / f"m1_b2_factor_manifest_{today}.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nStage 1 Complete:")
    print(f"  Output: {outfile} ({size_kb} KB, {ticker_count} tickers, sha256={sha})")
    print(f"  Manifest: {manifest_path}")
    print(f"  B2 missing: {b2_missing}, Q missing: {q_missing}, Sector missing: {sector_missing}")
    return outfile, manifest_path

def main():
    p = argparse.ArgumentParser(description="Stage 1 — Build M1_B2 factor snapshot")
    p.add_argument("--snapshot-id", required=True, help="Snapshot ID (e.g. 2026-06-24T080500Z)")
    p.add_argument("--output-dir", default=str(ROOT / "outputs/quarterly/factor_inputs"),
                   help="Output directory")
    p.add_argument("--ranking-csv", help="Path to ranking CSV with sectors/industries")
    p.add_argument("--as-of", help="Override as_of_date (market data date), e.g. 2026-06-30")
    args = p.parse_args()
    try:
        build_factor_input(args.snapshot_id, Path(args.output_dir),
                          Path(args.ranking_csv) if args.ranking_csv else None,
                          as_of_date=args.as_of)
    except Exception as e:
        print(f"STAGE 1 FAILED: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
