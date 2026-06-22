#!/usr/bin/env python3
"""Run accounting invariants and create contribution-matched SPY/QQQ ledgers."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest.engine import CostModel, flow_checksum, generate_contributions, json_dump, load_yfinance_history, performance_metrics, simulate_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    test_run = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_accounting.py", "-v"],
        text=True,
        capture_output=True,
        check=False,
    )
    (args.output_dir / "unittest.log").write_text(test_run.stdout + test_run.stderr, encoding="utf-8")

    config = json.loads(args.config.read_text(encoding="utf-8"))
    cost = CostModel(**config["cost_models"]["expected"])
    histories = {
        ticker: load_yfinance_history(args.snapshot / ticker / "history_daily.csv")
        for ticker in ("SPY", "QQQ")
    }
    dates = histories["SPY"].index.intersection(histories["QQQ"].index)
    dates = dates[(dates >= pd.Timestamp(config["calendar"]["analysis_start"])) & (dates <= pd.Timestamp(config["calendar"]["final_holdout_end"]))]
    flows = generate_contributions(dates, dates[0], dates[-1], "weekly")
    checksum = flow_checksum(flows)

    ledgers: dict[str, pd.DataFrame] = {}
    metrics: dict[str, object] = {}
    for ticker in ("SPY", "QQQ"):
        price = histories[ticker]["Adj Close"].reindex(dates)
        ledger = simulate_benchmark(price, flows.copy(), cost)
        ledgers[ticker] = ledger
        ledger.to_csv(args.output_dir / f"{ticker}_weekly_ledger.csv", date_format="%Y-%m-%d")
        metrics[ticker] = performance_metrics(ledger)

    checks = {
        "unit_tests_pass": test_run.returncode == 0,
        "spy_qqq_flow_checksum_equal": flow_checksum(ledgers["SPY"]["external_flow"]) == flow_checksum(ledgers["QQQ"]["external_flow"]) == checksum,
        "spy_qqq_total_contributed_equal": float(ledgers["SPY"]["external_flow"].sum()) == float(ledgers["QQQ"]["external_flow"].sum()),
        "no_negative_spy_cash": bool((ledgers["SPY"]["cash"] >= -1e-8).all()),
        "no_negative_qqq_cash": bool((ledgers["QQQ"]["cash"] >= -1e-8).all()),
        "positive_ending_values": bool(ledgers["SPY"]["nav"].iloc[-1] > 0 and ledgers["QQQ"]["nav"].iloc[-1] > 0),
    }
    result = {
        "experiment_id": "EXP-0006",
        "overall_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "unit_test_log": str(args.output_dir / "unittest.log"),
        "flow_checksum": checksum,
        "contribution_events": int((flows > 0).sum()),
        "total_contributed": float(flows.sum()),
        "cost_model": config["cost_models"]["expected"],
        "benchmark_metrics": metrics,
        "accounting_conventions": {
            "price": "yfinance adjusted close; dividends and splits embedded exactly once",
            "external_flow_timing": "calendar Friday mapped to next trading session and posted at the close",
            "return": "(ending NAV - close-timed external flow) / prior ending NAV - 1",
            "fractional_units": True,
        },
    }
    json_dump(result, args.output_dir / "accounting_validation.json")
    print(json.dumps({"overall_status": result["overall_status"], "checks": checks, "output": str(args.output_dir / "accounting_validation.json")}))
    if result["overall_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
