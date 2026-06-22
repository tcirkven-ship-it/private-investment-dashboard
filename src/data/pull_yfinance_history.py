#!/usr/bin/env python3
"""Download auditable daily Yahoo Finance extracts through yfinance.

This is a prototype price/action source. It is not a historical universe,
delisting-return database, or point-in-time fundamental database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_for_json(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): clean_for_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_for_json(item) for item in value]
    return str(value)


def fetch_history(
    ticker: str,
    *,
    period: str,
    start: str | None,
    end: str | None,
    attempts: int,
) -> tuple[pd.DataFrame, dict[str, object]]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            instrument = yf.Ticker(ticker)
            kwargs: dict[str, object] = {
                "interval": "1d",
                "auto_adjust": False,
                "back_adjust": False,
                "actions": True,
                "repair": False,
                "keepna": True,
                "timeout": 30,
            }
            if start or end:
                kwargs["start"] = start
                kwargs["end"] = end
            else:
                kwargs["period"] = period

            history = instrument.history(**kwargs)
            if history.empty:
                raise RuntimeError(f"{ticker}: Yahoo returned no rows")
            metadata = clean_for_json(instrument.get_history_metadata(repair=False))
            return history, metadata if isinstance(metadata, dict) else {"metadata": metadata}
        except Exception as exc:  # yfinance surfaces several transport exceptions.
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** (2 * attempt))
    assert last_error is not None
    raise last_error


def write_extract(ticker: str, history: pd.DataFrame, metadata: dict[str, object], output: Path) -> dict[str, object]:
    ticker_dir = output / ticker.upper().replace("/", "_")
    ticker_dir.mkdir(parents=False, exist_ok=False)

    history_out = history.copy()
    history_out.index.name = "Date"
    history_path = ticker_dir / "history_daily.csv"
    history_out.to_csv(history_path, date_format="%Y-%m-%dT%H:%M:%S%z")

    action_columns = [name for name in ("Dividends", "Stock Splits", "Capital Gains") if name in history_out.columns]
    actions = history_out[action_columns].copy()
    if action_columns:
        actions = actions[(actions != 0).any(axis=1)]
    actions_path = ticker_dir / "actions.csv"
    actions.to_csv(actions_path, date_format="%Y-%m-%dT%H:%M:%S%z")

    metadata_path = ticker_dir / "history_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    nonmissing_close = history_out["Close"].dropna()
    return {
        "ticker": ticker.upper(),
        "rows": int(len(history_out)),
        "first_nonmissing_date": str(nonmissing_close.index.min()) if not nonmissing_close.empty else None,
        "last_nonmissing_date": str(nonmissing_close.index.max()) if not nonmissing_close.empty else None,
        "columns": list(history_out.columns),
        "nonzero_action_rows": int(len(actions)),
        "files": {
            "history": {"path": str(history_path), "sha256": sha256(history_path)},
            "actions": {"path": str(actions_path), "sha256": sha256(actions_path)},
            "metadata": {"path": str(metadata_path), "sha256": sha256(metadata_path)},
        },
    }


def summarize_existing(ticker: str, output: Path) -> dict[str, object]:
    ticker_dir = output / ticker.upper().replace("/", "_")
    history_path = ticker_dir / "history_daily.csv"
    actions_path = ticker_dir / "actions.csv"
    metadata_path = ticker_dir / "history_metadata.json"
    if not all(path.is_file() for path in (history_path, actions_path, metadata_path)):
        raise FileNotFoundError(f"Incomplete existing extract for {ticker}")

    history = pd.read_csv(history_path, index_col="Date", parse_dates=True)
    actions = pd.read_csv(actions_path)
    nonmissing_close = history["Close"].dropna()
    return {
        "ticker": ticker.upper(),
        "rows": int(len(history)),
        "first_nonmissing_date": str(nonmissing_close.index.min()) if not nonmissing_close.empty else None,
        "last_nonmissing_date": str(nonmissing_close.index.max()) if not nonmissing_close.empty else None,
        "columns": list(history.columns),
        "nonzero_action_rows": int(len(actions)),
        "files": {
            "history": {"path": str(history_path), "sha256": sha256(history_path)},
            "actions": {"path": str(actions_path), "sha256": sha256(actions_path)},
            "metadata": {"path": str(metadata_path), "sha256": sha256(metadata_path)},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    ticker_source = parser.add_mutually_exclusive_group(required=True)
    ticker_source.add_argument("--tickers", nargs="+")
    ticker_source.add_argument("--tickers-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--period", default="max")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--delay-seconds", type=float, default=2.0)
    parser.add_argument("--cache-dir", type=Path, default=Path("data/metadata/yfinance_cache"))
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if args.tickers_file:
        args.tickers = [
            line.strip()
            for line in args.tickers_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    args.tickers = list(dict.fromkeys(ticker.strip().upper() for ticker in args.tickers))
    if not args.tickers:
        raise SystemExit("No tickers supplied")

    if args.output.exists() and any(args.output.iterdir()) and not args.resume:
        raise SystemExit(f"Refusing to overwrite non-empty output directory: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)

    args.cache_dir.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(args.cache_dir))
    yf.config.debug.hide_exceptions = False
    retrieved_at = datetime.now(timezone.utc).isoformat()
    results: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []

    for index, ticker in enumerate(args.tickers):
        normalized = ticker.strip().upper()
        existing_dir = args.output / normalized.replace("/", "_")
        if args.resume and existing_dir.is_dir():
            results.append(summarize_existing(normalized, args.output))
            continue
        if index:
            time.sleep(args.delay_seconds)
        try:
            history, metadata = fetch_history(
                normalized,
                period=args.period,
                start=args.start,
                end=args.end,
                attempts=args.attempts,
            )
            results.append(write_extract(normalized, history, metadata, args.output))
            if len(results) % 10 == 0:
                print(json.dumps({"downloaded_or_resumed": len(results), "failures": len(failures)}), flush=True)
        except Exception as exc:
            failures.append({"ticker": normalized, "error_type": type(exc).__name__, "message": str(exc)})

    manifest = {
        "source": "Yahoo Finance via yfinance",
        "yfinance_version": yf.__version__,
        "retrieved_at_utc": retrieved_at,
        "parameters": {
            "tickers": [ticker.upper() for ticker in args.tickers],
            "period": args.period,
            "start": args.start,
            "end": args.end,
            "interval": "1d",
            "auto_adjust": False,
            "back_adjust": False,
            "actions": True,
            "repair": False,
            "keepna": True,
        },
        "classification": "prototype_price_and_corporate_action_extract_only",
        "limitations": [
            "Personal-use Yahoo data obtained through an unofficial open-source client.",
            "No complete historical universe, permanent security identifiers, or delisting returns.",
            "Upstream values and availability can change without a versioned vendor snapshot.",
            "Yahoo financial statements are not point-in-time fundamentals and are excluded from strategy backtests.",
        ],
        "successes": results,
        "failures": failures,
    }
    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"successes": len(results), "failures": len(failures), "manifest": str(manifest_path)}))
    return 0 if results and not failures else 1


if __name__ == "__main__":
    sys.exit(main())
