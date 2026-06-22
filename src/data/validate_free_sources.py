#!/usr/bin/env python3
"""Validate immutable zero-cost source snapshots and emit a machine-readable report."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path


EXPECTED = {
    "NASDAQXNDX.csv": {
        "header": ["observation_date", "NASDAQXNDX"],
        "sha256": "fd7c25868fe8a6bffe613da6ef71671ae3e79660c723d236e84e64dd6a54eebb",
        "return_type": "total_return_index",
    },
    "NASDAQXCMP.csv": {
        "header": ["observation_date", "NASDAQXCMP"],
        "sha256": "836a376d43e9ad33d49947a7d79aad5eebe99e2f7510ae15ddbe7e6b7a0cdb24",
        "return_type": "total_return_index",
    },
    "SP500.csv": {
        "header": ["observation_date", "SP500"],
        "sha256": "35642a8c7dfb11155b8979bfe6664b9a7cd3832061863d351d37415d5f01e83a",
        "return_type": "price_index_excluding_dividends",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_file(path: Path, expected: dict[str, str | list[str]]) -> dict[str, object]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    header = rows[0] if rows else []
    data = rows[1:]
    parsed_dates: list[date] = []
    missing_values = 0
    malformed_rows = 0

    for row in data:
        if len(row) != 2:
            malformed_rows += 1
            continue
        parsed_dates.append(date.fromisoformat(row[0]))
        if row[1] in {"", "."}:
            missing_values += 1
        else:
            float(row[1])

    duplicates = len(parsed_dates) - len(set(parsed_dates))
    chronological = parsed_dates == sorted(parsed_dates)
    file_hash = sha256(path)
    checks = {
        "file_exists": path.is_file(),
        "header_matches": header == expected["header"],
        "checksum_matches_manifest": file_hash == expected["sha256"],
        "no_malformed_rows": malformed_rows == 0,
        "dates_strictly_unique": duplicates == 0,
        "dates_chronological": chronological,
        "has_nonmissing_values": missing_values < len(data),
    }
    nonmissing = [row for row in data if len(row) == 2 and row[1] not in {"", "."}]

    return {
        "file": path.name,
        "sha256": file_hash,
        "return_type": expected["return_type"],
        "data_rows": len(data),
        "missing_values": missing_values,
        "malformed_rows": malformed_rows,
        "duplicate_dates": duplicates,
        "first_nonmissing_date": nonmissing[0][0] if nonmissing else None,
        "last_nonmissing_date": nonmissing[-1][0] if nonmissing else None,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    results = [validate_file(args.input_dir / name, expected) for name, expected in EXPECTED.items()]
    report = {
        "experiment_id": "EXP-0004",
        "validation_scope": "zero_cost_fred_source_snapshot",
        "overall_status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL",
        "files": results,
        "interpretation": {
            "NASDAQXNDX.csv": "Eligible as a theoretical Nasdaq-100 total-return reference.",
            "NASDAQXCMP.csv": "Eligible as an additional Nasdaq Composite total-return reference.",
            "SP500.csv": "Diagnostic only: price index excludes dividends and cannot be the primary S&P 500 benchmark.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"overall_status": report["overall_status"], "output": str(args.output)}))
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
