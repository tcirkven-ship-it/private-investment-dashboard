"""Stage 2 — Official M1_B2_QUALITY_VETO_N30 Selector/Writer.
Reads the official factor input CSV (from Stage 1), applies Quality Veto +
sector/industry caps, produces validated Top 30.
Refuses to write if the factor snapshot is stale or missing metadata.
"""
from __future__ import annotations
import argparse, json, sys, csv
from pathlib import Path
from datetime import datetime, timezone, date
from collections import Counter
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest.price_walkforward import write_json

MODEL_ID = "M1_B2_QUALITY_VETO_N30"
Q_FACTORS = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]
QUALITY_VETO_THRESHOLD = 0.10
SECTOR_CAP = 7
INDUSTRY_CAP = 4
TARGET_COUNT = 30
TARGET_WEIGHT = round(100.0 / TARGET_COUNT, 4)
MAX_STALENESS_DAYS = 90

def find_latest_factor_input(allow_legacy: bool = False):
    """Find the most recent dated factor input file.
    Without --allow-legacy, fails if no dated file exists.
    With --allow-legacy, falls back to the committed undated input."""
    dated_dir = ROOT / "outputs/quarterly/factor_inputs"
    if dated_dir.exists():
        dated = sorted(dated_dir.glob("m1_b2_factor_input_2*.csv"), reverse=True)
        if dated: return dated[0]
    if allow_legacy:
        legacy = ROOT / "outputs/quarterly/m1_b2_factor_input.csv"
        if legacy.exists():
            print("WARNING: Using legacy undated factor input (--allow-legacy). Staleness checks may not apply.")
            return legacy
        raise FileNotFoundError(
            "No dated factor input file found and legacy fallback missing.\n"
            "Run Stage 1 first: python scripts/build_m1_b2_factor_snapshot.py --snapshot-id <ID>"
        )
    raise FileNotFoundError(
        "No dated factor input file found in outputs/quarterly/factor_inputs/.\n"
        "Run Stage 1 first: python scripts/build_m1_b2_factor_snapshot.py --snapshot-id <ID>\n"
        "Or use --allow-legacy to fall back to committed undated input."
    )

def main(factor_input: str | None = None, allow_legacy: bool = False):
    output_dir = ROOT / "outputs/quarterly"
    output_dir.mkdir(parents=True, exist_ok=True)

    if factor_input:
        input_file = Path(factor_input)
        if not input_file.exists():
            print(f"ERROR: Factor input file not found: {factor_input}")
            sys.exit(1)
    else:
        input_file = find_latest_factor_input(allow_legacy)

    print(f"Stage 2: Reading factor input: {input_file.name} (from {input_file.parent})")
    df = pd.read_csv(input_file)
    print(f"  Input: {len(df)} tickers")

    required_date_cols = ["as_of_date", "source_snapshot"]
    for col in required_date_cols:
        if col not in df.columns:
            print(f"ERROR: Required column '{col}' missing from factor input")
            sys.exit(1)

    as_of_str = str(df["as_of_date"].iloc[0])
    try:
        as_of_date = date.fromisoformat(as_of_str[:10])
        age = (date.today() - as_of_date).days
        print(f"  Factor snapshot date (as_of_date): {as_of_date} (age: {age} days)")
        if sum(df["as_of_date"].isna()) > 0:
            print("ERROR: Some rows have missing as_of_date values")
            sys.exit(1)
        if age > MAX_STALENESS_DAYS:
            if allow_legacy:
                print(f"WARNING: Legacy factor snapshot is {age} days old (max {MAX_STALENESS_DAYS}). Proceeding with --allow-legacy.")
            else:
                print(f"ERROR: Factor snapshot is {age} days old (max {MAX_STALENESS_DAYS}). Run Stage 1 to refresh.")
                sys.exit(1)
        if as_of_date > date.today():
            print(f"ERROR: Factor snapshot date {as_of_date} is in the future")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Cannot parse factor snapshot as_of_date from '{as_of_str}': {e}")
        sys.exit(1)

    source_snap = str(df["source_snapshot"].iloc[0]) if "source_snapshot" in df.columns else ""
    if not source_snap or source_snap == "nan":
        print("ERROR: source_snapshot is missing or empty")
        sys.exit(1)
    print(f"  Source snapshot: {source_snap}")

    # Derive Q_components_ok
    for qf in Q_FACTORS:
        if qf not in df.columns:
            df[f"q_{qf}"] = 0
        else:
            df[f"q_{qf}"] = df[qf].notna().astype(int)
    df["Q_components_ok"] = sum(df[f"q_{f}"] for f in Q_FACTORS)

    # Validate required columns
    for col in ["B2_score", "Q_score", "ticker", "sector", "industry"]:
        if col not in df.columns:
            print(f"ERROR: Required column '{col}' missing from factor input")
            sys.exit(1)

    # Quality Veto
    df = df.dropna(subset=["Q_score"]).copy()
    df["q_rank"] = df["Q_score"].rank(pct=True)
    excluded = df[df["q_rank"] <= QUALITY_VETO_THRESHOLD]
    qualified = df[df["q_rank"] > QUALITY_VETO_THRESHOLD].copy()
    print(f"  Quality veto: {len(excluded)} excluded, {len(qualified)} remain")

    # Select Top 30
    qualified = qualified.sort_values("B2_score", ascending=False)
    selected, sector_counts, industry_counts = [], {}, {}
    for _, row in qualified.iterrows():
        t = str(row["ticker"]).strip().upper()
        sector = str(row.get("sector", "Unknown"))
        industry = str(row.get("industry", "Unknown"))
        if sector_counts.get(sector, 0) >= SECTOR_CAP: continue
        if industry_counts.get(industry, 0) >= INDUSTRY_CAP: continue
        selected.append(row)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        industry_counts[industry] = industry_counts.get(industry, 0) + 1
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
    print(f"  VALIDATION PASSED: {len(selected)} holdings, {len(sector_counts)} sectors")

    # Write CSV
    csv_path = output_dir / "m1_b2_quality_veto_targets.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "B2_score", "Q_percentile", "Q_components_ok", "target_pct", "sector", "industry", "is_missing_q"])
        for r in selected:
            t = str(r["ticker"]).strip().upper()
            w.writerow([t, f"{float(r['B2_score']):.4f}", f"{round(float(r['q_rank'])*100,4):.4f}",
                        int(r.get("Q_components_ok", 4)), f"{TARGET_WEIGHT:.4f}",
                        str(r.get("sector", "")), str(r.get("industry", "")), "False"])

    # Manifest
    snapshot_date = str(df["as_of_date"].iloc[0])[:10] if "as_of_date" in df.columns else "unknown"
    source_snapshot = str(df.iloc[0].get("source_snapshot", "unknown")) if len(df) > 0 else "unknown"
    manifest = {
        "model_id": MODEL_ID,
        "generation_mode": "official_factor_snapshot",
        "stage": "2",
        "factor_snapshot_date": snapshot_date,
        "factor_snapshot_id": source_snapshot,
        "source_factor_file": str(input_file.name),
        "input_row_count": len(df),
        "b2_formula": "mean of M12_1, M6_1, TREND200",
        "quality_formula": f"mean of {', '.join(Q_FACTORS)}",
        "quality_veto_threshold": f"{QUALITY_VETO_THRESHOLD*100}%",
        "sector_cap": str(SECTOR_CAP),
        "industry_cap": str(INDUSTRY_CAP),
        "holdings": len(selected),
        "validation_passed": ok,
        "tickers": tickers,
        "sectors": {str(k): int(v) for k, v in sector_counts.items()},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "staleness_max_days": MAX_STALENESS_DAYS,
    }
    write_json(output_dir / "m1_b2_manifest.json", manifest)

    print(f"\n{MODEL_ID} Generated (Stage 2):")
    print(f"  Holdings: {len(selected)}")
    print(f"  Factor date: {snapshot_date}")
    print(f"  Tickers: {', '.join(tickers[:10])}...")
    return 0

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Stage 2 — Generate M1_B2_QUALITY_VETO_N30 official holdings")
    p.add_argument("--allow-legacy", action="store_true", help="Allow fallback to undated legacy factor input CSV")
    p.add_argument("--factor-input", type=str, default=None, help="Exact path to factor input CSV from Stage 1")
    args = p.parse_args()
    sys.exit(main(factor_input=args.factor_input, allow_legacy=args.allow_legacy))
