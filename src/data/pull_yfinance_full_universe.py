#!/usr/bin/env python3
"""Retrieve a non-truncated current yfinance-only US equity research universe."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
import re
import shutil
import sys
import time
from datetime import datetime, time as datetime_time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yfinance as yf
from yfinance import EquityQuery

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.audit_yfinance_capabilities import (
    MAIN_US_EXCHANGES,
    SECTORS,
    clean_json,
    fetch_ticker,
    retry_call,
    sha256,
    write_frame,
    write_json,
)


INITIAL_BANDS = [
    (1_000_000_000, 2_000_000_000),
    (2_000_000_000, 5_000_000_000),
    (5_000_000_000, 10_000_000_000),
    (10_000_000_000, 25_000_000_000),
    (25_000_000_000, 50_000_000_000),
    (50_000_000_000, 100_000_000_000),
    (100_000_000_000, 250_000_000_000),
    (250_000_000_000, 500_000_000_000),
    (500_000_000_000, 1_000_000_000_000),
    (1_000_000_000_000, 10_000_000_000_000),
]

NONORDINARY_PATTERN = re.compile(
    r"\b(L\.?P\.?|LIMITED PARTNERSHIP|DEPOSITARY|WARRANT|RIGHTS?|UNITS?|ETF|FUND)\b",
    re.IGNORECASE,
)


def make_query(sector: str, lower: int, upper: int) -> EquityQuery:
    return EquityQuery(
        "and",
        [
            EquityQuery("eq", ["region", "us"]),
            EquityQuery("is-in", ["exchange", *MAIN_US_EXCHANGES]),
            EquityQuery("eq", ["sector", sector]),
            EquityQuery("gte", ["intradaymarketcap", lower]),
            EquityQuery("lt", ["intradaymarketcap", upper]),
            EquityQuery("gte", ["intradayprice", 5]),
            EquityQuery("gte", ["avgdailyvol3m", 200_000]),
        ],
    )


def retrieve_partition(
    sector: str,
    lower: int,
    upper: int,
    output: Path,
    query_records: list[dict[str, object]],
    quote_rows: list[dict[str, object]],
    attempts: int,
    depth: int = 0,
) -> None:
    query_id = f"q{len(query_records):04d}"
    query = make_query(sector, lower, upper)
    response, error = retry_call(
        f"screen:{sector}:{lower}:{upper}",
        lambda: yf.screen(query, size=250, sortField="intradaymarketcap", sortAsc=False),
        attempts,
    )
    spec = {
        "query_id": query_id,
        "sector": sector,
        "market_cap_lower_inclusive": lower,
        "market_cap_upper_exclusive": upper,
        "depth": depth,
        "query": query.to_dict(),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_json(output / f"{query_id}_query.json", spec)
    if error:
        write_json(output / f"{query_id}_error.json", error)
        query_records.append({**spec, "status": "ERROR", "error": error})
        raise RuntimeError(error)
    assert isinstance(response, dict)
    write_json(output / f"{query_id}_response.json", response)
    total = int(response.get("total", len(response.get("quotes", []))))
    returned = len(response.get("quotes", []))
    record = {**spec, "status": "OK", "reported_total": total, "returned": returned}
    query_records.append(record)

    if total > 250:
        if depth >= 16 or upper - lower <= 1_000_000:
            raise RuntimeError(f"Unable to split capped partition {sector} {lower}:{upper} total={total}")
        midpoint = int(math.sqrt(lower * upper))
        if midpoint <= lower or midpoint >= upper:
            midpoint = lower + (upper - lower) // 2
        record["split_at"] = midpoint
        retrieve_partition(sector, lower, midpoint, output, query_records, quote_rows, attempts, depth + 1)
        retrieve_partition(sector, midpoint, upper, output, query_records, quote_rows, attempts, depth + 1)
        return

    for quote in response.get("quotes", []):
        quote_rows.append(
            {
                "ticker": str(quote.get("symbol", "")).upper(),
                "query_id": query_id,
                "query_sector": sector,
                "market_cap_band_lower": lower,
                "market_cap_band_upper": upper,
                "screen_exchange": quote.get("exchange"),
                "screen_quote_type": quote.get("quoteType"),
                "screen_currency": quote.get("currency"),
                "screen_financial_currency": quote.get("financialCurrency"),
                "screen_market_cap": quote.get("marketCap"),
                "screen_price": quote.get("regularMarketPrice"),
                "screen_average_volume_3m": quote.get("averageDailyVolume3Month"),
                "screen_first_trade_ms": quote.get("firstTradeDateMilliseconds"),
                "screen_long_name": quote.get("longName"),
                "screen_short_name": quote.get("shortName"),
            }
        )


def retrieve_screened_universe(output: Path, attempts: int) -> pd.DataFrame:
    query_dir = output / "universe_queries"
    query_dir.mkdir()
    query_records: list[dict[str, object]] = []
    quote_rows: list[dict[str, object]] = []
    for sector in SECTORS:
        for lower, upper in INITIAL_BANDS:
            retrieve_partition(sector, lower, upper, query_dir, query_records, quote_rows, attempts)
    queries = pd.DataFrame(query_records)
    if "split_at" not in queries.columns:
        queries["split_at"] = np.nan
    queries.to_csv(output / "query_registry.csv", index=False)
    if (queries["reported_total"] > 250).any() and queries.loc[queries["reported_total"] > 250, "split_at"].isna().any():
        raise AssertionError("A capped partition was not split")
    quotes = pd.DataFrame(quote_rows)
    if quotes.empty:
        raise RuntimeError("No screened equities returned")
    duplicates = quotes[quotes.duplicated("ticker", keep=False)].sort_values("ticker")
    duplicates.to_csv(output / "screen_duplicate_rows.csv", index=False)
    quotes = quotes.sort_values(["ticker", "screen_market_cap"], ascending=[True, False]).drop_duplicates("ticker", keep="first")
    quotes.to_csv(output / "screened_universe.csv", index=False)
    return quotes


def normalize_issuer_name(name: object) -> str:
    text = re.sub(r"[^A-Z0-9 ]", " ", str(name).upper())
    removable = {
        "INC", "INCORPORATED", "CORP", "CORPORATION", "COMPANY", "CO", "PLC", "LTD", "LIMITED",
        "COMMON", "STOCK", "CLASS", "A", "B", "C", "HOLDING", "HOLDINGS",
    }
    return " ".join(token for token in text.split() if token not in removable)


def read_history_metrics(history: pd.DataFrame) -> dict[str, object]:
    if history.empty or "Close" not in history or "Volume" not in history:
        return {"history_observations": 0, "latest_close": None, "median_dollar_volume_63": None}
    current = datetime.now(timezone.utc).astimezone(ZoneInfo("America/New_York"))
    cutoff = pd.Timestamp(current.date())
    if current.weekday() >= 5 or current.time() < datetime_time(16, 15):
        cutoff -= pd.Timedelta(days=1)
    dates = pd.to_datetime(history.index, utc=True, errors="coerce").tz_convert(None).normalize()
    history = history.loc[np.asarray(dates <= cutoff)].copy()
    valid = history.dropna(subset=["Close"])
    dollar_volume = (pd.to_numeric(history["Close"], errors="coerce") * pd.to_numeric(history["Volume"], errors="coerce")).dropna()
    return {
        "history_observations": int(len(valid)),
        "latest_close": float(valid["Close"].iloc[-1]) if not valid.empty else None,
        "median_dollar_volume_63": float(dollar_volume.tail(63).median()) if len(dollar_volume.tail(63)) >= 55 else None,
    }


def enrich_candidates(screened: pd.DataFrame, output: Path, attempts: int, delay: float, resume: bool, workers: int) -> pd.DataFrame:
    enrichment_dir = output / "enrichment"
    enrichment_dir.mkdir(exist_ok=True)
    rows = []
    candidates = screened[screened["screen_market_cap"] >= 2_000_000_000].copy()

    def enrich_one(row: pd.Series) -> dict[str, object]:
        ticker = row["ticker"]
        ticker_dir = enrichment_dir / ticker.replace("/", "_")
        manifest_path = ticker_dir / "enrichment_manifest.json"
        if resume and manifest_path.exists():
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            saved = payload["row"]
            essential = [saved.get("info_exchange"), saved.get("info_quote_type"), saved.get("info_country"),
                         saved.get("info_currency"), saved.get("info_financial_currency"),
                         saved.get("info_market_cap"), saved.get("info_sector")]
            if all(value not in (None, "") for value in essential) and int(saved.get("history_observations") or 0) >= 504:
                return saved
        ticker_dir.mkdir(parents=True, exist_ok=True)
        if delay:
            time.sleep(delay)
        instrument = yf.Ticker(ticker)
        info, info_error = retry_call("info", instrument.get_info, attempts)
        history, history_error = retry_call(
            "history_3y",
            lambda: instrument.history(
                period="3y", interval="1d", auto_adjust=False, back_adjust=False,
                actions=True, repair=False, keepna=True, timeout=30,
            ),
            attempts,
        )
        info = info if isinstance(info, dict) else {}
        history = history if isinstance(history, pd.DataFrame) else pd.DataFrame()
        write_json(ticker_dir / "info.json", info)
        write_frame(ticker_dir / "history_3y.csv", history)
        metrics = read_history_metrics(history)
        name = info.get("longName") or row.get("screen_long_name") or info.get("shortName") or ticker
        nonordinary_match = NONORDINARY_PATTERN.search(str(name))
        enriched = {
            **row.to_dict(),
            "info_long_name": name,
            "normalized_issuer_name": normalize_issuer_name(name),
            "info_country": info.get("country"),
            "info_exchange": info.get("exchange"),
            "info_quote_type": info.get("quoteType"),
            "info_currency": info.get("currency"),
            "info_financial_currency": info.get("financialCurrency"),
            "info_market_cap": info.get("marketCap"),
            "info_sector": info.get("sector"),
            "info_industry": info.get("industry"),
            "info_enterprise_value": info.get("enterpriseValue"),
            "info_shares_outstanding": info.get("sharesOutstanding"),
            "nonordinary_name_match": nonordinary_match.group(0) if nonordinary_match else None,
            **metrics,
            "info_error": json.dumps(info_error) if info_error else None,
            "history_error": json.dumps(history_error) if history_error else None,
        }
        write_json(ticker_dir / "enrichment_manifest.json", {"ticker": ticker, "row": enriched})
        return enriched

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(enrich_one, row) for _, row in candidates.reset_index(drop=True).iterrows()]
        for completed, future in enumerate(as_completed(futures), start=1):
            rows.append(future.result())
            if completed % 25 == 0:
                print(json.dumps({"enriched": completed, "candidates": len(candidates)}), flush=True)
    result = pd.DataFrame(rows).sort_values("ticker")
    result.to_csv(output / "enriched_candidates.csv", index=False)
    return result


def apply_filters(enriched: pd.DataFrame, output: Path) -> pd.DataFrame:
    frame = enriched.copy()
    frame["pass_exchange"] = frame["info_exchange"].isin(MAIN_US_EXCHANGES)
    frame["pass_quote_type"] = frame["info_quote_type"].eq("EQUITY")
    frame["pass_country"] = frame["info_country"].eq("United States")
    frame["pass_currency"] = frame["info_currency"].eq("USD") & frame["info_financial_currency"].eq("USD")
    frame["pass_market_cap"] = pd.to_numeric(frame["info_market_cap"], errors="coerce").ge(2_000_000_000)
    frame["pass_price"] = pd.to_numeric(frame["latest_close"], errors="coerce").ge(5)
    frame["pass_history"] = pd.to_numeric(frame["history_observations"], errors="coerce").ge(504)
    frame["pass_liquidity"] = pd.to_numeric(frame["median_dollar_volume_63"], errors="coerce").ge(5_000_000)
    frame["pass_sector_present"] = frame["info_sector"].notna()
    frame["pass_financials_exclusion"] = ~frame["info_sector"].eq("Financial Services")
    frame["pass_real_estate_exclusion"] = ~frame["info_sector"].eq("Real Estate")
    frame["pass_nonordinary"] = frame["nonordinary_name_match"].isna()

    ordered = [
        "pass_exchange", "pass_quote_type", "pass_country", "pass_currency", "pass_market_cap",
        "pass_price", "pass_history", "pass_liquidity", "pass_sector_present",
        "pass_financials_exclusion", "pass_real_estate_exclusion", "pass_nonordinary",
    ]
    cumulative = pd.Series(True, index=frame.index)
    waterfall = [{"stage": "screened_market_cap_at_least_2b", "count": int(len(frame))}]
    first_reason = pd.Series("", index=frame.index, dtype=object)
    for column in ordered:
        newly_failed = cumulative & ~frame[column]
        first_reason.loc[newly_failed] = column.removeprefix("pass_")
        cumulative &= frame[column]
        waterfall.append({"stage": column.removeprefix("pass_"), "count": int(cumulative.sum())})
    frame["pass_pre_dedup"] = cumulative
    frame["first_exclusion_reason"] = first_reason.replace("", None)

    eligible = frame[frame["pass_pre_dedup"]].copy()
    eligible = eligible.sort_values(
        ["normalized_issuer_name", "info_market_cap", "median_dollar_volume_63", "ticker"],
        ascending=[True, False, False, True],
    )
    duplicated = eligible.duplicated("normalized_issuer_name", keep=False)
    dedup_rows = eligible[duplicated].copy()
    dedup_rows["dedup_retained"] = ~dedup_rows.duplicated("normalized_issuer_name", keep="first")
    dedup_rows.to_csv(output / "issuer_deduplication_decisions.csv", index=False)
    eligible["pass_issuer_dedup"] = ~eligible.duplicated("normalized_issuer_name", keep="first")
    removed = eligible.loc[~eligible["pass_issuer_dedup"], "ticker"]
    frame.loc[frame["ticker"].isin(removed), "first_exclusion_reason"] = "issuer_share_class_dedup"
    final = eligible[eligible["pass_issuer_dedup"]].copy()
    waterfall.append({"stage": "issuer_share_class_dedup", "count": int(len(final))})

    frame.to_csv(output / "eligibility_and_exclusions.csv", index=False)
    pd.DataFrame(waterfall).to_csv(output / "eligibility_waterfall.csv", index=False)
    final.to_csv(output / "base_eligible_universe.csv", index=False)
    (output / "base_eligible_tickers.txt").write_text("\n".join(final["ticker"]) + "\n", encoding="utf-8")
    return final


def fetch_benchmarks(output: Path, attempts: int, fallback_dir: Path | None = None) -> list[dict[str, object]]:
    benchmark_dir = output / "benchmarks"
    benchmark_dir.mkdir(exist_ok=True)
    rows = []
    for ticker in ("SPY", "QQQ"):
        history, error = retry_call(
            f"benchmark:{ticker}",
            lambda ticker=ticker: yf.Ticker(ticker).history(
                period="max", interval="1d", auto_adjust=False, back_adjust=False,
                actions=True, repair=False, keepna=True, timeout=30,
            ),
            attempts,
        )
        provenance = "retrieved_with_checkpoint2"
        if error and fallback_dir is not None:
            fallback = fallback_dir / ticker / "history_daily.csv"
            if fallback.exists():
                history = pd.read_csv(fallback, index_col=0)
                provenance = f"rate_limit_fallback_from_{fallback}; sha256={sha256(fallback)}"
                error = None
        if error:
            raise RuntimeError(error)
        descriptor = write_frame(benchmark_dir / f"{ticker}_history_daily.csv", history)
        rows.append({"ticker": ticker, "provenance": provenance, **descriptor})
    return rows


def scoring_core_complete(ticker_dir: Path) -> bool:
    info_path = ticker_dir / "info.json"
    try:
        info = json.loads(info_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return False
    if not isinstance(info, dict) or not info:
        return False
    for name, minimum_rows in [("history_daily.csv", 253), ("annual_income.csv", 1),
                               ("annual_balance.csv", 1), ("annual_cashflow.csv", 1)]:
        path = ticker_dir / name
        try:
            frame = pd.read_csv(path, index_col=0)
        except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError):
            return False
        if len(frame) < minimum_rows and frame.shape[1] < minimum_rows:
            return False
    return True


def fetch_scoring_core(ticker: str, output: Path, attempts: int, endpoint_delay: float) -> dict[str, object]:
    """Fetch only inputs used by frozen Q/V/P scoring; seed fresh info/history from enrichment."""
    ticker_dir = output / "tickers" / ticker.replace("/", "_")
    ticker_dir.mkdir(parents=True)
    seed_dir = output / "enrichment" / ticker.replace("/", "_")
    files: dict[str, object] = {}
    errors: list[dict[str, str]] = []
    for source_name, target_name in [("info.json", "info.json"), ("history_3y.csv", "history_daily.csv")]:
        source, target = seed_dir / source_name, ticker_dir / target_name
        shutil.copy2(source, target)
        files[target_name.removesuffix(".json").removesuffix(".csv")] = {
            "path": str(target), "sha256": sha256(target), "bytes": target.stat().st_size,
            "provenance": f"fresh_enrichment:{source}",
        }
    history = pd.read_csv(ticker_dir / "history_daily.csv", index_col=0)
    action_columns = [column for column in ("Dividends", "Stock Splits", "Capital Gains") if column in history.columns]
    actions = history[action_columns] if action_columns else pd.DataFrame(index=history.index)
    if action_columns:
        actions = actions[(actions.fillna(0) != 0).any(axis=1)]
    files["actions"] = write_frame(ticker_dir / "actions.csv", actions)
    instrument = yf.Ticker(ticker)
    calls = {
        "annual_income": lambda: instrument.get_income_stmt(freq="yearly"),
        "quarterly_income": lambda: instrument.get_income_stmt(freq="quarterly"),
        "trailing_income": lambda: instrument.get_income_stmt(freq="trailing"),
        "annual_balance": lambda: instrument.get_balance_sheet(freq="yearly"),
        "quarterly_balance": lambda: instrument.get_balance_sheet(freq="quarterly"),
        "annual_cashflow": lambda: instrument.get_cash_flow(freq="yearly"),
        "quarterly_cashflow": lambda: instrument.get_cash_flow(freq="quarterly"),
        "trailing_cashflow": lambda: instrument.get_cash_flow(freq="trailing"),
    }
    for name, function in calls.items():
        if endpoint_delay:
            time.sleep(endpoint_delay)
        value, error = retry_call(name, function, attempts)
        if error:
            errors.append(error); files[name] = {"error": error}
        else:
            files[name] = write_frame(ticker_dir / f"{name}.csv", value)
    result = {"ticker": ticker, "completed_at_utc": datetime.now(timezone.utc).isoformat(),
              "retrieval_scope": "frozen_qvp_scoring_core", "files": files, "errors": errors,
              "endpoint_successes": sum(1 for value in files.values() if isinstance(value, dict) and "error" not in value),
              "endpoint_errors": len(errors)}
    write_json(ticker_dir / "ticker_manifest.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--delay-seconds", type=float, default=0.1)
    parser.add_argument("--cache-dir", type=Path, default=Path("data/metadata/yfinance_cache"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--benchmark-fallback-dir", type=Path)
    parser.add_argument("--retry-endpoint-errors", action="store_true")
    parser.add_argument("--minimum-eligible", type=int, default=500)
    parser.add_argument("--maximum-final-endpoint-errors", type=int, default=-1,
                        help="Optional all-endpoint gate; -1 records errors without failing")
    parser.add_argument("--maximum-scoring-core-incomplete", type=int, default=0)
    parser.add_argument("--endpoint-delay-seconds", type=float, default=0.15)
    parser.add_argument("--enrichment-retry-passes", type=int, default=2)
    parser.add_argument("--scoring-core-retry-passes", type=int, default=2)
    parser.add_argument("--scoring-core-only", action="store_true")
    args = parser.parse_args()

    if args.output.exists() and any(args.output.iterdir()) and not args.resume:
        raise SystemExit(f"Refusing to overwrite non-empty snapshot: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(args.cache_dir))
    yf.config.debug.hide_exceptions = False
    started = datetime.now(timezone.utc).isoformat()

    screened_path = args.output / "screened_universe.csv"
    screened = pd.read_csv(screened_path) if args.resume and screened_path.exists() else retrieve_screened_universe(args.output, args.attempts)
    enriched = enrich_candidates(screened, args.output, args.attempts, args.delay_seconds, args.resume, args.workers)
    for retry_pass in range(1, args.enrichment_retry_passes + 1):
        essential_ok = (
            enriched[["info_exchange", "info_quote_type", "info_country", "info_currency",
                      "info_financial_currency", "info_market_cap", "info_sector"]].notna().all(axis=1)
            & pd.to_numeric(enriched["history_observations"], errors="coerce").ge(504)
        )
        if bool(essential_ok.all()):
            break
        print(json.dumps({"enrichment_retry_pass": retry_pass,
                          "incomplete_candidates": int((~essential_ok).sum())}), flush=True)
        enriched = enrich_candidates(screened, args.output, args.attempts, args.delay_seconds, True, args.workers)
    eligible = apply_filters(enriched, args.output)
    if len(eligible) < args.minimum_eligible:
        raise RuntimeError(
            f"Only {len(eligible)} eligible names; below integrity floor {args.minimum_eligible}. "
            "Retry incomplete enrichment rather than accepting a degraded universe."
        )

    force_core_retry = args.resume and args.retry_endpoint_errors

    def fetch_full(ticker: str) -> dict[str, object]:
        ticker_dir = args.output / "tickers" / ticker.replace("/", "_")
        ticker_manifest = ticker_dir / "ticker_manifest.json"
        if ticker_manifest.exists():
            completed = json.loads(ticker_manifest.read_text(encoding="utf-8"))
            if not force_core_retry or scoring_core_complete(ticker_dir):
                return completed
        if ticker_dir.exists():
            shutil.rmtree(ticker_dir)
        if args.delay_seconds:
            time.sleep(args.delay_seconds)
        if args.scoring_core_only:
            return fetch_scoring_core(ticker, args.output, args.attempts, args.endpoint_delay_seconds)
        return fetch_ticker(ticker, args.output, args.attempts, args.endpoint_delay_seconds)

    full_results = []
    scoring_core_incomplete: list[str] = []
    for core_pass in range(args.scoring_core_retry_passes + 1):
        force_core_retry = args.resume or core_pass > 0
        full_results = []
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = [pool.submit(fetch_full, ticker) for ticker in eligible["ticker"].astype(str)]
            for completed, future in enumerate(as_completed(futures), start=1):
                full_results.append(future.result())
                if completed % 10 == 0:
                    print(json.dumps({"full_tickers": completed, "eligible": len(eligible),
                                      "scoring_core_pass": core_pass}), flush=True)
        full_results.sort(key=lambda row: str(row.get("ticker", "")))
        scoring_core_incomplete = sorted(
            ticker for ticker in eligible["ticker"].astype(str)
            if not scoring_core_complete(args.output / "tickers" / ticker.replace("/", "_"))
        )
        if not scoring_core_incomplete:
            break
        print(json.dumps({"scoring_core_retry_pass": core_pass + 1,
                          "incomplete_tickers": scoring_core_incomplete}), flush=True)
    final_errors = sum(int(row.get("endpoint_errors", 0)) for row in full_results)
    if len(scoring_core_incomplete) > args.maximum_scoring_core_incomplete:
        raise RuntimeError(
            f"Scoring-core incomplete tickers {scoring_core_incomplete} exceed allowed "
            f"{args.maximum_scoring_core_incomplete}; resume with retries."
        )
    if args.maximum_final_endpoint_errors >= 0 and final_errors > args.maximum_final_endpoint_errors:
        raise RuntimeError(
            f"Final ticker endpoint errors {final_errors} exceed allowed {args.maximum_final_endpoint_errors}."
        )

    benchmarks = fetch_benchmarks(args.output, args.attempts, args.benchmark_fallback_dir)
    query_registry = pd.read_csv(args.output / "query_registry.csv")
    waterfall = pd.read_csv(args.output / "eligibility_waterfall.csv")
    manifest = {
        "snapshot_id": args.output.name,
        "source": "Yahoo Finance accessed exclusively through yfinance 1.4.0",
        "started_at_utc": started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "partition_method": "Nonoverlapping sector x market-cap ranges; recursively split when Yahoo reported total > 250",
        "initial_market_cap_bands": INITIAL_BANDS,
        "query_count": int(len(query_registry)),
        "max_leaf_reported_total": int(query_registry.loc[query_registry["split_at"].isna(), "reported_total"].max()),
        "screened_unique_tickers": int(len(screened)),
        "enriched_market_cap_2b_tickers": int(len(enriched)),
        "base_eligible_tickers": int(len(eligible)),
        "eligibility_waterfall": waterfall.to_dict(orient="records"),
        "ticker_results": full_results,
        "final_endpoint_errors": final_errors,
        "scoring_core_incomplete_tickers": scoring_core_incomplete,
        "benchmarks": benchmarks,
        "yfinance_version": yf.__version__,
        "classification": "Current yfinance-only universe and factor snapshot; not historical universe or point-in-time historical fundamentals",
        "limitations": [
            "Yahoo screen coverage is current and result semantics can change.",
            "Country/security-type/issuer deduplication use current Yahoo metadata without permanent identifiers.",
            "Current statements may be restated and do not reconstruct past retrieval vintages.",
            "Inactive/delisted securities and terminal returns are incomplete.",
        ],
    }
    write_json(args.output / "manifest.json", manifest)
    print(json.dumps({"status": "complete", "screened": len(screened), "enriched": len(enriched), "eligible": len(eligible), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
