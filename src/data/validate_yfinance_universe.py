#!/usr/bin/env python3
"""Validate a multi-ticker immutable yfinance snapshot and summarize coverage."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS = {
    "Open",
    "High",
    "Low",
    "Close",
    "Adj Close",
    "Volume",
    "Dividends",
    "Stock Splits",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--tickers-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads((args.snapshot / "manifest.json").read_text(encoding="utf-8"))
    registered = [line.strip().upper() for line in args.tickers_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    success_by_ticker = {row["ticker"]: row for row in manifest["successes"]}
    ticker_results: list[dict[str, object]] = []
    coverage_dates = [pd.Timestamp(value) for value in ("2010-01-04", "2015-01-02", "2020-01-02", "2023-01-03", "2026-06-18")]
    coverage = {str(date.date()): 0 for date in coverage_dates}

    for ticker in registered:
        entry = success_by_ticker.get(ticker)
        if not entry:
            ticker_results.append({"ticker": ticker, "status": "FAIL", "reason": "missing_from_manifest"})
            continue
        history_path = Path(entry["files"]["history"]["path"])
        actions_path = Path(entry["files"]["actions"]["path"])
        metadata_path = Path(entry["files"]["metadata"]["path"])
        history = pd.read_csv(history_path)
        dates = pd.to_datetime(history["Date"], utc=True).dt.tz_convert(None).dt.normalize()
        numeric = history.drop(columns=["Date"]).apply(pd.to_numeric, errors="coerce")
        checks = {
            "history_checksum": bool(sha256(history_path) == entry["files"]["history"]["sha256"]),
            "actions_checksum": bool(sha256(actions_path) == entry["files"]["actions"]["sha256"]),
            "metadata_checksum": bool(sha256(metadata_path) == entry["files"]["metadata"]["sha256"]),
            "row_count": bool(len(history) == entry["rows"]),
            "columns": bool(EXPECTED_COLUMNS.issubset(history.columns)),
            "dates_unique": bool(not dates.duplicated().any()),
            "dates_chronological": bool(dates.is_monotonic_increasing),
            "positive_adjusted_close": bool((numeric["Adj Close"].dropna() > 0).all()),
            "nonnegative_volume": bool((numeric["Volume"].dropna() >= 0).all()),
            "nonnegative_dividends": bool((numeric["Dividends"].dropna() >= 0).all()),
            "nonnegative_splits": bool((numeric["Stock Splits"].dropna() >= 0).all()),
        }
        valid_dates = dates[numeric["Adj Close"].notna()]
        for date in coverage_dates:
            prior = valid_dates[valid_dates <= date]
            if len(prior) >= 252 and prior.iloc[-1] >= date - pd.Timedelta(days=7):
                coverage[str(date.date())] += 1
        ticker_results.append(
            {
                "ticker": ticker,
                "status": "PASS" if all(checks.values()) else "FAIL",
                "rows": len(history),
                "first_date": str(valid_dates.iloc[0].date()),
                "last_date": str(valid_dates.iloc[-1].date()),
                "checks": checks,
            }
        )

    passes = sum(row["status"] == "PASS" for row in ticker_results)
    result = {
        "experiment_id": "EXP-0008",
        "scope": "OEF_current_universe_yfinance_price_action_validation",
        "registered_tickers": len(registered),
        "manifest_successes": len(manifest["successes"]),
        "manifest_failures": manifest["failures"],
        "ticker_passes": passes,
        "success_rate": passes / len(registered),
        "coverage_with_252_prior_observations": coverage,
        "ticker_results": ticker_results,
        "overall_status": "PASS" if passes / len(registered) >= 0.90 and not manifest["failures"] else "FAIL",
        "limitations": [
            "Universe is the current 2026 OEF holdings snapshot projected backward.",
            "Validation does not establish inactive-security or delisting-return completeness.",
            "Adjusted-close semantics are used for total-return research and actions remain separately auditable.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"overall_status": result["overall_status"], "passes": passes, "registered": len(registered), "output": str(args.output)}))
    if result["overall_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
