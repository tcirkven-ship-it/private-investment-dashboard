#!/usr/bin/env python3
"""Archive and compare yfinance intraday intervals without strategy-return use."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf


SPECS = {"1m": "7d", "5m": "60d", "15m": "60d"}


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tickers", nargs="+", default=["SPY", "QQQ", "NTCT", "CRUS", "EIX", "CALM"])
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit(f"Refusing to overwrite {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    rows, files = [], []
    started = datetime.now(timezone.utc).isoformat()
    for interval, period in SPECS.items():
        for ticker in args.tickers:
            frame = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False, back_adjust=False,
                                               actions=False, prepost=False, repair=False, keepna=True, timeout=30)
            path = args.output / f"{ticker}_{interval}.csv"
            frame.to_csv(path, index_label="Datetime")
            sha = checksum(path)
            files.append({"path": path.name, "sha256": sha, "bytes": path.stat().st_size})
            if frame.empty:
                rows.append({"ticker": ticker, "interval": interval, "period": period, "rows": 0, "sessions": 0,
                             "window_sessions": 0, "duplicate_timestamps": 0, "missing_ohlc_rows": 0,
                             "window_missing_ohlc_rows": 0,
                             "first": None, "last": None, "bytes": path.stat().st_size, "sha256": sha})
                continue
            local = frame.copy()
            if local.index.tz is None:
                local.index = local.index.tz_localize("America/New_York")
            else:
                local.index = local.index.tz_convert("America/New_York")
            regular = local.between_time("09:30", "16:00", inclusive="left")
            window = local.between_time("15:45", "15:55", inclusive="both")
            window_missing = int(window[["Open", "High", "Low", "Close"]].isna().any(axis=1).sum())
            rows.append({"ticker": ticker, "interval": interval, "period": period, "rows": len(frame),
                         "sessions": regular.index.normalize().nunique(),
                         "window_sessions": window.index.normalize().nunique(),
                         "window_rows": len(window), "window_missing_ohlc_rows": window_missing,
                         "duplicate_timestamps": int(frame.index.duplicated().sum()),
                         "missing_ohlc_rows": int(frame[["Open", "High", "Low", "Close"]].isna().any(axis=1).sum()),
                         "first": str(frame.index.min()), "last": str(frame.index.max()),
                         "bytes": path.stat().st_size, "sha256": sha})
    summary = pd.DataFrame(rows)
    summary.to_csv(args.output / "availability_summary.csv", index=False)
    selection = summary.groupby("interval").agg(tickers=("ticker", "size"), nonempty=("rows", lambda x: int((x > 0).sum())),
        median_sessions=("sessions", "median"), minimum_window_sessions=("window_sessions", "min"),
        duplicate_timestamps=("duplicate_timestamps", "sum"), missing_ohlc_rows=("missing_ohlc_rows", "sum"),
        window_missing_ohlc_rows=("window_missing_ohlc_rows", "sum"),
        total_bytes=("bytes", "sum")).reset_index()
    selection["window_coverage"] = selection["minimum_window_sessions"] / selection["median_sessions"]
    selection.to_csv(args.output / "interval_comparison.csv", index=False)
    payload = {"experiment": "intraday_availability_smoke_no_strategy_returns", "started_at_utc": started,
               "completed_at_utc": datetime.now(timezone.utc).isoformat(), "tickers": args.tickers,
               "specifications": SPECS, "yfinance_version": yf.__version__, "files": files,
               "selection_rule": "Choose the finest interval with at least 20 observed sessions, complete 15:45-15:55 window coverage, zero duplicate timestamps, and zero missing OHLC inside that execution window. Missing inactive bars outside the window remain reason-coded.",
               "strategy_returns_examined": False}
    (args.output / "manifest.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(selection.to_json(orient="records"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
