#!/usr/bin/env python3
"""Create an immutable yfinance-only capability snapshot.

The stock sample is constructed with yfinance's Yahoo equity screener, then
every selected ticker is queried through documented yfinance Ticker methods.
No non-yfinance market or fundamental source is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd
import yfinance as yf
from yfinance import EquityQuery


SECTORS = [
    "Technology",
    "Healthcare",
    "Financial Services",
    "Consumer Cyclical",
    "Consumer Defensive",
    "Industrials",
    "Communication Services",
    "Energy",
    "Basic Materials",
    "Real Estate",
    "Utilities",
]

MAIN_US_EXCHANGES = ["NMS", "NYQ", "ASE"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_json(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and pd.isna(value):
            return None
        return value
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [clean_json(item) for item in value]
    if hasattr(value, "item"):
        try:
            return clean_json(value.item())
        except Exception:
            pass
    return str(value)


def write_json(path: Path, value: object) -> dict[str, object]:
    path.write_text(json.dumps(clean_json(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}


def write_frame(path: Path, frame: pd.DataFrame | pd.Series | None) -> dict[str, object]:
    if frame is None:
        out = pd.DataFrame()
    elif isinstance(frame, pd.Series):
        out = frame.rename("value").to_frame()
    else:
        out = frame.copy()
    out.index.name = out.index.name or "index"
    out.to_csv(path, date_format="%Y-%m-%dT%H:%M:%S%z")
    return {
        "path": str(path),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "rows": int(out.shape[0]),
        "columns": int(out.shape[1]),
        "nonmissing_cells": int(out.notna().sum().sum()) if not out.empty else 0,
        "total_cells": int(out.shape[0] * out.shape[1]),
    }


def retry_call(label: str, function: Callable[[], object], attempts: int) -> tuple[object | None, dict[str, str] | None]:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return function(), None
        except Exception as exc:  # yfinance exposes multiple transport/parsing exceptions.
            last = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    assert last is not None
    return None, {"endpoint": label, "error_type": type(last).__name__, "message": str(last)}


def sector_query(sector: str) -> EquityQuery:
    return EquityQuery(
        "and",
        [
            EquityQuery("eq", ["region", "us"]),
            EquityQuery("is-in", ["exchange", *MAIN_US_EXCHANGES]),
            EquityQuery("eq", ["sector", sector]),
            EquityQuery("gte", ["intradaymarketcap", 1_000_000_000]),
            EquityQuery("gte", ["intradayprice", 5]),
            EquityQuery("gte", ["avgdailyvol3m", 200_000]),
        ],
    )


def build_sample(output: Path, sample_per_sector: int, candidates_per_sector: int, attempts: int) -> pd.DataFrame:
    screener_dir = output / "screener"
    screener_dir.mkdir()
    rows: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    for sector in SECTORS:
        response, error = retry_call(
            f"screen:{sector}",
            lambda sector=sector: yf.screen(
                sector_query(sector),
                size=candidates_per_sector,
                sortField="intradaymarketcap",
                sortAsc=False,
            ),
            attempts,
        )
        safe = sector.lower().replace(" ", "_")
        if error:
            errors.append({"sector": sector, **error})
            write_json(screener_dir / f"{safe}.error.json", error)
            continue
        assert isinstance(response, dict)
        write_json(screener_dir / f"{safe}.json", response)
        accepted = 0
        for rank, quote in enumerate(response.get("quotes", []), start=1):
            symbol = str(quote.get("symbol", "")).strip().upper()
            if not symbol or accepted >= sample_per_sector:
                continue
            rows.append(
                {
                    "ticker": symbol,
                    "sector_query": sector,
                    "sector_rank_by_market_cap": rank,
                    "exchange": quote.get("exchange"),
                    "quote_type": quote.get("quoteType"),
                    "market_cap": quote.get("marketCap"),
                    "price": quote.get("regularMarketPrice"),
                    "average_daily_volume_3m": quote.get("averageDailyVolume3Month"),
                    "short_name": quote.get("shortName"),
                    "long_name": quote.get("longName"),
                }
            )
            accepted += 1
    write_json(screener_dir / "errors.json", errors)
    sample = pd.DataFrame(rows).drop_duplicates("ticker", keep="first")
    sample.to_csv(output / "sample_universe.csv", index=False)
    return sample


def fetch_ticker(ticker: str, output: Path, attempts: int, endpoint_delay: float = 0.0) -> dict[str, object]:
    ticker_dir = output / "tickers" / ticker.replace("/", "_")
    ticker_dir.mkdir(parents=True)
    instrument = yf.Ticker(ticker)
    files: dict[str, object] = {}
    errors: list[dict[str, str]] = []

    def capture_json(name: str, function: Callable[[], object]) -> None:
        if endpoint_delay:
            time.sleep(endpoint_delay)
        value, error = retry_call(name, function, attempts)
        if error:
            errors.append(error)
            files[name] = {"error": error}
        else:
            files[name] = write_json(ticker_dir / f"{name}.json", value)

    def capture_frame(name: str, function: Callable[[], object]) -> None:
        if endpoint_delay:
            time.sleep(endpoint_delay)
        value, error = retry_call(name, function, attempts)
        if error:
            errors.append(error)
            files[name] = {"error": error}
            return
        if value is not None and not isinstance(value, (pd.DataFrame, pd.Series)):
            errors.append({"endpoint": name, "error_type": "UnexpectedType", "message": type(value).__name__})
            value = pd.DataFrame()
        files[name] = write_frame(ticker_dir / f"{name}.csv", value)

    capture_json("info", lambda: instrument.get_info())
    capture_json("fast_info", lambda: dict(instrument.fast_info))
    capture_frame(
        "history_daily",
        lambda: instrument.history(
            period="max",
            interval="1d",
            auto_adjust=False,
            back_adjust=False,
            actions=True,
            repair=False,
            keepna=True,
            timeout=30,
        ),
    )
    history_path = ticker_dir / "history_daily.csv"
    if history_path.exists():
        history = pd.read_csv(history_path, index_col=0)
        action_columns = [column for column in ("Dividends", "Stock Splits", "Capital Gains") if column in history.columns]
        actions = history[action_columns] if action_columns else pd.DataFrame(index=history.index)
        if action_columns:
            actions = actions[(actions.fillna(0) != 0).any(axis=1)]
        files["actions"] = write_frame(ticker_dir / "actions.csv", actions)

    statement_calls = {
        "annual_income": lambda: instrument.get_income_stmt(freq="yearly"),
        "quarterly_income": lambda: instrument.get_income_stmt(freq="quarterly"),
        "trailing_income": lambda: instrument.get_income_stmt(freq="trailing"),
        "annual_balance": lambda: instrument.get_balance_sheet(freq="yearly"),
        "quarterly_balance": lambda: instrument.get_balance_sheet(freq="quarterly"),
        "annual_cashflow": lambda: instrument.get_cash_flow(freq="yearly"),
        "quarterly_cashflow": lambda: instrument.get_cash_flow(freq="quarterly"),
        "trailing_cashflow": lambda: instrument.get_cash_flow(freq="trailing"),
    }
    for name, function in statement_calls.items():
        capture_frame(name, function)

    capture_frame("shares_full", lambda: instrument.get_shares_full(start="2000-01-01"))
    analyst_calls = {
        "earnings_history": instrument.get_earnings_history,
        "eps_revisions": instrument.get_eps_revisions,
        "eps_trend": instrument.get_eps_trend,
        "revenue_estimate": instrument.get_revenue_estimate,
        "earnings_estimate": instrument.get_earnings_estimate,
        "recommendations": instrument.get_recommendations,
        "recommendations_summary": instrument.get_recommendations_summary,
    }
    for name, function in analyst_calls.items():
        capture_frame(name, function)

    result = {
        "ticker": ticker,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": files,
        "errors": errors,
        "endpoint_successes": sum(1 for value in files.values() if isinstance(value, dict) and "error" not in value),
        "endpoint_errors": len(errors),
    }
    write_json(ticker_dir / "ticker_manifest.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-per-sector", type=int, default=10)
    parser.add_argument("--candidates-per-sector", type=int, default=25)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--delay-seconds", type=float, default=0.3)
    parser.add_argument("--cache-dir", type=Path, default=Path("data/metadata/yfinance_cache"))
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if args.output.exists() and any(args.output.iterdir()) and not args.resume:
        raise SystemExit(f"Refusing to overwrite non-empty snapshot: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(args.cache_dir))
    yf.config.debug.hide_exceptions = False
    started = datetime.now(timezone.utc).isoformat()

    sample_path = args.output / "sample_universe.csv"
    if args.resume and sample_path.exists():
        sample = pd.read_csv(sample_path)
    else:
        sample = build_sample(args.output, args.sample_per_sector, args.candidates_per_sector, args.attempts)
    if len(sample) < 100:
        raise SystemExit(f"Capability sample has only {len(sample)} tickers; at least 100 required")

    results: list[dict[str, object]] = []
    tickers_dir = args.output / "tickers"
    tickers_dir.mkdir(exist_ok=True)
    for index, ticker in enumerate(sample["ticker"].astype(str)):
        manifest_path = tickers_dir / ticker.replace("/", "_") / "ticker_manifest.json"
        if args.resume and manifest_path.exists():
            results.append(json.loads(manifest_path.read_text(encoding="utf-8")))
            continue
        if index:
            time.sleep(args.delay_seconds)
        result = fetch_ticker(ticker, args.output, args.attempts)
        results.append(result)
        print(json.dumps({"completed": len(results), "sample": len(sample), "ticker": ticker, "endpoint_errors": result["endpoint_errors"]}), flush=True)

    manifest = {
        "snapshot_id": args.output.name,
        "source": "Yahoo Finance accessed exclusively through yfinance",
        "yfinance_version": yf.__version__,
        "started_at_utc": started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "sample_design": {
            "method": "Custom yfinance EquityQuery separately by Yahoo sector, sorted by intraday market cap",
            "sectors": SECTORS,
            "sample_per_sector": args.sample_per_sector,
            "candidates_per_sector": args.candidates_per_sector,
            "region": "us",
            "exchanges": MAIN_US_EXCHANGES,
            "minimum_screener_market_cap": 1_000_000_000,
            "minimum_screener_price": 5,
            "minimum_screener_average_daily_volume_3m": 200_000,
            "current_universe_only": True,
        },
        "methods_used": [
            "yf.screen(EquityQuery)",
            "Ticker.get_info",
            "Ticker.fast_info",
            "Ticker.history",
            "Ticker.get_income_stmt(yearly|quarterly|trailing)",
            "Ticker.get_balance_sheet(yearly|quarterly)",
            "Ticker.get_cash_flow(yearly|quarterly|trailing)",
            "Ticker.get_shares_full",
            "Ticker.get_earnings_history",
            "Ticker.get_eps_revisions",
            "Ticker.get_eps_trend",
            "Ticker.get_revenue_estimate",
            "Ticker.get_earnings_estimate",
            "Ticker.get_recommendations",
            "Ticker.get_recommendations_summary",
        ],
        "sample_size": int(len(sample)),
        "ticker_results": results,
        "classification": "Phase 1B yfinance capability snapshot; current and potentially restated, not point in time",
        "limitations": [
            "Current yfinance screen and current ticker metadata do not reconstruct a historical universe.",
            "Yahoo statements may be restated and do not preserve historical retrieval vintages.",
            "Analyst estimates/revisions are current snapshots only.",
            "No complete inactive/delisted security master or delisting-return field is provided.",
        ],
    }
    write_json(args.output / "manifest.json", manifest)
    print(json.dumps({"status": "complete", "sample_size": len(sample), "manifest": str(args.output / "manifest.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
