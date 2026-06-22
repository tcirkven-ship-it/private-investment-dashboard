#!/usr/bin/env python3
"""Risk/factor/sector diagnostics for the preserved C03-M return path."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "outputs/experiment_runs"


def ledger(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()


def read_factor_zip(path: Path, member: str, columns: list[str]) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        text = archive.read(member).decode("utf-8", errors="replace")
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip().startswith(","))
    data = pd.read_csv(io.StringIO("\n".join(lines[start:])))
    first = data.columns[0]
    dates = pd.to_datetime(data[first].astype(str).str.strip(), format="%Y%m%d", errors="coerce")
    data = data.loc[dates.notna()].copy()
    data.index = dates[dates.notna()]
    data = data[columns].apply(pd.to_numeric, errors="coerce") / 100.0
    return data


def regression(portfolio: pd.Series, factors: pd.DataFrame) -> dict[str, object]:
    frame = pd.concat([portfolio.rename("portfolio"), factors], axis=1).dropna()
    y = (frame["portfolio"] - frame["RF"]).to_numpy()
    names = [name for name in frame.columns if name not in {"portfolio", "RF"}]
    x = np.column_stack([np.ones(len(frame)), frame[names].to_numpy()])
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    residual = y - x @ beta
    dof = len(y) - x.shape[1]
    sigma2 = float(residual @ residual / dof)
    covariance = sigma2 * np.linalg.inv(x.T @ x)
    standard_error = np.sqrt(np.diag(covariance))
    t_stat = beta / standard_error
    r2 = 1 - float(residual @ residual) / float(((y - y.mean()) ** 2).sum())
    return {
        "start": str(frame.index.min().date()),
        "end": str(frame.index.max().date()),
        "observations": int(len(frame)),
        "annualized_alpha": float(beta[0] * 252),
        "alpha_t_stat": float(t_stat[0]),
        "loadings": {name: float(value) for name, value in zip(names, beta[1:])},
        "loading_t_stats": {name: float(value) for name, value in zip(names, t_stat[1:])},
        "r_squared": r2,
        "interpretation_warning": "Descriptive full-sample regression on a survivor-biased strategy path; not causal alpha evidence.",
    }


def simple_beta(left: pd.Series, right: pd.Series) -> float:
    frame = pd.concat([left, right], axis=1).dropna()
    return float(frame.cov().iloc[0, 1] / frame.iloc[:, 1].var(ddof=1))


def sector_diagnostics(full: pd.DataFrame) -> dict[str, object]:
    universe = pd.read_csv(ROOT / "data/interim/universe/2026-06-21/oef_equities.csv")
    universe = universe.sort_values("Weight (%)", ascending=False).drop_duplicates("Issuer Key", keep="first")
    sector = dict(zip(universe["YFinance Ticker"], universe["Sector"]))
    tickers = list(sector)
    prices = {}
    for ticker in tickers:
        frame = pd.read_csv(ROOT / f"data/raw/yfinance/oef_2026-06-21/{ticker}/history_daily.csv")
        frame["Date"] = pd.to_datetime(frame["Date"], utc=True).dt.tz_convert(None).dt.normalize()
        prices[ticker] = frame.set_index("Date")["Adj Close"].reindex(full.index).ffill(limit=3)
    panel = pd.DataFrame(prices)

    trades = pd.concat(
        [
            pd.read_csv(RUNS / "EXP-0009/primary_trades.csv", parse_dates=["date"]),
            pd.read_csv(RUNS / "EXP-0010/primary_trades.csv", parse_dates=["date"]),
        ],
        ignore_index=True,
    )
    by_date = {date: group for date, group in trades.groupby("date")}
    units: dict[str, float] = {}
    rows = []
    for date in full.index:
        if date in by_date:
            for trade in by_date[date].itertuples(index=False):
                signed = float(trade.units) if trade.side == "BUY" else -float(trade.units)
                units[trade.ticker] = units.get(trade.ticker, 0.0) + signed
        values = {
            ticker: amount * float(panel.loc[date, ticker])
            for ticker, amount in units.items()
            if abs(amount) > 1e-10 and np.isfinite(panel.loc[date, ticker])
        }
        nav = float(full.loc[date, "nav"])
        sector_weights: dict[str, float] = {}
        if nav > 0:
            for ticker, value in values.items():
                label = sector.get(ticker, "Unknown")
                sector_weights[label] = sector_weights.get(label, 0.0) + value / nav
        rows.append({"date": date, **sector_weights})
    frame = pd.DataFrame(rows).set_index("date").fillna(0.0)
    technology = frame.get("Information Technology", pd.Series(0.0, index=frame.index))
    return {
        "classification": "Current 2026 OEF sector labels projected backward; diagnostic only.",
        "average_information_technology_weight": float(technology[full["nav"] > 0].mean()),
        "maximum_information_technology_weight": float(technology.max()),
        "average_sector_weights": {key: float(value) for key, value in frame.loc[full["nav"] > 0].mean().sort_values(ascending=False).items()},
        "benchmark_limitation": "Historical SPY/QQQ sector weights were not in the preserved dataset, so exact sector-active weights cannot be reconstructed.",
    }


def main() -> None:
    pre = ledger(RUNS / "EXP-0009/primary_daily_ledger.csv")
    hold = ledger(RUNS / "EXP-0010/primary_daily_ledger.csv")
    strategy = pd.concat([pre, hold]).sort_index()
    spy = ledger(RUNS / "EXP-0006/SPY_weekly_ledger.csv").reindex(strategy.index)
    qqq = ledger(RUNS / "EXP-0006/QQQ_weekly_ledger.csv").reindex(strategy.index)

    base = ROOT / "data/raw/fama_french/2026-06-21"
    five = read_factor_zip(
        base / "F-F_Research_Data_5_Factors_2x3_daily_CSV.zip",
        "F-F_Research_Data_5_Factors_2x3_daily.csv",
        ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"],
    )
    momentum = read_factor_zip(
        base / "F-F_Momentum_Factor_daily_CSV.zip",
        "F-F_Momentum_Factor_daily.csv",
        ["Mom"],
    )
    factors = five.join(momentum, how="inner")
    factors = factors[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom", "RF"]]

    result = {
        "audit_id": "EXP-0011-PHASE1A-BENCHMARK-DIAGNOSTICS",
        "betas": {
            "C03-M_vs_SPY": simple_beta(strategy["daily_return"], spy["daily_return"]),
            "C03-M_vs_QQQ": simple_beta(strategy["daily_return"], qqq["daily_return"]),
            "QQQ_vs_SPY": simple_beta(qqq["daily_return"], spy["daily_return"]),
        },
        "factor_regressions": {
            "C03-M": regression(strategy["daily_return"], factors),
            "SPY": regression(spy["daily_return"], factors),
            "QQQ": regression(qqq["daily_return"], factors),
        },
        "factor_interpretation": {
            "SMB": "size exposure (positive indicates smaller-company tilt)",
            "HML": "value exposure",
            "RMW": "profitability exposure, used only as a quality proxy",
            "CMA": "conservative-investment exposure",
            "Mom": "momentum exposure",
        },
        "sector_diagnostics": sector_diagnostics(strategy),
        "benchmark_policy": "SPY and QQQ remain separate required hurdles. Factor diagnostics explain differences; they do not waive either hurdle.",
    }
    output = RUNS / "EXP-0011/phase1a_benchmark_diagnostics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(output)}))


if __name__ == "__main__":
    main()
