#!/usr/bin/env python3
"""Assemble development and evaluation Price results into final machine-readable tables."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
LABEL = "Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe."


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def combine(name: str) -> pd.DataFrame:
    frames = []
    for experiment, stage in (("EXP-0021", "development"), ("EXP-0022", "evaluation")):
        frame = pd.read_csv(ROOT / "outputs/experiment_runs" / experiment / name)
        frame.insert(0, "evidence_label", LABEL)
        frame.insert(1, "source_experiment", experiment)
        frame.insert(2, "research_stage", stage)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    final = ROOT / "outputs/final"
    folds = combine("fold_results.csv")
    configurations = combine("configuration_results.csv")
    if len(folds) != 288 * 11:
        raise RuntimeError(f"Expected 3,168 fold rows, found {len(folds)}")
    if len(configurations) != 288 * 2:
        raise RuntimeError(f"Expected 576 configuration rows, found {len(configurations)}")
    folds.to_csv(final / "price_results_by_fold.csv", index=False)
    configurations.to_csv(final / "price_results_by_configuration.csv", index=False)

    selected_id = json.loads((ROOT / "outputs/experiment_runs/EXP-0021/frozen_operational_choice.json").read_text())["selected_configuration_id"]
    selected = configurations[configurations.configuration_id.eq(selected_id)].copy()
    def row_dict(frame: pd.DataFrame) -> dict:
        return {key: (None if pd.isna(value) else value) for key, value in frame.iloc[0].to_dict().items()}

    summary = {
        "evidence_label": LABEL,
        "selected_configuration_id": selected_id,
        "development": row_dict(selected[selected.research_stage.eq("development")]),
        "evaluation": row_dict(selected[selected.research_stage.eq("evaluation")]),
        "fold_rows": len(folds),
        "configuration_rows": len(configurations),
    }
    summary_path = ROOT / "outputs/experiment_runs/EXP-0022/assembled_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str, allow_nan=False) + "\n"
    )
    manifest_path = ROOT / "outputs/experiment_runs/EXP-0022/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][summary_path.name] = {"sha256": sha256(summary_path), "bytes": summary_path.stat().st_size}
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"fold_rows": len(folds), "configuration_rows": len(configurations), "selected": selected_id}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
