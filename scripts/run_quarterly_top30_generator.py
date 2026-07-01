#!/usr/bin/env python3
"""Quarterly Top 30 Generator Launcher — M1_B2_QUALITY_VETO_N30.
Coordinates the local pipeline, creates timestamped output for app loading.
"""
import argparse, json, csv, shutil, hashlib, subprocess, sys, os, webbrowser
from pathlib import Path
from datetime import datetime, timezone, date, timedelta

ROOT = Path(__file__).resolve().parents[1]

def quarter_label(as_of: str) -> str:
    d = date.fromisoformat(as_of)
    q = (d.month - 1) // 3 + 1
    return f"{d.year}-Q{q}"

def default_as_of() -> str:
    today = date.today()
    m = (today.month - 1) // 3 * 3 + 3
    year = today.year if m <= 12 else today.year + 1
    m = m if m <= 12 else 3
    last_day = (date(year, m, 1) - timedelta(days=1)).isoformat()
    return last_day

def main():
    p = argparse.ArgumentParser(description="M1_B2_QUALITY_VETO_N30 quarterly generator launcher")
    p.add_argument("--as-of", default=default_as_of(), help=f"Quarter-end market data date (default: {default_as_of()})")
    p.add_argument("--skip-build", action="store_true", help="Skip Stage 1 factor snapshot build")
    p.add_argument("--skip-fresh", action="store_true", help="Skip Stage 0 fresh data pull (use existing snapshot)")
    args = p.parse_args()

    as_of = args.as_of
    ql = quarter_label(as_of)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    out_dir = ROOT / f"outputs/quarterly_exports/{ql}_asof-{as_of}_generated-{now}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  M1_B2_QUALITY_VETO_N30 — Quarterly Top 30 Generator")
    print(f"  Quarter: {ql}   as_of_date: {as_of}")
    print(f"  Output: {out_dir.name}")
    print(f"{'='*60}\n")

    # Stage 0: Fresh data pull
    if not args.skip_fresh:
        print("[0/3] Pulling fresh market data...")
        print("  This may take 1–2 hours. Waiting for daily_screen.py...")
        r = subprocess.run([sys.executable, "src/daily_screen.py",
                           "--output-root", "outputs/quarterly_pull",
                           "--workers", "2", "--attempts", "5", "--delay-seconds", "1.5"],
                           cwd=str(ROOT))
        if r.returncode != 0:
            print("STAGE 0 FAILED: Fresh data pull failed. Try again or use --skip-fresh.")
            sys.exit(1)
        print("  Fresh data pull complete.\n")
    else:
        print("[0/3] Skipping fresh data pull (--skip-fresh). Using existing snapshot data.\n")

    # Stage 1: Build factor snapshot
    factor_input_path = None
    if not args.skip_build:
        print("[1/3] Building factor snapshot...")
        snap_dirs = sorted(Path("data/prospective/daily_qvp/snapshots").glob("2*"), reverse=True)
        if not snap_dirs:
            snap_dirs = sorted(Path("outputs/quarterly_pull/daily_qvp_runs").rglob("analysis/factor_level_current.csv"), reverse=True)
            snap_dirs = [d.parent.parent.parent for d in snap_dirs]
        if not snap_dirs:
            print("ERROR: No raw snapshot data found. Run Stage 0 first (data pull).")
            sys.exit(1)
        snap_id = snap_dirs[0].name
        print(f"  Using snapshot: {snap_id}")
        r = subprocess.run([sys.executable, "scripts/build_m1_b2_factor_snapshot.py",
                           "--snapshot-id", snap_id, "--output-dir", str(out_dir)],
                           capture_output=True, text=True)
        print(r.stdout)
        if r.returncode != 0:
            print(f"STAGE 1 FAILED:\n{r.stderr}")
            sys.exit(1)
        # Find the exact output file
        factor_files = sorted(out_dir.glob("m1_b2_factor_input_*.csv"), reverse=True)
        if factor_files:
            factor_input_path = str(factor_files[0])
    else:
        print("[1/3] Skipping factor snapshot build (--skip-build)")

    # Stage 2: Select Top 30 — MUST use exact Stage 1 output
    print("[2/3] Selecting Top 30...")
    if not factor_input_path:
        print("ERROR: No factor input from Stage 1. Cannot proceed.")
        sys.exit(1)

    cmd = [sys.executable, "scripts/generate_m1_b2_official.py", "--factor-input", factor_input_path]
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(f"STAGE 2 FAILED:\n{r.stderr}")
        sys.exit(1)

    # Stage 3: Validate and finalize
    print("[3/3] Validating and finalizing...")
    source_csv = ROOT / "outputs/quarterly/m1_b2_quality_veto_targets.csv"
    source_manifest = ROOT / "outputs/quarterly/m1_b2_manifest.json"

    # Date validation
    if source_manifest.exists():
        with open(source_manifest) as f:
            mf = json.load(f)
        snap_date = mf.get("factor_snapshot_date", "")
        if snap_date and snap_date != as_of:
            print(f"HARD STOP: Factor snapshot date ({snap_date}) != as_of_date ({as_of}).")
            print("Generation aborted. Run Stage 0 (fresh data pull) to get current quarter-end data.")
            sys.exit(1)
        print(f"  Date check: factor_snapshot_date ({snap_date}) == as_of_date ({as_of}) PASSED")
    print(f"  Stage 2 input: {factor_input_path}")

    if source_csv.exists():
        dest_csv = out_dir / "m1_b2_quality_veto_targets.csv"
        shutil.copy(source_csv, dest_csv)

        # CSV checksum
        with open(dest_csv, "rb") as f:
            csv_sha = hashlib.sha256(f.read()).hexdigest()[:12]

        # Parse CSV to get tickers
        with open(dest_csv) as f:
            rows = list(csv.DictReader(f))
        tickers = [r["ticker"].strip().upper() for r in rows if r.get("ticker")]

        # Validation
        errors = []
        if len(rows) != 30: errors.append(f"Expected 30, got {len(rows)}")
        if len(set(tickers)) != len(tickers): errors.append("Duplicate tickers")
        for col in ["B2_score", "Q_percentile"]:
            missing = sum(1 for r in rows if not r.get(col) or r[col] in ("", "0", "0.0"))
            if missing > 0: errors.append(f"{missing} rows missing {col}")
    else:
        tickers = []
        csv_sha = ""
        errors = ["CSV not found"]

    # Write manifest
    manifest = {
        "model_id": "M1_B2_QUALITY_VETO_N30",
        "quarter_label": ql,
        "as_of_date": as_of,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generation_mode": "offline_notebook_official_generator",
        "source": "local_generator",
        "holdings": len(rows) if source_csv.exists() else 0,
        "target_weight": "3.3333%",
        "sector_cap": "25%",
        "industry_cap": "15%",
        "quality_veto": "bottom 10%",
        "validation_passed": len(errors) == 0,
        "errors": errors,
        "final_tickers": tickers,
        "csv_sha256": csv_sha,
        "output_folder": str(out_dir.name),
    }
    with open(out_dir / "m1_b2_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # Write log
    with open(out_dir / "generation_log.txt", "w") as f:
        f.write(f"M1_B2_QUALITY_VETO_N30 Generation Log\n")
        f.write(f"Quarter: {ql}\n")
        f.write(f"as_of_date: {as_of}\n")
        f.write(f"generated_at: {manifest['generated_at']}\n")
        f.write(f"holdings: {manifest['holdings']}\n")
        f.write(f"validation: {'PASSED' if manifest['validation_passed'] else 'FAILED'}\n")
        f.write(f"tickers: {', '.join(tickers[:10])}...\n")

    # Write README for app loading
    with open(out_dir / "README_LOAD_IN_APP.txt", "w") as f:
        f.write("HOW TO LOAD IN APP\n")
        f.write("==================\n\n")
        f.write("1. Open the app: https://private-investment-dashboard.vercel.app\n")
        f.write("2. Sign in.\n")
        f.write("3. Go to Top 30 page.\n")
        f.write("4. Click 'Load Notebook-Generated Top 30'.\n")
        f.write("5. Select: m1_b2_quality_veto_targets.csv\n")
        f.write("6. Confirm 30 holdings with scores are visible.\n")
        f.write("7. Go to Compare page.\n\n")
        f.write(f"Model: M1_B2_QUALITY_VETO_N30\n")
        f.write(f"Quarter: {ql}\n")
        f.write(f"as_of_date: {as_of}\n")
        f.write(f"Holdings: {manifest['holdings']}\n")
        f.write(f"Validation: {'PASSED' if manifest['validation_passed'] else 'FAILED'}\n")
        if errors:
            for e in errors:
                f.write(f"  - {e}\n")

    # Done
    print(f"\n{'='*60}")
    print(f"GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"Model:  M1_B2_QUALITY_VETO_N30")
    print(f"Quarter: {ql}")
    print(f"As-of:   {as_of}")
    print(f"Output:  {out_dir}")
    print(f"Holdings: {manifest['holdings']}")
    print(f"Validation: {'PASSED' if manifest['validation_passed'] else 'FAILED'}")
    print(f"Tickers: {', '.join(tickers[:10])}...")
    if errors:
        print(f"WARNINGS:")
        for e in errors: print(f"  - {e}")
    print(f"\nTo load in app: select {dest_csv.name} from Top 30 page")

    # Open folder
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(out_dir)])
        elif sys.platform == "win32":
            os.startfile(str(out_dir))
    except:
        pass

    sys.exit(0 if manifest["validation_passed"] else 1)

if __name__ == "__main__":
    main()
