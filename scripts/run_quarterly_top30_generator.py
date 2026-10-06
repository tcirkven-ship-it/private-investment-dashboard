#!/usr/bin/env python3
"""Quarterly Top 30 Generator Launcher — M1_B2_QUALITY_VETO_N30.
Coordinates the local pipeline, creates timestamped output for app loading.
"""
import argparse, json, csv, shutil, hashlib, subprocess, sys, os, webbrowser
from pathlib import Path
from datetime import datetime, timezone, date, timedelta

ROOT = Path(__file__).resolve().parents[1]
MAX_SOURCE_AGE_DAYS_AFTER_ASOF = 21

def quarter_label(as_of: str) -> str:
    d = date.fromisoformat(as_of)
    q = (d.month - 1) // 3 + 1
    return f"{d.year}-Q{q}"

def snapshot_date_from_id(snapshot_id: str) -> date:
    return date.fromisoformat(snapshot_id[:10])

def check_snapshot_freshness(snapshot_id: str, as_of: str) -> tuple[bool, str]:
    """Return (ok, message) for whether snapshot is fresh for the requested as_of date."""
    try:
        snap_date = snapshot_date_from_id(snapshot_id)
        asof_date = date.fromisoformat(as_of)
    except ValueError as e:
        return False, f"Cannot parse snapshot id '{snapshot_id}' or as_of '{as_of}': {e}"
    if snap_date < asof_date:
        return False, (
            f"Snapshot {snapshot_id} (data date {snap_date}) predates as_of_date {asof_date}. "
            f"It cannot cover the quarter-end session."
        )
    age = (snap_date - asof_date).days
    if age > MAX_SOURCE_AGE_DAYS_AFTER_ASOF:
        return False, (
            f"Snapshot {snapshot_id} (data date {snap_date}) is {age} days after as_of_date {asof_date} "
            f"(max {MAX_SOURCE_AGE_DAYS_AFTER_ASOF})."
        )
    return True, f"Snapshot {snapshot_id} (data date {snap_date}, {age} days after as_of_date) is fresh."

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

    print(f"\n{'='*60}")
    print(f"  M1_B2_QUALITY_VETO_N30 — Quarterly Top 30 Generator")
    print(f"  Quarter: {ql}   as_of_date: {as_of}")
    print(f"  Output: {out_dir.name} (created only after freshness check passes)")
    print(f"{'='*60}\n")

    # Early freshness gate for quick runs: fail before doing any work.
    if args.skip_fresh and not args.skip_build:
        snap_root = ROOT / "data/prospective/daily_qvp/snapshots"
        snap_dirs = sorted(snap_root.glob("2*"), reverse=True)
        if snap_dirs:
            early_fresh, early_msg = check_snapshot_freshness(snap_dirs[0].name, as_of)
            if not early_fresh:
                print(f"{'='*60}")
                print("HARD STOP: STALE SOURCE SNAPSHOT (nothing was generated)")
                print(f"{'='*60}")
                print(f"  {early_msg}")
                print(f"  A snapshot from before {as_of} cannot be relabeled as {ql}.")
                print(f"\n  For a new quarter you must run the FULL pull (removes --skip-fresh):")
                print(f'    python scripts/run_quarterly_top30_generator.py --as-of "{as_of}"')
                print(f"  (takes 1-2 hours; downloads fresh market data)")
                sys.exit(1)

    # Stage 0: Fresh data pull
    if not args.skip_fresh:
        print("[0/3] Pulling fresh market data...")
        print("  This may take 1–2 hours. Waiting for daily_screen.py...")
        print("  Resumable: a partial pull is completed on retry (--resume-retrieval).")
        print("  Tolerance: up to 1 eligible ticker may lack scoring-core annual files")
        print("  (e.g. newly listed companies). The pull manifest records which tickers.")
        r = subprocess.run([sys.executable, "src/daily_screen.py",
                           "--output-root", "outputs/quarterly_pull",
                           "--workers", "2", "--attempts", "5", "--delay-seconds", "1.5",
                           "--resume-retrieval",
                           "--maximum-scoring-core-incomplete", "1"],
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
        snap_root = ROOT / "data/prospective/daily_qvp/snapshots"
        snap_dirs = sorted(snap_root.glob("2*"), reverse=True)
        if not snap_dirs:
            pull_root = ROOT / "outputs/quarterly_pull"
            snap_dirs = sorted(pull_root.rglob("analysis/factor_level_current.csv"), reverse=True)
            snap_dirs = [d.parent.parent.parent for d in snap_dirs]
        if not snap_dirs:
            print("ERROR: No raw snapshot data found. Run Stage 0 first (data pull).")
            sys.exit(1)
        snap_id = snap_dirs[0].name
        print(f"  Using snapshot: {snap_id}")

        # Freshness gate: refuse stale source data before doing any work.
        fresh, fresh_msg = check_snapshot_freshness(snap_id, as_of)
        if not fresh:
            print(f"\n{'='*60}")
            print("HARD STOP: STALE SOURCE SNAPSHOT (nothing was generated)")
            print(f"{'='*60}")
            print(f"  {fresh_msg}")
            print(f"  A snapshot from before {as_of} cannot be relabeled as {ql}.")
            if args.skip_fresh:
                print(f"\n  You used --skip-fresh (quick run). For a new quarter you must run the FULL pull:")
                print(f'    python scripts/run_quarterly_top30_generator.py --as-of "{as_of}"')
                print(f"  (takes 1-2 hours; downloads fresh market data)")
            else:
                print(f"\n  A fresh pull did not produce a usable snapshot. Check Stage 0 output.")
            sys.exit(1)
        print(f"  Freshness: {fresh_msg}")

        # Create the export folder only after the freshness gate passes.
        out_dir.mkdir(parents=True, exist_ok=True)

        r = subprocess.run([sys.executable, "scripts/build_m1_b2_factor_snapshot.py",
                           "--snapshot-id", snap_id, "--output-dir", str(out_dir),
                           "--as-of", as_of],
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

    # Source snapshot freshness validation (against the REAL snapshot date, not the relabeled as_of).
    src_snap_id = ""
    src_snap_date = ""
    if source_manifest.exists():
        with open(source_manifest) as f:
            mf = json.load(f)
        src_snap_id = str(mf.get("factor_snapshot_id", ""))
        src_snap_date = str(mf.get("factor_snapshot_date", ""))
        if not src_snap_id or not src_snap_date:
            print("HARD STOP: Stage 2 manifest is missing factor_snapshot_id / factor_snapshot_date.")
            sys.exit(1)
        fresh, fresh_msg = check_snapshot_freshness(src_snap_id, as_of)
        if not fresh:
            print(f"HARD STOP: STALE SOURCE — {fresh_msg}")
            print("Generation aborted. Run Stage 0 (fresh data pull) to get current quarter-end data.")
            sys.exit(1)
        print(f"  Freshness check: {fresh_msg}")
        print(f"  Source snapshot: {src_snap_id} (data date {src_snap_date})")
    else:
        print("HARD STOP: Stage 2 manifest not found.")
        sys.exit(1)
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
        for col in ["B2_score", "Q_percentile", "model_id", "as_of_date", "generated_at", "source", "quarter_label", "rank"]:
            missing = sum(1 for r in rows if not r.get(col) or r[col] in ("", "0", "0.0"))
            if missing > 0: errors.append(f"{missing} rows missing {col}")
        # Check date consistency
        csv_asof = rows[0].get("as_of_date", "") if rows else ""
        if csv_asof and csv_asof != as_of:
            errors.append(f"as_of_date mismatch: CSV says {csv_asof}, expected {as_of}")
        csv_ql = rows[0].get("quarter_label", "") if rows else ""
        if csv_ql and csv_ql != ql:
            errors.append(f"quarter_label mismatch: CSV says {csv_ql}, expected {ql}")

        # Date validation: as_of_date should be the quarter-end date
        if as_of:
            try:
                ad = date.fromisoformat(as_of)
                expected_month = {"1": 3, "2": 6, "3": 9, "4": 12}.get(ql.split("-Q")[-1] if "-Q" in ql else "")
                if expected_month and ad.month != expected_month:
                    errors.append(f"as_of_date ({as_of}) month does not match quarter-end for {ql} (expected month {expected_month})")
            except:
                pass
    else:
        tickers = []
        csv_sha = ""
        errors = ["CSV not found"]

    # Write manifest
    manifest = {
        "model_id": "M1_B2_QUALITY_VETO_N30",
        "quarter_label": ql,
        "as_of_date": as_of,
        "source_snapshot_id": src_snap_id,
        "source_snapshot_date": src_snap_date,
        "source_freshness_max_days_after_asof": MAX_SOURCE_AGE_DAYS_AFTER_ASOF,
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
        f.write(f"source_snapshot_id: {src_snap_id}\n")
        f.write(f"source_snapshot_date: {src_snap_date}\n")
        f.write(f"generated_at: {manifest['generated_at']}\n")
        f.write(f"holdings: {manifest['holdings']}\n")
        f.write(f"validation: {'PASSED' if manifest['validation_passed'] else 'FAILED'}\n")
        f.write(f"tickers: {', '.join(tickers[:10])}...\n")

    # Write README for app loading
    with open(out_dir / "README_LOAD_IN_APP.txt", "w") as f:
        f.write("HOW TO LOAD IN APP\n")
        f.write("==================\n\n")
        f.write("1. Open the app: https://private-investment-dashboard-tcirkven-projects.vercel.app\n")
        f.write("2. Sign in.\n")
        f.write("3. Go to Top 30 page.\n")
        f.write("4. Click 'Load Notebook-Generated Top 30'.\n")
        f.write("5. Select: m1_b2_quality_veto_targets.csv\n")
        f.write("6. Confirm 30 holdings with scores are visible.\n")
        f.write("7. Go to Compare page.\n\n")
        f.write(f"Model: M1_B2_QUALITY_VETO_N30\n")
        f.write(f"Quarter: {ql}\n")
        f.write(f"as_of_date: {as_of}\n")
        f.write(f"source_snapshot: {src_snap_id} (data date {src_snap_date})\n")
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
    print(f"Source:  {src_snap_id} (data date {src_snap_date})")
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
