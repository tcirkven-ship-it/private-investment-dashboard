#!/usr/bin/env python3
"""Create the immutable Checkpoint 3 readiness manifest and rehearsal comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yfinance as yf


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree(directory: Path) -> dict[str, str]:
    return {str(path.relative_to(directory)): sha(path) for path in sorted(directory.rglob("*")) if path.is_file()}


def git_hash() -> str | None:
    result = subprocess.run(["git", "rev-parse", "HEAD"], text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else None


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tests", type=int, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    first, second = args.output / "rehearsal_3", args.output / "rehearsal_4"
    first_tree, second_tree = tree(first), tree(second)
    comparison = {"rehearsal_1_files": len(first_tree), "rehearsal_2_files": len(second_tree),
                  "byte_identical": first_tree == second_tree,
                  "rehearsal_1_tree_sha256": hashlib.sha256(json.dumps(first_tree, sort_keys=True).encode()).hexdigest(),
                  "rehearsal_2_tree_sha256": hashlib.sha256(json.dumps(second_tree, sort_keys=True).encode()).hexdigest(),
                  "differences": sorted(set(first_tree) ^ set(second_tree)) + sorted(k for k in set(first_tree) & set(second_tree) if first_tree[k] != second_tree[k])}
    write(args.output / "rehearsal_comparison.json", comparison)
    tracked = [
        "research/configs/yfinance_forward_readiness_v1.json", "research/configs/yfinance_forward_environment_lock.txt",
        "research/configs/yfinance_statement_aliases_v1.json", "src/paper/universe.py", "src/paper/ledger.py",
        "src/validation/run_yfinance_intraday_smoke.py", "src/validation/run_yfinance_activation_rehearsal.py",
        "src/validation/finalize_yfinance_readiness.py",
        "tests/test_yfinance_paper_readiness.py", "research/35_yfinance_universe_refresh_policy.md",
        "research/36_yfinance_execution_convention.md", "research/37_yfinance_paper_ledger_validation.md",
        "research/38_yfinance_benchmark_parity.md", "research/39_yfinance_success_protocol.md",
        "research/40_yfinance_activation_readiness.md", "outputs/final/yfinance_activation_checklist.md",
        "handoff.md", "research/decision_log.md", "research/experiment_registry.csv", "research/contradictions.md",
        "data/raw/yfinance_phase1b_checkpoint3/intraday_smoke/2026-06-22T_readiness_v2Z/manifest.json",
        "data/raw/yfinance_phase1b_checkpoint2/2026-06-22T_currentZ/manifest.json",
        "outputs/experiment_runs/EXP-0014/analysis_manifest.json"
    ]
    files = [{"path": name, "bytes": (args.root / name).stat().st_size, "sha256": sha(args.root / name)} for name in tracked]
    commit = git_hash()
    summary = {"checkpoint": "Phase 1B Checkpoint 3", "decision": "FAIL_NOT_READY_TO_ACTIVATE",
               "activation_changed": False, "yf_fwd_001_status": "registered_not_started",
               "tests_passed": args.tests, "rehearsals_byte_identical": comparison["byte_identical"],
               "git_commit_hash": commit, "git_gate_pass": commit is not None,
               "complete_cost_gate_pass": False, "cost_blocker": "IBKR Tiered third-party venue/regulatory/pass-through fees not frozen",
               "python_version": sys.version.split()[0], "yfinance_version": yf.__version__, "files": files}
    write(args.output / "readiness_summary.json", summary)
    manifest_files = [{"path": path.name, "bytes": path.stat().st_size, "sha256": sha(path)}
                      for path in sorted(args.output.iterdir()) if path.is_file() and path.name != "readiness_manifest.json"]
    write(args.output / "readiness_manifest.json", {"schema": "YF-READINESS-1.0.0", "files": manifest_files,
                                                      "external_files": files})
    print(json.dumps(summary, sort_keys=True))
    return 0 if comparison["byte_identical"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
