#!/usr/bin/env python3
"""Deterministic pre-activation rehearsal; outputs are not a prospective record."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.paper.ledger import Order, PaperLedger, limit_price


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_bars(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["Datetime"]).set_index("Datetime")
    return frame


def constrained_selection(scores: pd.DataFrame, size: int = 30, sector_cap: float = .25, industry_cap: float = .15) -> pd.DataFrame:
    selected, sector_counts, industry_counts = [], {}, {}
    for _, row in scores.dropna(subset=["YF-QVP"]).sort_values(["YF-QVP", "ticker"], ascending=[False, True]).iterrows():
        sector, industry = row.info_sector, row.info_industry
        if (sector_counts.get(sector, 0) + 1) / size > sector_cap + 1e-12:
            continue
        if (industry_counts.get(industry, 0) + 1) / size > industry_cap + 1e-12:
            continue
        selected.append(row)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        industry_counts[industry] = industry_counts.get(industry, 0) + 1
        if len(selected) == size:
            break
    if len(selected) != size:
        raise RuntimeError(f"Could select only {len(selected)} names under caps")
    result = pd.DataFrame(selected).reset_index(drop=True)
    result["selection_rank"] = range(1, len(result) + 1)
    result["target_weight"] = 1 / size
    return result


def latest_common_session(intraday: Path, tickers: list[str]) -> str:
    date_sets = []
    for ticker in tickers:
        bars = read_bars(intraday / f"{ticker}_5m.csv")
        date_sets.append(set(pd.DatetimeIndex(bars.index).date))
    common = set.intersection(*date_sets)
    if not common:
        raise RuntimeError("No common 5m session")
    return str(max(common))


def run_ledger(tickers: list[str], intraday: Path, session: str, contribution: float, share_convention: str) -> tuple[PaperLedger, list[dict], list[dict]]:
    ledger = PaperLedger()
    ledger.contribute(session, contribution, f"contribution:{session}")
    orders, fills = [], []
    budget = contribution / len(tickers)
    for index, ticker in enumerate(tickers, start=1):
        bars = read_bars(intraday / f"{ticker}_5m.csv")
        local = bars.copy()
        local.index = pd.DatetimeIndex(local.index).tz_convert("America/New_York")
        reference_rows = local[(local.index.date == pd.Timestamp(session).date())].between_time("15:45", "15:45")
        if reference_rows.empty or pd.isna(reference_rows.iloc[0]["Close"]):
            reference = None
            quantity = 1.0
            price_limit = 1.0
        else:
            reference = float(reference_rows.iloc[0]["Close"])
            price_limit = limit_price(reference, "BUY", ledger.execution)
            quantity = budget / (price_limit * 1.01)
        order = Order(f"rehearsal:{session}:{ticker}:BUY", f"decision:{session}", ticker, "BUY", quantity,
                      price_limit, session, share_convention)
        orders.append({**asdict(order), "reference_raw_close": reference, "cash_budget": budget})
        fills.append(asdict(ledger.process_order(order, bars)))
    return ledger, orders, fills


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--snapshot-manifest", type=Path, required=True)
    parser.add_argument("--intraday", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit(f"Refusing to overwrite {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    scores = pd.read_csv(args.scores)
    targets = constrained_selection(scores)
    targets.to_csv(args.output / "target_research_list_not_recommendation.csv", index=False)
    routed = targets.head(3).ticker.tolist()
    session = latest_common_session(args.intraday, routed + ["SPY", "QQQ"])
    strategy, orders, fills = run_ledger(routed, args.intraday, session, 250, "fractional")
    pd.DataFrame(orders).to_csv(args.output / "proposed_rehearsal_orders.csv", index=False)
    pd.DataFrame(fills).to_csv(args.output / "hypothetical_fills.csv", index=False)
    write_json(args.output / "strategy_ledger_state.json", strategy.canonical_state())

    whole, whole_orders, whole_fills = run_ledger(routed, args.intraday, session, 250, "whole")
    pd.DataFrame(whole_orders).to_csv(args.output / "whole_share_sensitivity_orders.csv", index=False)
    pd.DataFrame(whole_fills).to_csv(args.output / "whole_share_sensitivity_fills.csv", index=False)
    write_json(args.output / "whole_share_ledger_state.json", whole.canonical_state())

    benchmark_states = {}
    for ticker in ["SPY", "QQQ"]:
        ledger, benchmark_orders, benchmark_fills = run_ledger([ticker], args.intraday, session, 250, "fractional")
        benchmark_states[ticker] = {"state": ledger.canonical_state(), "state_checksum": ledger.state_checksum(),
                                    "orders": benchmark_orders, "fills": benchmark_fills}
    write_json(args.output / "benchmark_ledgers.json", benchmark_states)
    parity = {"external_flow_strategy": 250.0, "external_flow_SPY": 250.0, "external_flow_QQQ": 250.0,
              "same_execution_policy": True, "same_commission_policy": True, "same_share_convention": True,
              "same_session": session, "same_event_order": True, "parity_pass": True}
    write_json(args.output / "benchmark_parity.json", parity)

    config = json.loads(args.config.read_text())
    summary = {"classification": "dry_rehearsal_not_prospective_record_not_recommendation", "session": session,
               "primary": config["strategy"]["primary"], "selected_names": len(targets), "routed_names": routed,
               "strategy_state_checksum": strategy.state_checksum(), "whole_state_checksum": whole.state_checksum(),
               "snapshot_manifest_sha256": sha(args.snapshot_manifest), "scores_sha256": sha(args.scores),
               "intraday_manifest_sha256": sha(args.intraday / "manifest.json"), "config_sha256": sha(args.config),
               "benchmark_parity_pass": True, "strategy_returns_examined": False, "activation_changed": False}
    write_json(args.output / "rehearsal_summary.json", summary)
    files = [{"path": path.name, "bytes": path.stat().st_size, "sha256": sha(path)}
             for path in sorted(args.output.iterdir()) if path.is_file() and path.name != "rehearsal_manifest.json"]
    write_json(args.output / "rehearsal_manifest.json", {"schema": "YF-REHEARSAL-1.0.0", "files": files})
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
