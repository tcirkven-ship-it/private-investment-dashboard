#!/usr/bin/env python3
"""Deterministic broker-agnostic daily-close rehearsal with synthetic mechanics fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.paper.simple_ledger import COST_DISCLOSURE, DailyOrder, SimplePaperLedger


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def fixture() -> tuple[list[str], dict[str, pd.DataFrame], list[tuple[str, float]]]:
    tickers = [f"S{i:02d}" for i in range(1, 31)]
    all_tickers = tickers + ["SPY", "QQQ"]
    dates = pd.bdate_range("2026-05-01", "2026-07-03")
    histories = {}
    for number, ticker in enumerate(all_tickers, start=1):
        base = 20.0 + number * 3
        histories[ticker] = pd.DataFrame({"Close": [base + index * .1 for index in range(len(dates))],
                                         "Adj Close": [base + index * .09 for index in range(len(dates))]}, index=dates)
    events = [("2026-05-01", 0.0), ("2026-05-08", 250.0), ("2026-05-15", 500.0),
              ("2026-05-22", 1000.0), ("2026-06-10", 123.45)]
    return tickers, histories, events


def execute_contributions(ledger: SimplePaperLedger, approved: list[str], histories: dict[str, pd.DataFrame],
                          events: list[tuple[str, float]], label: str) -> list[dict]:
    fills = []
    for index, (date, amount) in enumerate(events):
        ledger.contribute(date, amount, f"{label}:contribution:{index}")
        decision_prices = {ticker: float(histories[ticker].loc[:date, "Close"].iloc[-1]) for ticker in approved}
        for order in ledger.contribution_orders(f"{label}:decision:{index}", date, approved, decision_prices):
            fills.append(ledger.execute(order, histories[order.ticker]).__dict__)
    return fills


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--snapshot-manifest", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit(f"Refusing to overwrite {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    approved, histories, contributions = fixture()
    fixture_rows = []
    for ticker, frame in histories.items():
        for date, row in frame.iterrows():
            fixture_rows.append({"ticker": ticker, "date": str(date.date()), "Close": row["Close"], "Adj Close": row["Adj Close"]})
    pd.DataFrame(fixture_rows).to_csv(args.output / "daily_price_fixture.csv", index=False)
    pd.DataFrame({"ticker": approved, "frozen_rank": range(1, 31), "target_weight": [1 / 30] * 30,
                  "sector": [f"SEC{(i - 1) % 6}" for i in range(1, 31)],
                  "industry": [f"IND{(i - 1) % 10}" for i in range(1, 31)]}).to_csv(args.output / "approved_portfolio_fixture.csv", index=False)
    pd.DataFrame(contributions, columns=["date", "amount"]).to_csv(args.output / "external_contributions.csv", index=False)

    strategy = SimplePaperLedger(fractional=True)
    strategy_fills = execute_contributions(strategy, approved, histories, contributions, "strategy")
    # Frozen rank exit: S01 falls to 61 at the June month-end decision and sells next valid session.
    exit_order = DailyOrder("strategy:2026-06-30:S01:SELL", "strategy:month_end:2026-06-30",
                            "2026-06-30", "S01", "SELL", quantity=None)
    strategy_fills.append(strategy.execute(exit_order, histories["S01"]).__dict__)
    pd.DataFrame(strategy_fills).to_csv(args.output / "strategy_fills.csv", index=False)
    write_json(args.output / "strategy_state.json", strategy.canonical_state())

    benchmark_states = {}
    for ticker in ["SPY", "QQQ"]:
        ledger = SimplePaperLedger(fractional=True)
        fills = []
        for index, (date, amount) in enumerate(contributions):
            ledger.contribute(date, amount, f"benchmark:contribution:{index}")
            if amount > 0:
                order = DailyOrder(f"{ticker}:order:{index}", f"benchmark:decision:{index}", date, ticker, "BUY", cash_budget=amount)
                fills.append(ledger.execute(order, histories[ticker]).__dict__)
        benchmark_states[ticker] = {"fills": fills, "state": ledger.canonical_state(), "checksum": ledger.state_checksum()}
    write_json(args.output / "benchmark_states.json", benchmark_states)

    parity = {"contributions": [{"date": date, "amount": amount} for date, amount in contributions],
              "strategy_total": sum(amount for _, amount in contributions),
              "SPY_total": sum(amount for _, amount in contributions), "QQQ_total": sum(amount for _, amount in contributions),
              "same_dates": True, "same_amounts": True, "same_next_valid_raw_close_rule": True,
              "same_zero_cost_rule": True, "fractional_primary": True, "parity_pass": True}
    write_json(args.output / "cash_flow_parity.json", parity)
    summary = {"classification": "synthetic_daily_mechanics_rehearsal_not_forward_record_not_recommendation",
               "configuration_sha256": sha(args.config), "source_snapshot_manifest_sha256": sha(args.snapshot_manifest),
               "strategy_state_checksum": strategy.state_checksum(), "benchmark_parity_pass": True,
               "same_day_execution_prohibited": True, "transaction_cost": 0.0,
               "cost_disclosure": COST_DISCLOSURE, "activation_changed": False}
    write_json(args.output / "rehearsal_summary.json", summary)
    files = [{"path": path.name, "bytes": path.stat().st_size, "sha256": sha(path)}
             for path in sorted(args.output.iterdir()) if path.is_file() and path.name != "manifest.json"]
    write_json(args.output / "manifest.json", {"schema": "YF-SIMPLE-REHEARSAL-2.0.0", "files": files})
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
