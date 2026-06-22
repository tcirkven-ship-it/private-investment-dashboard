#!/usr/bin/env python3
"""Generate the final research charts from experiment result files."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "data/metadata/matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


COLORS = {"Strategy": "#0F766E", "SPY": "#2563EB", "QQQ": "#7C3AED"}


def load_ledger(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["date"]).set_index("date")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preholdout-dir", type=Path, required=True)
    parser.add_argument("--holdout-dir", type=Path, required=True)
    parser.add_argument("--benchmark-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

    strategy = pd.concat(
        [
            load_ledger(args.preholdout_dir / "primary_daily_ledger.csv"),
            load_ledger(args.holdout_dir / "primary_daily_ledger.csv"),
        ]
    ).sort_index()
    spy = load_ledger(args.benchmark_dir / "SPY_weekly_ledger.csv").reindex(strategy.index)
    qqq = load_ledger(args.benchmark_dir / "QQQ_weekly_ledger.csv").reindex(strategy.index)
    series = {"Strategy": strategy, "SPY": spy, "QQQ": qqq}

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(11, 6.2))
    for name, ledger in series.items():
        ax.plot(ledger.index, ledger["nav"], label=name, color=COLORS[name], linewidth=2 if name == "Strategy" else 1.7)
    ax.axvline(pd.Timestamp("2023-01-01"), color="#6B7280", linestyle="--", linewidth=1.2, label="Holdout start")
    ax.set_title("Contribution-matched portfolio values")
    ax.set_ylabel("Portfolio value (USD)")
    ax.legend(ncol=4, frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "contribution_matched_values.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 6.2))
    for name, ledger in series.items():
        wealth = (1 + ledger["daily_return"].fillna(0)).cumprod()
        ax.plot(ledger.index, wealth, label=name, color=COLORS[name], linewidth=2 if name == "Strategy" else 1.7)
    ax.axvline(pd.Timestamp("2023-01-01"), color="#6B7280", linestyle="--", linewidth=1.2)
    ax.set_yscale("log")
    ax.set_title("Time-weighted growth of one dollar (log scale)")
    ax.set_ylabel("Growth multiple")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "time_weighted_growth.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 6.2))
    for name, ledger in series.items():
        wealth = (1 + ledger["daily_return"].fillna(0)).cumprod()
        drawdown = wealth / wealth.cummax() - 1
        ax.plot(ledger.index, drawdown, label=name, color=COLORS[name], linewidth=1.8)
    ax.axvline(pd.Timestamp("2023-01-01"), color="#6B7280", linestyle="--", linewidth=1.2)
    ax.set_title("Drawdown paths")
    ax.set_ylabel("Drawdown")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "drawdowns.png", dpi=180)
    plt.close(fig)

    annual = pd.DataFrame({name: (1 + ledger["daily_return"]).groupby(ledger.index.year).prod() - 1 for name, ledger in series.items()})
    active = pd.DataFrame({"vs SPY": annual["Strategy"] - annual["SPY"], "vs QQQ": annual["Strategy"] - annual["QQQ"]})
    fig, ax = plt.subplots(figsize=(12, 6.2))
    x = np.arange(len(active.index))
    width = 0.38
    ax.bar(x - width / 2, active["vs SPY"], width, label="vs SPY", color="#2563EB")
    ax.bar(x + width / 2, active["vs QQQ"], width, label="vs QQQ", color="#7C3AED")
    ax.axhline(0, color="#111827", linewidth=0.8)
    ax.axvline(12.5, color="#6B7280", linestyle="--", linewidth=1.2)
    ax.set_xticks(x, active.index.astype(str), rotation=45)
    ax.set_title("Calendar-year active returns")
    ax.set_ylabel("Strategy return minus benchmark return")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "annual_active_returns.png", dpi=180)
    plt.close(fig)

    pre = pd.read_csv(args.preholdout_dir / "candidate_metrics.csv").set_index("candidate_id")
    holdout = pd.read_csv(args.holdout_dir / "candidate_metrics.csv").set_index("candidate_id")
    common = pre.index.intersection(holdout.index)
    fig, ax = plt.subplots(figsize=(8.5, 7.2))
    sizes = 35 + 18 * np.minimum(pre.loc[common, "annualized_gross_turnover"], 5)
    ax.scatter(pre.loc[common, "vs_QQQ_annualized_twr_advantage"], holdout.loc[common, "vs_QQQ_annualized_twr_advantage"], s=sizes, color="#0F766E", alpha=0.8)
    for candidate in common:
        ax.annotate(candidate, (pre.loc[candidate, "vs_QQQ_annualized_twr_advantage"], holdout.loc[candidate, "vs_QQQ_annualized_twr_advantage"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
    ax.axhline(0, color="#111827", linewidth=0.8)
    ax.axvline(0, color="#111827", linewidth=0.8)
    ax.set_xlabel("Pre-holdout annualized active return vs QQQ")
    ax.set_ylabel("Holdout annualized active return vs QQQ")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_title("Parameter/candidate stability versus QQQ\nBubble size increases with pre-holdout turnover")
    fig.tight_layout()
    fig.savefig(args.output_dir / "candidate_stability_vs_qqq.png", dpi=180)
    plt.close(fig)

    print(f"wrote 5 charts to {args.output_dir}")


if __name__ == "__main__":
    main()
