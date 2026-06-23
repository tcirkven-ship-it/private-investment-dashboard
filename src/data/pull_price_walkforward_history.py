#!/usr/bin/env python3
"""Retrieve immutable maximum daily histories for the frozen Price experiment."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf


REQUIRED = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_history(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    frame = frame.copy().reset_index()
    date_column = "Date" if "Date" in frame.columns else frame.columns[0]
    frame = frame.rename(columns={date_column: "Date"})
    frame["Date"] = pd.to_datetime(frame["Date"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["Date"]).sort_values("Date").drop_duplicates("Date", keep="last")
    for column in REQUIRED + ["Dividends", "Stock Splits", "Capital Gains"]:
        if column not in frame:
            frame[column] = 0.0 if column in {"Dividends", "Stock Splits", "Capital Gains"} else pd.NA
    return frame[["Date", *REQUIRED, "Dividends", "Stock Splits", "Capital Gains"]]


def validate(frame: pd.DataFrame, ticker: str) -> None:
    if frame.empty:
        raise ValueError("empty_history")
    if frame["Date"].duplicated().any() or not frame["Date"].is_monotonic_increasing:
        raise ValueError("invalid_chronology")
    if frame["Adj Close"].notna().sum() < 2:
        raise ValueError("insufficient_adjusted_prices")
    positive = frame[["Open", "High", "Low", "Close", "Adj Close"]].dropna(how="all")
    if (positive <= 0).any(axis=None):
        raise ValueError(f"nonpositive_price:{ticker}")
    if (pd.to_numeric(frame["Volume"], errors="coerce").dropna() < 0).any():
        raise ValueError(f"negative_volume:{ticker}")


def fetch_one(ticker: str, output: Path, end_exclusive: str, retries: int) -> dict[str, object]:
    ticker_dir = output / "tickers" / ticker
    history_path = ticker_dir / "history_daily.csv"
    metadata_path = ticker_dir / "retrieval.json"
    if history_path.exists() and metadata_path.exists():
        existing = pd.read_csv(history_path)
        validate(existing, ticker)
        meta = json.loads(metadata_path.read_text())
        return {**meta, "status": "reused_completed_local", "history_sha256": sha256(history_path)}

    error = ""
    for attempt in range(1, retries + 1):
        started = datetime.now(timezone.utc).isoformat()
        try:
            frame = yf.Ticker(ticker).history(
                period="max",
                interval="1d",
                auto_adjust=False,
                actions=True,
                repair=False,
                timeout=30,
                raise_errors=True,
            )
            frame = normalize_history(frame)
            frame = frame.loc[frame["Date"] < pd.Timestamp(end_exclusive, tz="UTC")].copy()
            validate(frame, ticker)
            ticker_dir.mkdir(parents=True, exist_ok=True)
            frame.to_csv(history_path, index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
            actions = frame.loc[
                (pd.to_numeric(frame["Dividends"], errors="coerce").fillna(0) != 0)
                | (pd.to_numeric(frame["Stock Splits"], errors="coerce").fillna(0) != 0)
                | (pd.to_numeric(frame["Capital Gains"], errors="coerce").fillna(0) != 0),
                ["Date", "Dividends", "Stock Splits", "Capital Gains"],
            ]
            actions.to_csv(ticker_dir / "actions.csv", index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
            completed = datetime.now(timezone.utc).isoformat()
            record = {
                "ticker": ticker,
                "status": "downloaded",
                "attempts": attempt,
                "retrieval_started_at_utc": started,
                "retrieval_completed_at_utc": completed,
                "rows": int(len(frame)),
                "first_session": str(frame["Date"].iloc[0].date()),
                "last_session": str(frame["Date"].iloc[-1].date()),
                "adjusted_price_observations": int(frame["Adj Close"].notna().sum()),
                "history_sha256": sha256(history_path),
                "actions_sha256": sha256(ticker_dir / "actions.csv"),
                "error": "",
            }
            metadata_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
            return record
        except Exception as exc:  # upstream failures are preserved in the manifest
            error = f"{type(exc).__name__}: {exc}"
            if attempt < retries:
                time.sleep(min(30.0, 2.0 ** attempt))
    return {
        "ticker": ticker,
        "status": "failed",
        "attempts": retries,
        "retrieval_started_at_utc": started,
        "retrieval_completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows": 0,
        "first_session": None,
        "last_session": None,
        "adjusted_price_observations": 0,
        "history_sha256": None,
        "actions_sha256": None,
        "error": error,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--end-exclusive", default="2026-01-01")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--retries", type=int, default=4)
    args = parser.parse_args()

    universe = pd.read_csv(args.universe)
    tickers = sorted(set(universe["ticker"].dropna().astype(str)) | {"SPY", "QQQ"})
    args.output.mkdir(parents=True, exist_ok=True)
    invocation = datetime.now(timezone.utc).isoformat()
    records: list[dict[str, object]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(fetch_one, ticker, args.output, args.end_exclusive, args.retries): ticker
            for ticker in tickers
        }
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            record = future.result()
            records.append(record)
            completed += 1
            if completed % 25 == 0 or record["status"] == "failed":
                print(json.dumps({"completed": completed, "total": len(tickers), "last": record["ticker"], "status": record["status"]}), flush=True)

    records.sort(key=lambda item: str(item["ticker"]))
    report = pd.DataFrame(records)
    report.to_csv(args.output / "retrieval_report.csv", index=False)
    failures = report[report.status.eq("failed")]
    manifest = {
        "schema": "PRICE-WF-HISTORY-1.0.0",
        "provider": "yfinance",
        "yfinance_version": yf.__version__,
        "retrieval_invoked_at_utc": invocation,
        "retrieval_completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "end_exclusive": args.end_exclusive,
        "universe_path": str(args.universe),
        "universe_sha256": sha256(args.universe),
        "requested_ticker_count": len(tickers),
        "successful_ticker_count": int((~report.status.eq("failed")).sum()),
        "failed_ticker_count": int(len(failures)),
        "failed_tickers": failures.ticker.tolist(),
        "retrieval_report_sha256": sha256(args.output / "retrieval_report.csv"),
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, sort_keys=True))
    return 0 if failures.empty else 2


if __name__ == "__main__":
    raise SystemExit(main())
