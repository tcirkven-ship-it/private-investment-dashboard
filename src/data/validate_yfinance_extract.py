#!/usr/bin/env python3
"""Validate a yfinance snapshot and reconcile ETF returns with free index references."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


EXPECTED_COLUMNS = {
    "Date",
    "Open",
    "High",
    "Low",
    "Close",
    "Adj Close",
    "Volume",
    "Dividends",
    "Stock Splits",
    "Capital Gains",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_history(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["date"] = pd.to_datetime(frame["Date"], utc=True).dt.date
    return frame


def validate_ticker(root: Path, item: dict[str, object]) -> tuple[dict[str, object], pd.DataFrame]:
    ticker = str(item["ticker"])
    ticker_dir = root / ticker
    history_path = ticker_dir / "history_daily.csv"
    actions_path = ticker_dir / "actions.csv"
    metadata_path = ticker_dir / "history_metadata.json"
    history = load_history(history_path)
    actions = pd.read_csv(actions_path)

    expected_files = item["files"]
    assert isinstance(expected_files, dict)
    checks = {
        "history_checksum": sha256(history_path) == expected_files["history"]["sha256"],
        "actions_checksum": sha256(actions_path) == expected_files["actions"]["sha256"],
        "metadata_checksum": sha256(metadata_path) == expected_files["metadata"]["sha256"],
        "columns_complete": EXPECTED_COLUMNS.issubset(history.columns),
        "row_count_matches": len(history) == int(item["rows"]),
        "dates_chronological": history["date"].tolist() == sorted(history["date"].tolist()),
        "dates_unique": not history["date"].duplicated().any(),
        "positive_nonmissing_close": bool((history["Close"].dropna() > 0).all()),
        "nonnegative_volume": bool((history["Volume"].dropna() >= 0).all()),
        "nonnegative_dividends": bool((history["Dividends"].dropna() >= 0).all()),
        "nonnegative_splits": bool((history["Stock Splits"].dropna() >= 0).all()),
        "action_row_count_matches": len(actions) == int(item["nonzero_action_rows"]),
    }
    result = {
        "ticker": ticker,
        "rows": len(history),
        "first_date": str(history["date"].min()),
        "last_date": str(history["date"].max()),
        "action_rows": len(actions),
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }
    return result, history


def load_fred(path: Path, value_column: str) -> pd.DataFrame:
    frame = pd.read_csv(path, na_values=".")
    frame["date"] = pd.to_datetime(frame["observation_date"]).dt.date
    return frame[["date", value_column]].dropna()


def return_reconciliation(
    etf: pd.DataFrame,
    etf_column: str,
    index: pd.DataFrame,
    index_column: str,
    start_date: str,
) -> dict[str, object]:
    merged = etf.merge(index, on="date").copy()
    merged = merged[merged["date"] >= pd.Timestamp(start_date).date()]
    etf_return = merged[etf_column].pct_change()
    index_return = merged[index_column].pct_change()
    active = etf_return - index_return
    correlation = float(etf_return.corr(index_return))
    tracking_error = float(active.std() * np.sqrt(252))
    annualized_mean_difference = float(active.mean() * 252)
    checks = {
        "at_least_500_overlapping_days": len(merged) >= 500,
        "daily_return_correlation_at_least_0_995": correlation >= 0.995,
        "annualized_tracking_error_below_0_02": tracking_error < 0.02,
    }
    return {
        "overlap_rows": len(merged),
        "start_date": str(merged["date"].min()),
        "end_date": str(merged["date"].max()),
        "daily_return_correlation": correlation,
        "annualized_tracking_error": tracking_error,
        "annualized_mean_return_difference": annualized_mean_difference,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--fred-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads((args.snapshot / "manifest.json").read_text(encoding="utf-8"))
    ticker_results: list[dict[str, object]] = []
    frames: dict[str, pd.DataFrame] = {}
    for item in manifest["successes"]:
        result, frame = validate_ticker(args.snapshot, item)
        ticker_results.append(result)
        frames[result["ticker"]] = frame

    qqq_reference = load_fred(args.fred_dir / "NASDAQXNDX.csv", "NASDAQXNDX")
    sp500_reference = load_fred(args.fred_dir / "SP500.csv", "SP500")
    reconciliations = {
        "QQQ_adjusted_vs_Nasdaq100_total_return_2021_onward": return_reconciliation(
            frames["QQQ"], "Adj Close", qqq_reference, "NASDAQXNDX", "2021-01-01"
        ),
        "SPY_unadjusted_close_vs_SP500_price_2021_onward": return_reconciliation(
            frames["SPY"], "Close", sp500_reference, "SP500", "2021-01-01"
        ),
    }
    overall = all(item["status"] == "PASS" for item in ticker_results) and all(
        item["status"] == "PASS" for item in reconciliations.values()
    )
    report = {
        "experiment_id": "EXP-0005",
        "scope": "yfinance_SPY_QQQ_price_action_viability",
        "overall_status": "PASS" if overall else "FAIL",
        "snapshot_manifest": str(args.snapshot / "manifest.json"),
        "ticker_validation": ticker_results,
        "benchmark_reconciliation": reconciliations,
        "decision": {
            "viable_for": [
                "personal-use prototype daily price and volume history",
                "SPY and QQQ investable benchmark ledgers",
                "dividend and split event inputs subject to independent checks",
                "current-universe engineering tests and forward paper tracking",
            ],
            "not_viable_for": [
                "historical universe reconstruction",
                "complete inactive and delisted security coverage",
                "delisting returns and terminal outcomes",
                "permanent effective-dated security identifiers",
                "point-in-time fundamental statement vintages",
                "definitive pass or conditional-pass strategy evidence by itself",
            ],
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"overall_status": report["overall_status"], "output": str(args.output)}))
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
