#!/usr/bin/env python3
"""Auditable pre-activation storage inventory, CAS validation and allowlisted cleanup."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/storage_cleanup"
CAS = ROOT / "data/archive/yfinance_phase1b_cas"
CAS_MANIFEST = CAS / "manifests/2026-06-22T_currentZ.json"
RAW_CKPT2 = ROOT / "data/raw/yfinance_phase1b_checkpoint2/2026-06-22T_currentZ"

DELETE_PREFIXES = [
    "data/raw/yfinance_phase1b_checkpoint3",
    "data/raw/yfinance_phase1b/2026-06-21T204918Z",
    "data/raw/yfinance_phase1b_checkpoint2/2026-06-22T_currentZ",
    "outputs/experiment_runs/EXP-0015/rehearsal_1",
    "outputs/experiment_runs/EXP-0015/rehearsal_2",
    "outputs/experiment_runs/EXP-0015/rehearsal_3",
    "outputs/experiment_runs/EXP-0015/rehearsal_4",
    "outputs/experiment_runs/EXP-0016/daily_rehearsal_1",
    "data/metadata/yfinance_cache",
]
DELETE_FILES = {"outputs/experiment_runs/EXP-0014/factor_level_current.csv"}
CACHE_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".ipynb_checkpoints"}
CACHE_SUFFIXES = {".pyc", ".pyo", ".swp", ".tmp"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_files() -> set[str]:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True)
    return set(result.stdout.splitlines())


def planned_delete(relative: str, path: Path) -> tuple[bool, str, str]:
    if relative in DELETE_FILES:
        return True, "superseded_and_safely_deletable", "regenerable_large_factor table; compact scores, coverage and manifest retained"
    if any(relative == prefix or relative.startswith(prefix + "/") for prefix in DELETE_PREFIXES):
        if "checkpoint2" in relative:
            return True, "duplicate_of_verified_content_addressed_archive", "full logical snapshot retained in validated CAS"
        if "phase1b/2026" in relative:
            return True, "superseded_and_safely_deletable", "110-name sample superseded by 698-name audit; compact outputs and manifest retained"
        if "checkpoint3" in relative or "EXP-0015" in relative:
            return True, "superseded_and_safely_deletable", "intraday/execution-heavy design superseded without activation"
        if "daily_rehearsal_1" in relative:
            return True, "duplicate_of_retained_rehearsal", "byte-identical daily_rehearsal_2 retained"
        return True, "safe_generated_cache", "provider/cache material not used by active protocol"
    if path.name == ".DS_Store" or any(part in CACHE_NAMES for part in path.parts) or path.suffix in CACHE_SUFFIXES:
        return True, "safe_generated_cache", "generated cache/temp file"
    if relative.startswith("data/archive/yfinance_phase1b_cas"):
        return False, "required_for_active_prospective_experiment", "canonical compressed Checkpoint 2 baseline"
    if relative.startswith("outputs/experiment_runs/EXP-0016/daily_rehearsal_2"):
        return False, "required_only_for_compact_audit_history", "latest valid simplified rehearsal retained"
    if relative.startswith("outputs/experiment_runs/EXP-0014"):
        return False, "required_only_for_compact_audit_history", "compact factor/score/semantic evidence retained"
    if relative.startswith(".venv"):
        return False, "uncertain_and_retained", "active tested environment; lock exists but environment is currently used"
    if relative.startswith("data/raw/yfinance") or relative.startswith("data/raw/fred") or relative.startswith("data/raw/universe"):
        return False, "uncertain_and_retained", "Phase 1A audit scripts/reproducibility depend on these non-CAS inputs"
    if relative.startswith(".git"):
        return False, "required_for_active_prospective_experiment", "Git activation freeze"
    return False, "required_only_for_compact_audit_history", "retained document, code, compact result, manifest or uncertain small file"


def inventory(path: Path) -> dict:
    tracked = git_files()
    rows = []
    for item in sorted(ROOT.rglob("*")):
        if item.is_symlink():
            size, kind = 0, "symlink"
        elif item.is_file():
            size, kind = item.stat().st_size, "file"
        elif item.is_dir():
            size, kind = 0, "directory"
        else:
            continue
        relative = str(item.relative_to(ROOT))
        delete, classification, reason = planned_delete(relative, item)
        if relative in tracked and delete:
            raise RuntimeError(f"Refusing to classify Git-tracked file for deletion: {relative}")
        rows.append({"path": relative, "type": kind, "bytes": size,
                     "mtime_utc": datetime.fromtimestamp(item.lstat().st_mtime, timezone.utc).isoformat(),
                     "git_tracked": relative in tracked, "classification": classification,
                     "reason": reason, "planned_action": "delete" if delete else "retain"})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    return {"rows": len(rows), "file_bytes": sum(row["bytes"] for row in rows if row["type"] == "file")}


def prepare() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    before = inventory(OUT / "inventory_before.csv")
    retained = OUT / "retained_manifests"
    retained.mkdir(exist_ok=True)
    copies = {
        RAW_CKPT2 / "manifest.json": retained / "checkpoint2_full_universe_manifest.json",
        ROOT / "data/raw/yfinance_phase1b/2026-06-21T204918Z/manifest.json": retained / "checkpoint1_capability_manifest.json",
        ROOT / "data/raw/yfinance_phase1b_checkpoint3/intraday_smoke/2026-06-22T_readiness_v2Z/manifest.json": retained / "superseded_intraday_manifest.json",
    }
    for source, target in copies.items():
        if source.exists(): shutil.copy2(source, target)
    rows = []
    with (OUT / "inventory_before.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["planned_action"] == "delete" and row["type"] in {"file", "symlink"}:
                rows.append({"path": row["path"], "bytes": row["bytes"], "classification": row["classification"],
                             "reason": row["reason"], "status": "planned_not_deleted"})
    with (OUT / "deletion_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    dependency_rows = [
        {"path": "research/configs/yfinance_forward_simplified_v2.json", "classification": "active", "reason": "frozen strategy"},
        {"path": "src/paper/simple_ledger.py", "classification": "active", "reason": "active ledger"},
        {"path": "data/archive/yfinance_phase1b_cas/manifests/2026-06-22T_currentZ.json", "classification": "active", "reason": "canonical baseline snapshot"},
        {"path": "outputs/storage_cleanup/retained_manifests/checkpoint2_full_universe_manifest.json", "classification": "active", "reason": "compact logical manifest"},
        {"path": "outputs/experiment_runs/EXP-0014", "classification": "audit", "reason": "compact score/semantic evidence except regenerable factor-level table"},
        {"path": "outputs/experiment_runs/EXP-0016/daily_rehearsal_2", "classification": "audit", "reason": "latest valid simplified rehearsal"},
        {"path": ".venv", "classification": "uncertain_retained", "reason": "currently used tested environment"},
        {"path": "data/raw/yfinance", "classification": "uncertain_retained", "reason": "Phase 1A non-CAS reconstruction dependency"},
    ]
    with (OUT / "retained_dependencies.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=dependency_rows[0].keys()); writer.writeheader(); writer.writerows(dependency_rows)
    print(json.dumps({"prepared": True, "inventory": before, "planned_delete_files": len(rows)}))


def validate_archive(reconstruct: Path, delete_orphans: bool, require_original: bool, report_path: Path) -> None:
    manifest = json.loads(CAS_MANIFEST.read_text())
    referenced = set()
    logical_failures = []
    object_failures = []
    compared_original = 0
    if reconstruct.exists(): shutil.rmtree(reconstruct)
    reconstruct.mkdir(parents=True)
    for entry in manifest["files"]:
        object_path = CAS / entry["object"]
        referenced.add(object_path.resolve())
        if not object_path.exists():
            object_failures.append({"object": entry["object"], "reason": "missing"}); continue
        try: raw = gzip.decompress(object_path.read_bytes())
        except Exception as error:
            object_failures.append({"object": entry["object"], "reason": type(error).__name__}); continue
        if sha(raw) != entry["sha256"] or len(raw) != int(entry["bytes"]):
            object_failures.append({"object": entry["object"], "reason": "checksum_or_size"}); continue
        target = reconstruct / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        original = RAW_CKPT2 / entry["path"]
        if original.exists():
            compared_original += 1
            if sha(original.read_bytes()) != entry["sha256"]: logical_failures.append(entry["path"])
    all_objects = {path.resolve() for path in (CAS / "objects").rglob("*.gz")}
    orphans = sorted(all_objects - referenced)
    orphan_bytes = sum(path.stat().st_size for path in orphans)
    if delete_orphans and not object_failures and not logical_failures:
        for path in orphans: path.unlink()
    report = {"schema": "YF-CAS-CLEANUP-1.0.0", "manifest": str(CAS_MANIFEST.relative_to(ROOT)),
              "logical_files": len(manifest["files"]), "referenced_unique_objects": len(referenced),
              "all_objects_before": len(all_objects), "object_failures": object_failures,
              "logical_original_comparisons": compared_original, "logical_original_failures": logical_failures,
              "reconstructed_files": sum(1 for p in reconstruct.rglob("*") if p.is_file()),
              "orphan_objects": len(orphans), "orphan_bytes": orphan_bytes,
              "orphans_deleted": len(orphans) if delete_orphans and not object_failures and not logical_failures else 0,
              "original_comparison_required": require_original,
              "validation_pass": not object_failures and not logical_failures and
              (not require_original or compared_original == len(manifest["files"]))}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report))
    if not report["validation_pass"]: raise SystemExit(1)


def execute() -> None:
    report = json.loads((OUT / "archive_validation.json").read_text())
    if not report.get("validation_pass"):
        raise SystemExit("Archive validation must pass before deletion")
    tracked = git_files()
    deleted = []
    for prefix in DELETE_PREFIXES:
        path = ROOT / prefix
        if path.exists():
            for item in path.rglob("*"):
                if item.is_file() and str(item.relative_to(ROOT)) in tracked:
                    raise RuntimeError(f"Tracked deletion refused: {item}")
            size = sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
            shutil.rmtree(path); deleted.append((prefix, size))
    for relative in DELETE_FILES:
        path = ROOT / relative
        if path.exists():
            if relative in tracked: raise RuntimeError(f"Tracked deletion refused: {relative}")
            size = path.stat().st_size; path.unlink(); deleted.append((relative, size))
    for path in sorted(ROOT.rglob("*"), reverse=True):
        relative = str(path.relative_to(ROOT))
        if relative.startswith(".git/") or relative.startswith(".venv/"): continue
        if path.is_file() and (path.name == ".DS_Store" or path.suffix in CACHE_SUFFIXES):
            if relative not in tracked: deleted.append((relative, path.stat().st_size)); path.unlink()
        elif path.is_dir() and path.name in CACHE_NAMES:
            size = sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
            shutil.rmtree(path); deleted.append((relative, size))
    status = {path: "deleted" for path, _ in deleted}
    rows = []
    with (OUT / "deletion_manifest.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            row["status"] = "deleted" if not (ROOT / row["path"]).exists() else "retained"
            rows.append(row)
    with (OUT / "deletion_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    inventory(OUT / "inventory_after.csv")
    print(json.dumps({"deleted_paths": len(deleted), "deleted_bytes": sum(size for _, size in deleted)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=["prepare", "validate", "execute"])
    parser.add_argument("--reconstruct", type=Path, default=Path("/tmp/yf_checkpoint2_cleanup_reconstruction"))
    parser.add_argument("--delete-orphans", action="store_true")
    parser.add_argument("--allow-missing-original", action="store_true")
    parser.add_argument("--report", type=Path, default=OUT / "archive_validation.json")
    args = parser.parse_args()
    if args.command == "prepare": prepare()
    elif args.command == "validate": validate_archive(
        args.reconstruct, args.delete_orphans, not args.allow_missing_original, args.report
    )
    else: execute()
