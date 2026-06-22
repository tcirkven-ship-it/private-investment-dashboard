#!/usr/bin/env python3
"""Validate a completed immutable Phase 1B yfinance capability snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--metadata-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest_path = args.snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sample = pd.read_csv(args.snapshot / "sample_universe.csv")
    checks = {
        "sample_at_least_100": len(sample) >= 100,
        "sample_tickers_unique": not sample["ticker"].duplicated().any(),
        "eleven_sectors_present": sample["sector_query"].nunique() == 11,
        "ten_or_more_each_sector": bool((sample["sector_query"].value_counts() >= 10).all()),
        "manifest_sample_matches_csv": int(manifest["sample_size"]) == len(sample),
        "yfinance_version_recorded": bool(manifest.get("yfinance_version")),
        "methods_recorded": len(manifest.get("methods_used", [])) >= 10,
    }

    endpoint_hash_checks = 0
    endpoint_hash_failures: list[dict[str, str]] = []
    missing_ticker_manifests: list[str] = []
    for ticker in sample["ticker"].astype(str):
        ticker_manifest_path = args.snapshot / "tickers" / ticker.replace("/", "_") / "ticker_manifest.json"
        if not ticker_manifest_path.exists():
            missing_ticker_manifests.append(ticker)
            continue
        ticker_manifest = json.loads(ticker_manifest_path.read_text(encoding="utf-8"))
        for endpoint, descriptor in ticker_manifest.get("files", {}).items():
            if "error" in descriptor:
                continue
            path = Path(descriptor["path"])
            endpoint_hash_checks += 1
            if not path.exists() or sha256(path) != descriptor["sha256"]:
                endpoint_hash_failures.append({"ticker": ticker, "endpoint": endpoint, "path": str(path)})
    checks["all_ticker_manifests_present"] = not missing_ticker_manifests
    checks["all_registered_endpoint_hashes_match"] = not endpoint_hash_failures

    inventory = []
    for path in sorted(value for value in args.snapshot.rglob("*") if value.is_file()):
        inventory.append(
            {
                "relative_path": str(path.relative_to(args.snapshot)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    args.metadata_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = args.metadata_dir / "snapshot_inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "snapshot": str(args.snapshot),
                "snapshot_manifest_sha256": sha256(manifest_path),
                "file_count": len(inventory),
                "total_bytes": sum(item["bytes"] for item in inventory),
                "files": inventory,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    result = {
        "experiment_id": "EXP-0012",
        "snapshot": str(args.snapshot),
        "snapshot_manifest_sha256": sha256(manifest_path),
        "snapshot_inventory": str(inventory_path),
        "inventory_sha256": sha256(inventory_path),
        "raw_file_count": len(inventory),
        "raw_total_bytes": sum(item["bytes"] for item in inventory),
        "endpoint_hash_checks": endpoint_hash_checks,
        "endpoint_hash_failures": endpoint_hash_failures,
        "missing_ticker_manifests": missing_ticker_manifests,
        "checks": checks,
        "overall_status": "PASS" if all(checks.values()) else "FAIL",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"overall_status": result["overall_status"], "raw_files": len(inventory), "hash_checks": endpoint_hash_checks}))
    if result["overall_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
