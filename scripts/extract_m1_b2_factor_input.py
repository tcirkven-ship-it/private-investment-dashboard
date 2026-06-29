"""Extract M1_B2_QUALITY_VETO_N30 factor input from raw factor panel.
Converts a 200MB factor_level_current.csv into a ~260KB committed file
containing only the columns needed for official M1_B2 generation.
"""
import pandas as pd
import hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

SNAPSHOT_ID = "2026-06-24T080500Z"
FACTOR_PANEL = ROOT / f"data/prospective/daily_qvp/snapshots/{SNAPSHOT_ID}/analysis/factor_level_current.csv"
RANKING_CSV = ROOT / "outputs/final/current_daily_qvp_ranking.csv"
OUTFILE = ROOT / "outputs/quarterly/m1_b2_factor_input.csv"

B2_FACTORS = ["M12_1", "M6_1", "TREND200"]
Q_FACTORS = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]

def main():
    print(f"Extracting M1_B2 factor input from snapshot {SNAPSHOT_ID}")
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)

    fp = pd.read_csv(FACTOR_PANEL)
    print(f"  Factor panel: {len(fp)} rows, {fp['ticker'].nunique()} tickers")

    ranking = pd.read_csv(RANKING_CSV)
    sec = ranking[["ticker", "sector", "industry", "company_name"]].drop_duplicates("ticker").set_index("ticker")

    needed = B2_FACTORS + Q_FACTORS
    filtered = fp[fp["factor"].isin(needed)].copy()
    print(f"  Filtered to {len(needed)} factors: {len(filtered)} rows")

    pivoted = filtered.pivot_table(index="ticker", columns="factor", values="percentile_rank", aggfunc="first").reset_index()

    pivoted["sector"] = pivoted["ticker"].map(sec["sector"]).fillna("Unknown")
    pivoted["industry"] = pivoted["ticker"].map(sec["industry"]).fillna("Unknown")
    pivoted["company"] = pivoted["ticker"].map(sec["company_name"]).fillna("")

    for qf in Q_FACTORS:
        pivoted[f"q_{qf}"] = (pivoted[qf].notna() if qf in pivoted.columns else 0).astype(int)
    pivoted["Q_components_ok"] = sum(pivoted[f"q_{f}"] for f in Q_FACTORS)

    pivoted["B2_score"] = pivoted[B2_FACTORS].mean(axis=1, skipna=True)
    pivoted["Q_score"] = pivoted[Q_FACTORS].mean(axis=1, skipna=True)
    pivoted["source_snapshot"] = SNAPSHOT_ID

    out_cols = ["ticker", "company", "sector", "industry"] + B2_FACTORS + Q_FACTORS + ["B2_score", "Q_score", "Q_components_ok", "source_snapshot"]
    out_cols = [c for c in out_cols if c in pivoted.columns]
    pivoted[out_cols].to_csv(OUTFILE, index=False)

    with open(OUTFILE, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()[:12]
    size_kb = OUTFILE.stat().st_size / 1024
    print(f"  Output: {OUTFILE} ({size_kb:.0f} KB, {pivoted['ticker'].nunique()} tickers, sha256={sha})")
    print(f"  Columns: {out_cols}")
    print(f"  Generated: {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    main()
