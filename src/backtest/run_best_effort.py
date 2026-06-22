#!/usr/bin/env python3
"""Run the frozen best-effort price-strategy experiment generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest.engine import CostModel, generate_contributions, json_dump, load_yfinance_history, performance_metrics, simulate_benchmark
from src.backtest.strategy import StrategySpec, load_price_panels, simulate_strategy


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def candidate_specs() -> list[StrategySpec]:
    common = {"sector_cap": 0.25, "name_drift_cap": 0.075, "minimum_order_usd": 25.0}
    return [
        StrategySpec("C03-M", "momentum", 30, 252, 21, **common),
        StrategySpec("EW-ALL", "equal_weight", 100, 252, 21, **common),
        StrategySpec("C03-M-6-1", "momentum", 30, 126, 21, **common),
        StrategySpec("C03-M-9-1", "momentum", 30, 189, 21, **common),
        StrategySpec("C03-M-N10", "momentum", 10, 252, 21, **common),
        StrategySpec("C03-M-N20", "momentum", 20, 252, 21, **common),
        StrategySpec("C03-M-N40", "momentum", 40, 252, 21, **common),
        StrategySpec("C03-M-N50", "momentum", 50, 252, 21, **common),
        StrategySpec("L-LOWVOL", "low_volatility", 30, 252, 21, **common),
        StrategySpec("ML-EQUAL-RANK", "momentum_low_volatility", 30, 252, 21, **common),
    ]


def period_ledger(ledger: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.DataFrame, float]:
    subset = ledger.loc[(ledger.index >= start) & (ledger.index <= end)].copy()
    before = ledger.loc[ledger.index < subset.index[0], "nav"]
    opening_nav = float(before.iloc[-1]) if not before.empty else 0.0
    if opening_nav > 0:
        subset.iloc[0, subset.columns.get_loc("external_flow")] += opening_nav
    return subset, opening_nav


def rolling_win_rate(strategy: pd.Series, benchmark: pd.Series, months: int) -> float | None:
    aligned = pd.concat([strategy.rename("strategy"), benchmark.rename("benchmark")], axis=1).dropna()
    monthly = (1 + aligned).resample("ME").prod() - 1
    strategy_roll = (1 + monthly["strategy"]).rolling(months).apply(np.prod, raw=True) - 1
    benchmark_roll = (1 + monthly["benchmark"]).rolling(months).apply(np.prod, raw=True) - 1
    valid = pd.concat([strategy_roll, benchmark_roll], axis=1).dropna()
    return None if valid.empty else float((valid.iloc[:, 0] > valid.iloc[:, 1]).mean())


def annual_return(return_series: pd.Series) -> pd.Series:
    return (1 + return_series).groupby(return_series.index.year).prod() - 1


def moving_block_ci(active_monthly: pd.Series, seed: int, samples: int = 10_000, block: int = 6) -> dict[str, float | int | None]:
    values = active_monthly.dropna().to_numpy(dtype=float)
    if len(values) < 12:
        return {"samples": samples, "block_months": block, "lower_95": None, "median": None, "upper_95": None, "probability_positive": None}
    rng = np.random.default_rng(seed)
    starts = np.arange(len(values))
    results = np.empty(samples)
    blocks_needed = int(np.ceil(len(values) / block))
    for sample in range(samples):
        selected = []
        for _ in range(blocks_needed):
            start = int(rng.choice(starts))
            selected.extend(values[(start + np.arange(block)) % len(values)])
        draw = np.asarray(selected[: len(values)])
        results[sample] = (1 + draw.mean()) ** 12 - 1
    return {
        "samples": samples,
        "block_months": block,
        "lower_95": float(np.quantile(results, 0.025)),
        "median": float(np.quantile(results, 0.5)),
        "upper_95": float(np.quantile(results, 0.975)),
        "probability_positive": float((results > 0).mean()),
    }


def compare_metrics(strategy_metrics: dict[str, object], benchmark_metrics: dict[str, object]) -> dict[str, float]:
    return {
        "annualized_twr_advantage": float(strategy_metrics["annualized_twr"]) - float(benchmark_metrics["annualized_twr"]),
        "xirr_advantage": float(strategy_metrics["xirr"]) - float(benchmark_metrics["xirr"]),
        "max_drawdown_difference": float(strategy_metrics["max_drawdown"]) - float(benchmark_metrics["max_drawdown"]),
        "volatility_ratio": float(strategy_metrics["annualized_volatility"]) / float(benchmark_metrics["annualized_volatility"]),
    }


def diagnostics(ledger: pd.DataFrame, trades: pd.DataFrame, selections: pd.DataFrame) -> dict[str, object]:
    return {
        "trade_count": int(len(trades)),
        "average_holding_count": float(ledger["holding_count"].mean()),
        "minimum_selection_eligible_count": int(selections["eligible_count"].min()) if not selections.empty else 0,
        "minimum_target_count": int(selections["target_count"].min()) if not selections.empty else 0,
        "maximum_position_weight": float(ledger["max_position_weight"].max()),
        "maximum_sector_weight": float(ledger["max_sector_weight"].max()),
        "name_drift_cap_violation_sessions": int((ledger["max_position_weight"] > 0.075 + 1e-9).sum()),
        "sector_drift_cap_violation_sessions": int((ledger["max_sector_weight"] > 0.30 + 1e-9).sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["preholdout", "holdout"], required=True)
    parser.add_argument("--price-snapshot", type=Path, required=True)
    parser.add_argument("--benchmark-snapshot", type=Path, required=True)
    parser.add_argument("--universe-csv", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    config = json.loads(args.config.read_text(encoding="utf-8"))
    universe = pd.read_csv(args.universe_csv)
    universe = universe.sort_values("Weight (%)", ascending=False).drop_duplicates("Issuer Key", keep="first")
    tickers = universe["YFinance Ticker"].tolist()
    sectors = dict(zip(universe["YFinance Ticker"], universe["Sector"]))

    benchmark_history = {
        ticker: load_yfinance_history(args.benchmark_snapshot / ticker / "history_daily.csv")
        for ticker in ("SPY", "QQQ")
    }
    all_dates = benchmark_history["SPY"].index.intersection(benchmark_history["QQQ"].index)
    analysis_start = pd.Timestamp(config["calendar"]["analysis_start"])
    run_end = pd.Timestamp(config["calendar"]["walk_forward_end"] if args.stage == "preholdout" else config["calendar"]["final_holdout_end"])
    dates = all_dates[(all_dates >= analysis_start) & (all_dates <= run_end)]
    signal_history_start = analysis_start - pd.Timedelta(days=550)
    data_dates = all_dates[(all_dates >= signal_history_start) & (all_dates <= run_end)]
    panels = load_price_panels(args.price_snapshot, tickers, data_dates)
    specs = candidate_specs()

    if args.stage == "preholdout":
        evaluation_start, evaluation_end = analysis_start, pd.Timestamp(config["calendar"]["walk_forward_end"])
    else:
        evaluation_start, evaluation_end = pd.Timestamp(config["calendar"]["final_holdout_start"]), run_end

    costs = {name: CostModel(**parameters) for name, parameters in config["cost_models"].items()}
    primary_frequency = "weekly"
    expected_flows = generate_contributions(dates, dates[0], dates[-1], primary_frequency)

    benchmark_ledgers: dict[str, pd.DataFrame] = {}
    benchmark_period_ledgers: dict[str, pd.DataFrame] = {}
    benchmark_metrics: dict[str, dict[str, object]] = {}
    for ticker in ("SPY", "QQQ"):
        ledger = simulate_benchmark(benchmark_history[ticker]["Adj Close"].reindex(dates), expected_flows.copy(), costs["expected"])
        period, opening = period_ledger(ledger, evaluation_start, evaluation_end)
        benchmark_ledgers[ticker] = ledger
        benchmark_period_ledgers[ticker] = period
        benchmark_metrics[ticker] = performance_metrics(period)
        benchmark_metrics[ticker]["opening_nav"] = opening

    candidate_results: dict[str, dict[str, object]] = {}
    primary_detail: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame] | None = None
    for spec in specs:
        ledger, trades, selections = simulate_strategy(panels, sectors, expected_flows.copy(), costs["expected"], spec)
        period, opening = period_ledger(ledger, evaluation_start, evaluation_end)
        metrics = performance_metrics(period, benchmark_period_ledgers["SPY"]["daily_return"])
        metrics["opening_nav"] = opening
        comparisons = {ticker: compare_metrics(metrics, benchmark_metrics[ticker]) for ticker in ("SPY", "QQQ")}
        rolling = {
            ticker: {
                "rolling_3y_win_rate": rolling_win_rate(period["daily_return"], benchmark_period_ledgers[ticker]["daily_return"], 36),
                "rolling_5y_win_rate": rolling_win_rate(period["daily_return"], benchmark_period_ledgers[ticker]["daily_return"], 60),
            }
            for ticker in ("SPY", "QQQ")
        }
        candidate_results[spec.candidate_id] = {
            "spec": spec.__dict__,
            "metrics": metrics,
            "comparisons": comparisons,
            "rolling": rolling,
            "diagnostics": diagnostics(period, trades[(trades["date"] >= evaluation_start) & (trades["date"] <= evaluation_end)] if not trades.empty else trades, selections[(selections["fill_date"] >= evaluation_start) & (selections["fill_date"] <= evaluation_end)] if not selections.empty else selections),
        }
        monthly = (1 + period["daily_return"]).resample("ME").prod() - 1
        monthly.rename(spec.candidate_id).to_csv(args.output_dir / f"{spec.candidate_id}_monthly_returns.csv", date_format="%Y-%m-%d")
        if spec.candidate_id == "C03-M":
            primary_detail = (ledger, trades, selections)

    assert primary_detail is not None
    primary_ledger, primary_trades, primary_selections = primary_detail
    primary_period, _ = period_ledger(primary_ledger, evaluation_start, evaluation_end)

    stressed_flows = generate_contributions(dates, dates[0], dates[-1], primary_frequency)
    stressed_ledger, stressed_trades, stressed_selections = simulate_strategy(panels, sectors, stressed_flows, costs["stressed"], specs[0])
    stressed_period, stressed_opening = period_ledger(stressed_ledger, evaluation_start, evaluation_end)
    stressed_metrics = performance_metrics(stressed_period)
    stressed_metrics["opening_nav"] = stressed_opening
    stressed_benchmarks: dict[str, dict[str, object]] = {}
    stressed_comparisons: dict[str, dict[str, float]] = {}
    for ticker in ("SPY", "QQQ"):
        ledger = simulate_benchmark(benchmark_history[ticker]["Adj Close"].reindex(dates), stressed_flows.copy(), costs["stressed"])
        period, opening = period_ledger(ledger, evaluation_start, evaluation_end)
        metric = performance_metrics(period)
        metric["opening_nav"] = opening
        stressed_benchmarks[ticker] = metric
        stressed_comparisons[ticker] = compare_metrics(stressed_metrics, metric)

    frequency_results: dict[str, object] = {}
    for frequency in ("weekly", "biweekly", "monthly"):
        flows = generate_contributions(dates, dates[0], dates[-1], frequency)
        ledger, trades, selections = simulate_strategy(panels, sectors, flows, costs["expected"], specs[0])
        period, opening = period_ledger(ledger, evaluation_start, evaluation_end)
        metrics = performance_metrics(period)
        metrics["opening_nav"] = opening
        frequency_results[frequency] = {"metrics": metrics, "flow_events": int((flows > 0).sum()), "total_external_flow": float(flows.sum())}

    primary_metrics = candidate_results["C03-M"]["metrics"]
    primary_comparisons = candidate_results["C03-M"]["comparisons"]
    gates = {
        "twr_advantage_at_least_1pct_vs_spy": primary_comparisons["SPY"]["annualized_twr_advantage"] >= 0.01,
        "twr_advantage_at_least_1pct_vs_qqq": primary_comparisons["QQQ"]["annualized_twr_advantage"] >= 0.01,
        "xirr_advantage_at_least_1pct_vs_spy": primary_comparisons["SPY"]["xirr_advantage"] >= 0.01,
        "xirr_advantage_at_least_1pct_vs_qqq": primary_comparisons["QQQ"]["xirr_advantage"] >= 0.01,
        "positive_stressed_active_vs_spy": stressed_comparisons["SPY"]["annualized_twr_advantage"] > 0,
        "positive_stressed_active_vs_qqq": stressed_comparisons["QQQ"]["annualized_twr_advantage"] > 0,
        "volatility_not_above_1_2x_spy": primary_comparisons["SPY"]["volatility_ratio"] <= 1.2,
        "drawdown_not_over_5pct_worse_than_spy": primary_comparisons["SPY"]["max_drawdown_difference"] >= -0.05,
        "annualized_turnover_at_or_below_100pct": float(primary_metrics["annualized_gross_turnover"]) <= 1.0,
        "definitive_data_integrity": False,
    }

    annual = pd.DataFrame({"C03-M": annual_return(primary_period["daily_return"]), "SPY": annual_return(benchmark_period_ledgers["SPY"]["daily_return"]), "QQQ": annual_return(benchmark_period_ledgers["QQQ"]["daily_return"])})
    annual["active_vs_SPY"] = annual["C03-M"] - annual["SPY"]
    annual["active_vs_QQQ"] = annual["C03-M"] - annual["QQQ"]
    annual.index.name = "year"
    annual.to_csv(args.output_dir / "primary_annual_returns.csv")

    monthly_primary = (1 + primary_period["daily_return"]).resample("ME").prod() - 1
    bootstrap = {}
    for index, ticker in enumerate(("SPY", "QQQ")):
        monthly_benchmark = (1 + benchmark_period_ledgers[ticker]["daily_return"]).resample("ME").prod() - 1
        bootstrap[ticker] = moving_block_ci(monthly_primary - monthly_benchmark, int(config["random_seed"]) + index)

    primary_ledger.loc[(primary_ledger.index >= evaluation_start) & (primary_ledger.index <= evaluation_end)].to_csv(args.output_dir / "primary_daily_ledger.csv", date_format="%Y-%m-%d")
    if not primary_trades.empty:
        primary_trades.loc[(primary_trades["date"] >= evaluation_start) & (primary_trades["date"] <= evaluation_end)].to_csv(args.output_dir / "primary_trades.csv", index=False, date_format="%Y-%m-%d")
    if not primary_selections.empty:
        primary_selections.loc[(primary_selections["fill_date"] >= evaluation_start) & (primary_selections["fill_date"] <= evaluation_end)].to_csv(args.output_dir / "primary_selections.csv", index=False, date_format="%Y-%m-%d")

    result = {
        "experiment_id": "EXP-0009" if args.stage == "preholdout" else "EXP-0010",
        "stage": args.stage,
        "evaluation_start": str(evaluation_start.date()),
        "evaluation_end": str(evaluation_end.date()),
        "config_path": str(args.config),
        "config_sha256": sha256(args.config),
        "universe": {"registered_issuers": len(tickers), "current_membership_survivorship_bias": True},
        "benchmark_metrics": benchmark_metrics,
        "candidate_results": candidate_results,
        "primary_stressed": {"metrics": stressed_metrics, "benchmark_metrics": stressed_benchmarks, "comparisons": stressed_comparisons, "trade_count": len(stressed_trades), "selection_count": len(stressed_selections)},
        "contribution_frequency": frequency_results,
        "primary_gates": gates,
        "bootstrap_active_return": bootstrap,
        "economic_gate_status": "PASS" if all(value for key, value in gates.items() if key != "definitive_data_integrity") else "FAIL",
        "protocol_status": "FAIL" if not gates["definitive_data_integrity"] else "PENDING",
        "interpretation_ceiling": "Exploratory current-universe evidence only; never a survivor-bias-free historical result.",
    }
    json_dump(result, args.output_dir / "summary.json")
    rows = []
    for candidate_id, payload in candidate_results.items():
        row = {"candidate_id": candidate_id, **payload["metrics"], **{f"vs_{ticker}_{key}": value for ticker, values in payload["comparisons"].items() for key, value in values.items()}, **payload["diagnostics"]}
        rows.append(row)
    pd.DataFrame(rows).to_csv(args.output_dir / "candidate_metrics.csv", index=False)
    print(json.dumps({"experiment_id": result["experiment_id"], "stage": args.stage, "economic_gate_status": result["economic_gate_status"], "protocol_status": result["protocol_status"], "output": str(args.output_dir / "summary.json")}))


if __name__ == "__main__":
    main()
