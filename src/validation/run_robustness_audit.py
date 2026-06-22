#!/usr/bin/env python3
"""Aggregate pre-holdout and holdout results into falsification diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest.engine import json_dump, load_yfinance_history, performance_metrics


def annualized(return_series: pd.Series) -> float:
    values = return_series.dropna()
    return float((1 + values).prod() ** (252 / len(values)) - 1)


def compare(strategy: dict[str, object], benchmark: dict[str, object]) -> dict[str, float]:
    return {
        "annualized_twr_advantage": float(strategy["annualized_twr"]) - float(benchmark["annualized_twr"]),
        "xirr_advantage": float(strategy["xirr"]) - float(benchmark["xirr"]),
        "max_drawdown_difference": float(strategy["max_drawdown"]) - float(benchmark["max_drawdown"]),
        "volatility_ratio": float(strategy["annualized_volatility"]) / float(benchmark["annualized_volatility"]),
    }


def block_bootstrap(active_monthly: pd.Series, seed: int, samples: int = 10_000, block: int = 6) -> dict[str, float | int]:
    values = active_monthly.dropna().to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    results = np.empty(samples)
    starts = np.arange(len(values))
    blocks = int(np.ceil(len(values) / block))
    for sample in range(samples):
        draw = []
        for _ in range(blocks):
            start = int(rng.choice(starts))
            draw.extend(values[(start + np.arange(block)) % len(values)])
        results[sample] = (1 + np.mean(draw[: len(values)])) ** 12 - 1
    return {
        "samples": samples,
        "block_months": block,
        "lower_95": float(np.quantile(results, 0.025)),
        "median": float(np.quantile(results, 0.5)),
        "upper_95": float(np.quantile(results, 0.975)),
        "probability_positive": float((results > 0).mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preholdout-dir", type=Path, required=True)
    parser.add_argument("--holdout-dir", type=Path, required=True)
    parser.add_argument("--benchmark-dir", type=Path, required=True)
    parser.add_argument("--price-snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    pre = pd.read_csv(args.preholdout_dir / "primary_daily_ledger.csv", parse_dates=["date"]).set_index("date")
    holdout = pd.read_csv(args.holdout_dir / "primary_daily_ledger.csv", parse_dates=["date"]).set_index("date")
    full = pd.concat([pre, holdout]).sort_index()
    if full.index.has_duplicates:
        raise ValueError("Duplicate dates in stitched primary ledger")

    benchmarks = {
        ticker: pd.read_csv(args.benchmark_dir / f"{ticker}_weekly_ledger.csv", parse_dates=["date"]).set_index("date").reindex(full.index)
        for ticker in ("SPY", "QQQ")
    }
    strategy_metrics = performance_metrics(full, benchmarks["SPY"]["daily_return"])
    benchmark_metrics = {ticker: performance_metrics(ledger) for ticker, ledger in benchmarks.items()}
    comparisons = {ticker: compare(strategy_metrics, benchmark_metrics[ticker]) for ticker in benchmarks}

    annual = pd.DataFrame({"strategy": (1 + full["daily_return"]).groupby(full.index.year).prod() - 1})
    for ticker, ledger in benchmarks.items():
        annual[ticker] = (1 + ledger["daily_return"]).groupby(ledger.index.year).prod() - 1
        annual[f"active_vs_{ticker}"] = annual["strategy"] - annual[ticker]
    best_year = int(annual["strategy"].idxmax())
    without_best_year = full.index.year != best_year
    best_year_removal = {
        "removed_year": best_year,
        "strategy_annualized_twr": annualized(full.loc[without_best_year, "daily_return"]),
        "active_vs_SPY": annualized(full.loc[without_best_year, "daily_return"]) - annualized(benchmarks["SPY"].loc[without_best_year, "daily_return"]),
        "active_vs_QQQ": annualized(full.loc[without_best_year, "daily_return"]) - annualized(benchmarks["QQQ"].loc[without_best_year, "daily_return"]),
    }

    starting_date_sensitivity = []
    for year in range(2010, 2016):
        mask = full.index >= pd.Timestamp(f"{year}-01-01")
        starting_date_sensitivity.append(
            {
                "start_year": year,
                "strategy_annualized_twr": annualized(full.loc[mask, "daily_return"]),
                "active_vs_SPY": annualized(full.loc[mask, "daily_return"]) - annualized(benchmarks["SPY"].loc[mask, "daily_return"]),
                "active_vs_QQQ": annualized(full.loc[mask, "daily_return"]) - annualized(benchmarks["QQQ"].loc[mask, "daily_return"]),
            }
        )

    spy_returns = benchmarks["SPY"]["daily_return"]
    spy_vol = spy_returns.rolling(63).std() * np.sqrt(252)
    median_vol = float(spy_vol.median())
    active_daily = {ticker: full["daily_return"] - ledger["daily_return"] for ticker, ledger in benchmarks.items()}
    regime = {
        "high_volatility": {ticker: float(series[spy_vol >= median_vol].mean() * 252) for ticker, series in active_daily.items()},
        "low_volatility": {ticker: float(series[spy_vol < median_vol].mean() * 252) for ticker, series in active_daily.items()},
        "spy_bull_years": {ticker: float(annual.loc[annual["SPY"] >= 0, f"active_vs_{ticker}"].mean()) for ticker in benchmarks},
        "spy_bear_years": {ticker: float(annual.loc[annual["SPY"] < 0, f"active_vs_{ticker}"].mean()) for ticker in benchmarks},
    }

    pre_candidates = pd.read_csv(args.preholdout_dir / "candidate_metrics.csv").set_index("candidate_id")
    holdout_candidates = pd.read_csv(args.holdout_dir / "candidate_metrics.csv").set_index("candidate_id")
    stability_rows = []
    for candidate in pre_candidates.index.intersection(holdout_candidates.index):
        stability_rows.append(
            {
                "candidate_id": candidate,
                "pre_positive_vs_both": bool(pre_candidates.loc[candidate, "vs_SPY_annualized_twr_advantage"] > 0 and pre_candidates.loc[candidate, "vs_QQQ_annualized_twr_advantage"] > 0),
                "holdout_positive_vs_both": bool(holdout_candidates.loc[candidate, "vs_SPY_annualized_twr_advantage"] > 0 and holdout_candidates.loc[candidate, "vs_QQQ_annualized_twr_advantage"] > 0),
                "pre_turnover": float(pre_candidates.loc[candidate, "annualized_gross_turnover"]),
                "holdout_turnover": float(holdout_candidates.loc[candidate, "annualized_gross_turnover"]),
            }
        )
    stable_positive = sum(row["pre_positive_vs_both"] and row["holdout_positive_vs_both"] for row in stability_rows)

    trades = pd.concat(
        [
            pd.read_csv(args.preholdout_dir / "primary_trades.csv", parse_dates=["date"]),
            pd.read_csv(args.holdout_dir / "primary_trades.csv", parse_dates=["date"]),
        ],
        ignore_index=True,
    )
    final_units: dict[str, float] = {}
    pnl_rows = []
    final_date = full.index[-1]
    for ticker, group in trades.groupby("ticker"):
        buys = group[group["side"] == "BUY"]
        sells = group[group["side"] == "SELL"]
        units = float(buys["units"].sum() - sells["units"].sum())
        final_units[ticker] = units
        final_price = float(load_yfinance_history(args.price_snapshot / ticker / "history_daily.csv")["Adj Close"].asof(final_date))
        buy_cost = float((buys["notional"] + buys["commission"] + buys["impact_cost"]).sum())
        sell_proceeds = float((sells["notional"] - sells["commission"] - sells["impact_cost"]).sum())
        pnl = sell_proceeds + units * final_price - buy_cost
        pnl_rows.append({"ticker": ticker, "net_pnl": pnl, "ending_units": units, "ending_value": units * final_price})
    pnl_frame = pd.DataFrame(pnl_rows).sort_values("net_pnl", ascending=False)
    total_profit = float(full["nav"].iloc[-1] - full["external_flow"].sum())
    top = pnl_frame.iloc[0]
    top_stock = {
        "ticker": top["ticker"],
        "net_pnl": float(top["net_pnl"]),
        "share_of_total_portfolio_profit": float(top["net_pnl"] / total_profit) if total_profit else None,
        "profit_after_removing_top_stock_pnl": float(total_profit - top["net_pnl"]),
    }

    bootstrap = {}
    monthly_strategy = (1 + full["daily_return"]).resample("ME").prod() - 1
    for index, ticker in enumerate(("SPY", "QQQ")):
        monthly_benchmark = (1 + benchmarks[ticker]["daily_return"]).resample("ME").prod() - 1
        bootstrap[ticker] = block_bootstrap(monthly_strategy - monthly_benchmark, 20260621 + index)

    result = {
        "experiment_id": "EXP-0010",
        "stitched_period": {"start": str(full.index[0].date()), "end": str(full.index[-1].date())},
        "strategy_metrics": strategy_metrics,
        "benchmark_metrics": benchmark_metrics,
        "comparisons": comparisons,
        "calendar_consistency": {
            "years": int(len(annual)),
            "positive_active_years_vs_SPY": int((annual["active_vs_SPY"] > 0).sum()),
            "positive_active_years_vs_QQQ": int((annual["active_vs_QQQ"] > 0).sum()),
            "annual_returns": annual.reset_index().rename(columns={"index": "year"}).to_dict(orient="records"),
        },
        "best_year_removal": best_year_removal,
        "starting_date_sensitivity": starting_date_sensitivity,
        "regime_diagnostics": regime,
        "parameter_stability": {
            "registered_candidates": len(stability_rows),
            "positive_vs_both_pre_and_holdout": stable_positive,
            "stable_positive_fraction": stable_positive / len(stability_rows),
            "rows": stability_rows,
        },
        "top_stock_influence_approximation": top_stock,
        "bootstrap_active_return": bootstrap,
        "limitations": [
            "Top-stock P&L uses adjusted-price units and trade cash flows; it is an attribution approximation, not a counterfactual rerun.",
            "Regime labels are retrospective diagnostics and cannot become trading switches.",
            "All stock results inherit current-membership survivorship bias and missing delisting outcomes."
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    json_dump(result, args.output)
    pnl_frame.to_csv(args.output.with_name("stock_pnl_attribution.csv"), index=False)
    print(json.dumps({"status": "PASS", "output": str(args.output), "stable_positive_fraction": result["parameter_stability"]["stable_positive_fraction"], "top_stock": top_stock["ticker"]}))


if __name__ == "__main__":
    main()
