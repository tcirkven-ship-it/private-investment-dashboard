#!/usr/bin/env python3
"""Isolated repeated walk-forward research for the frozen YF Price component."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def clean_json(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(item) for item in value]
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean_json(value), indent=2, sort_keys=True, allow_nan=False) + "\n")


def load_history(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["Date"] = pd.to_datetime(frame["Date"], utc=True, errors="coerce").dt.tz_convert(None).dt.normalize()
    frame = frame.dropna(subset=["Date"]).drop_duplicates("Date", keep="last").set_index("Date").sort_index()
    for column in ["Close", "Adj Close", "Volume", "Dividends", "Stock Splits"]:
        if column not in frame:
            frame[column] = np.nan
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


@dataclass(frozen=True)
class Configuration:
    candidate: str
    portfolio_size: int
    schedule: str
    retention_multiple: float
    version: str
    weighting: str = "equal"

    @property
    def id(self) -> str:
        suffix = "U" if self.version == "unconstrained" else "C"
        weight = "EW" if self.weighting == "equal" else "RW"
        return f"{self.candidate}_N{self.portfolio_size}_{self.schedule}_B{self.retention_multiple:g}_{suffix}_{weight}"


@dataclass
class Panels:
    dates: pd.DatetimeIndex
    tickers: list[str]
    adjusted: pd.DataFrame
    raw_close: pd.DataFrame
    volume: pd.DataFrame
    returns: pd.DataFrame
    liquidity_ok: pd.DataFrame
    factors: dict[str, pd.DataFrame]
    scores: dict[str, pd.DataFrame]
    benchmark_returns: dict[str, pd.Series]
    sectors: np.ndarray
    industries: np.ndarray
    coverage: pd.DataFrame
    integrity: dict[str, object]


def cross_sectional_percentile(frame: pd.DataFrame, direction: int, quantiles: list[float]) -> pd.DataFrame:
    low = frame.quantile(quantiles[0], axis=1)
    high = frame.quantile(quantiles[1], axis=1)
    clipped = frame.clip(lower=low, upper=high, axis=0)
    return (clipped * direction).rank(axis=1, pct=True, method="average")


def load_panels(config: dict) -> Panels:
    universe_path = ROOT / config["universe"]["source"]
    history_roots = []
    for item in config["prices"]["history_roots"]:
        root = ROOT / item["path"]
        history_roots.append(root / "tickers" if item["ticker_subdirectory"] else root)
    universe = pd.read_csv(universe_path).sort_values("ticker")
    if len(universe) != int(config["universe"]["expected_count"]):
        raise RuntimeError(f"Frozen universe count mismatch: {len(universe)}")
    tickers = universe.ticker.astype(str).tolist()

    benchmark_root = ROOT / config["prices"]["benchmark_history_root"]
    benchmarks = {ticker: load_history(benchmark_root / ticker / "history_daily.csv") for ticker in config["benchmarks"]}
    dates = benchmarks["SPY"].index.intersection(benchmarks["QQQ"].index)
    dates = dates[(dates >= pd.Timestamp("2000-01-01")) & (dates < pd.Timestamp(config["prices"]["retrieval_end_exclusive"]))]

    adj_map: dict[str, pd.Series] = {}
    close_map: dict[str, pd.Series] = {}
    volume_map: dict[str, pd.Series] = {}
    coverage_rows: list[dict[str, object]] = []
    missing: list[str] = []
    suspicious: list[dict[str, object]] = []
    total_splits = total_dividends = 0
    for ticker in tickers:
        paths = [root / ticker / "history_daily.csv" for root in history_roots]
        path = next((candidate for candidate in paths if candidate.exists()), None)
        if path is None:
            missing.append(ticker)
            continue
        history = load_history(path)
        adjusted = history["Adj Close"].where(history["Adj Close"] > 0)
        raw_close = history["Close"].where(history["Close"] > 0)
        volume = history["Volume"].where(history["Volume"] >= 0)
        adj_map[ticker], close_map[ticker], volume_map[ticker] = adjusted, raw_close, volume
        total_splits += int((history["Stock Splits"].fillna(0) != 0).sum())
        total_dividends += int((history["Dividends"].fillna(0) != 0).sum())
        one_day = adjusted.pct_change(fill_method=None).abs()
        if (one_day > 5).any():
            suspicious.append({"ticker": ticker, "reason": "absolute_adjusted_one_day_return_gt_500pct", "count": int((one_day > 5).sum())})
        coverage_rows.append({
            "ticker": ticker,
            "first_session": str(history.index.min().date()),
            "last_session": str(history.index.max().date()),
            "adjusted_observations": int(adjusted.notna().sum()),
            "split_events": int((history["Stock Splits"].fillna(0) != 0).sum()),
            "dividend_events": int((history["Dividends"].fillna(0) != 0).sum()),
        })

    if len(adj_map) < 40:
        raise RuntimeError("Too few successful price histories for cross-sectional research")
    available_tickers = sorted(adj_map)
    universe = universe.set_index("ticker").loc[available_tickers]
    stale_limit = int(config["prices"]["stale_price_limit_sessions"])
    adjusted_actual = pd.DataFrame(adj_map).reindex(dates)
    adjusted = adjusted_actual.ffill(limit=stale_limit)
    raw_close = pd.DataFrame(close_map).reindex(dates).ffill(limit=stale_limit)
    volume = pd.DataFrame(volume_map).reindex(dates)
    returns = adjusted.pct_change(fill_method=None)
    dollar_volume = raw_close * volume
    liquidity = dollar_volume.rolling(63, min_periods=int(config["prices"]["minimum_liquidity_observations"])).median()
    liquidity_ok = (raw_close >= float(config["prices"]["minimum_price"])) & (liquidity >= float(config["prices"]["minimum_median_dollar_volume_63"]))
    actual_observations = adjusted_actual.notna().cumsum()

    log_returns = np.log(adjusted / adjusted.shift(1))
    factors = {
        "M12_1": adjusted.shift(21) / adjusted.shift(252) - 1,
        "M6_1": adjusted.shift(21) / adjusted.shift(126) - 1,
        "TREND200": adjusted / adjusted.rolling(200, min_periods=200).mean() - 1,
        "VOL252": log_returns.rolling(252, min_periods=200).std(ddof=1) * np.sqrt(252),
    }
    factors["M12_1"] = factors["M12_1"].where(actual_observations >= 253)
    factors["M6_1"] = factors["M6_1"].where(actual_observations >= 127)
    factors["TREND200"] = factors["TREND200"].where(actual_observations >= 200)
    factor_ranks = {
        name: cross_sectional_percentile(frame, int(config["factors"]["directions"][name]), config["factors"]["winsor_quantiles"])
        for name, frame in factors.items()
    }
    scores: dict[str, pd.DataFrame] = {}
    for candidate, names in config["factors"].items():
        if candidate not in {"P1", "P2", "P3", "P4"}:
            continue
        stacked = [factor_ranks[name] for name in names]
        score = sum(stacked) / len(stacked)
        required = pd.DataFrame(True, index=dates, columns=available_tickers)
        for name in names:
            required &= factor_ranks[name].notna()
        scores[candidate] = score.where(required)

    benchmark_returns = {
        ticker: benchmarks[ticker]["Adj Close"].reindex(dates).ffill(limit=stale_limit).pct_change(fill_method=None)
        for ticker in config["benchmarks"]
    }
    coverage = pd.DataFrame(coverage_rows)
    by_year = []
    for year in range(2010, 2026):
        year_dates = dates[dates.year == year]
        if year_dates.empty:
            continue
        last = year_dates[-1]
        by_year.append({
            "year": year,
            "histories_with_any_price": int(adjusted_actual.loc[:last].notna().any().sum()),
            "P1_score_count": int(scores["P1"].loc[last].notna().sum()),
            "P2_score_count": int(scores["P2"].loc[last].notna().sum()),
            "P3_score_count": int(scores["P3"].loc[last].notna().sum()),
            "P4_score_count": int(scores["P4"].loc[last].notna().sum()),
        })
    coverage_year = pd.DataFrame(by_year)
    integrity = {
        "requested_universe_count": len(tickers),
        "successful_history_count": len(available_tickers),
        "configured_history_roots": [str(path) for path in history_roots],
        "missing_history_count": len(missing),
        "missing_histories": missing,
        "suspicious_series": suspicious,
        "split_event_count": total_splits,
        "dividend_event_count": total_dividends,
        "ticker_change_handling": "Current Yahoo ticker history only; permanent identifiers and historical ticker maps unavailable.",
        "delisting_handling": "Unavailable; current-survivor universe omits inactive listings and reliable terminal returns.",
        "ipo_entry_rule": "A name enters only after every candidate-required observation exists; P4 therefore requires M12_1 history plus the other three factors.",
        "stale_price_rule": f"Forward-fill at most {stale_limit} common sessions; longer gaps remain missing and cannot form a score.",
    }
    return Panels(
        dates=dates,
        tickers=available_tickers,
        adjusted=adjusted,
        raw_close=raw_close,
        volume=volume,
        returns=returns,
        liquidity_ok=liquidity_ok,
        factors=factors,
        scores=scores,
        benchmark_returns=benchmark_returns,
        sectors=universe.info_sector.fillna("Unknown").astype(str).to_numpy(),
        industries=universe.info_industry.fillna("Unknown").astype(str).to_numpy(),
        coverage=coverage_year,
        integrity=integrity,
    )


def review_dates(dates: pd.DatetimeIndex, schedule: str) -> set[pd.Timestamp]:
    series = pd.Series(dates, index=dates)
    if schedule == "daily":
        return set(dates)
    if schedule == "weekly":
        return set(series.groupby(dates.to_period("W-FRI")).last())
    if schedule == "biweekly":
        weekly = list(series.groupby(dates.to_period("W-FRI")).last())
        return set(weekly[1::2])
    if schedule == "monthly":
        return set(series.groupby(dates.to_period("M")).last())
    raise ValueError(schedule)


class RankingCache:
    def __init__(self, panels: Panels):
        self.panels = panels
        self.cache: dict[tuple[str, int], tuple[np.ndarray, np.ndarray]] = {}

    def get(self, candidate: str, index: int) -> tuple[np.ndarray, np.ndarray]:
        key = (candidate, index)
        if key not in self.cache:
            values = self.panels.scores[candidate].iloc[index].to_numpy(dtype=float)
            valid = np.isfinite(values)
            order = np.lexsort((np.arange(len(values)), -np.nan_to_num(values, nan=-np.inf)))
            order = order[valid[order]].astype(np.int32)
            ranks = np.full(len(values), np.iinfo(np.int32).max, dtype=np.int32)
            ranks[order] = np.arange(1, len(order) + 1, dtype=np.int32)
            self.cache[key] = order, ranks
        return self.cache[key]


def choose_target(
    config: Configuration,
    panels: Panels,
    cache: RankingCache,
    signal_index: int,
    held: dict[int, float],
    excluded_ticker: int | None = None,
) -> tuple[list[int], np.ndarray]:
    order, ranks = cache.get(config.candidate, signal_index)
    valid = np.isfinite(panels.scores[config.candidate].iloc[signal_index].to_numpy(dtype=float))
    if config.version != "unconstrained":
        valid &= panels.liquidity_ok.iloc[signal_index].fillna(False).to_numpy(dtype=bool)
    if excluded_ticker is not None:
        valid[excluded_ticker] = False
    sector_max = max(1, int(np.floor(config.portfolio_size * 0.25 + 1e-12)))
    industry_max = max(1, int(np.floor(config.portfolio_size * 0.15 + 1e-12)))
    sector_count: dict[str, int] = {}
    industry_count: dict[str, int] = {}
    selected: list[int] = []

    def add(index: int) -> bool:
        if not valid[index] or index in selected:
            return False
        if config.version != "unconstrained":
            sector = str(panels.sectors[index])
            industry = str(panels.industries[index])
            if sector_count.get(sector, 0) >= sector_max or industry_count.get(industry, 0) >= industry_max:
                return False
            sector_count[sector] = sector_count.get(sector, 0) + 1
            industry_count[industry] = industry_count.get(industry, 0) + 1
        selected.append(index)
        return True

    rank_limit = config.retention_multiple * config.portfolio_size
    retained = sorted((idx for idx in held if valid[idx] and ranks[idx] <= rank_limit), key=lambda idx: (ranks[idx], idx))
    for idx in retained:
        if len(selected) >= config.portfolio_size:
            break
        add(idx)
    for idx in order:
        if len(selected) >= config.portfolio_size:
            break
        add(int(idx))
    return selected, ranks


def target_weights(selected: list[int], ranks: np.ndarray, size: int, weighting: str) -> tuple[dict[int, float], float]:
    if not selected:
        return {}, 1.0
    invested_fraction = min(1.0, len(selected) / size)
    if weighting == "equal":
        raw = np.ones(len(selected), dtype=float)
    elif weighting == "rank":
        raw = np.asarray([max(1.0, size + 1.0 - float(ranks[idx])) for idx in selected], dtype=float)
    else:
        raise ValueError(weighting)
    weights = raw / raw.sum() * invested_fraction
    return {idx: float(weight) for idx, weight in zip(selected, weights)}, 1.0 - invested_fraction


def simulate(
    config: Configuration,
    panels: Panels,
    cache: RankingCache,
    excluded_ticker: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = panels.dates
    start_index = int(dates.searchsorted(pd.Timestamp("2014-01-01")))
    signal_dates = review_dates(dates[start_index:], config.schedule)
    fill_to_signal: dict[int, int] = {}
    for signal_date in signal_dates:
        signal_index = int(dates.get_loc(signal_date))
        if signal_index + 1 < len(dates):
            fill_to_signal[signal_index + 1] = signal_index

    weights: dict[int, float] = {}
    cash = 1.0
    rows: list[dict[str, object]] = []
    contributions: dict[int, float] = {}
    for date_index in range(start_index, len(dates)):
        date = dates[date_index]
        day_return = 0.0
        gross_before = dict(weights)
        stock_returns = panels.returns.iloc[date_index].to_numpy(dtype=float)
        portfolio_growth = cash
        for idx, weight in gross_before.items():
            value_return = float(stock_returns[idx]) if np.isfinite(stock_returns[idx]) else 0.0
            contribution = weight * value_return
            day_return += contribution
            contributions[idx] = contributions.get(idx, 0.0) + contribution
            portfolio_growth += weight * (1.0 + value_return)
        if portfolio_growth > 0:
            weights = {
                idx: weight * (1.0 + (float(stock_returns[idx]) if np.isfinite(stock_returns[idx]) else 0.0)) / portfolio_growth
                for idx, weight in gross_before.items()
            }
            cash = cash / portfolio_growth

        turnover = 0.0
        selection_count = len(weights)
        if date_index in fill_to_signal:
            signal_index = fill_to_signal[date_index]
            selected, ranks = choose_target(config, panels, cache, signal_index, weights, excluded_ticker)
            new_weights, new_cash = target_weights(selected, ranks, config.portfolio_size, config.weighting)
            all_names = set(weights) | set(new_weights)
            turnover = sum(abs(new_weights.get(idx, 0.0) - weights.get(idx, 0.0)) for idx in all_names) + abs(new_cash - cash)
            weights, cash = new_weights, new_cash
            selection_count = len(selected)
        hhi = sum(weight * weight for weight in weights.values())
        top5_weight = sum(sorted(weights.values(), reverse=True)[:5])
        rows.append({
            "date": date,
            "daily_return": day_return,
            "gross_turnover": turnover,
            "holding_count": len(weights),
            "selection_count": selection_count,
            "cash_weight": cash,
            "weight_hhi": hhi,
            "top5_weight": top5_weight,
        })
    ledger = pd.DataFrame(rows).set_index("date")
    attribution = pd.DataFrame(
        [{"ticker": panels.tickers[idx], "return_contribution": value} for idx, value in contributions.items()]
    ).sort_values("return_contribution", ascending=False) if contributions else pd.DataFrame(columns=["ticker", "return_contribution"])
    return ledger, attribution


def max_drawdown_stats(returns: pd.Series) -> tuple[float, int]:
    wealth = (1 + returns.fillna(0)).cumprod()
    drawdown = wealth / wealth.cummax() - 1
    max_dd = float(drawdown.min()) if len(drawdown) else np.nan
    longest = run = 0
    for below in (drawdown < -1e-12):
        run = run + 1 if below else 0
        longest = max(longest, run)
    return max_dd, longest


def metrics(
    ledger: pd.DataFrame,
    benchmark_returns: dict[str, pd.Series],
    start: pd.Timestamp,
    end: pd.Timestamp,
    attribution: pd.DataFrame | None = None,
) -> dict[str, object]:
    frame = ledger.loc[(ledger.index >= start) & (ledger.index <= end)].copy()
    returns = frame.daily_return.fillna(0.0)
    observations = len(returns)
    years = observations / 252.0
    total_return = float((1 + returns).prod() - 1)
    annualized = float((1 + total_return) ** (1 / years) - 1) if years > 0 and total_return > -1 else np.nan
    volatility = float(returns.std(ddof=1) * np.sqrt(252)) if observations > 1 else np.nan
    downside = float(np.sqrt(np.mean(np.square(np.minimum(returns, 0)))) * np.sqrt(252)) if observations else np.nan
    sharpe = float(returns.mean() / returns.std(ddof=1) * np.sqrt(252)) if observations > 1 and returns.std(ddof=1) > 0 else np.nan
    max_dd, max_dd_duration = max_drawdown_stats(returns)
    monthly = (1 + returns).resample("ME").prod() - 1
    positive_months = monthly[monthly > 0]
    top5_period_share = float(positive_months.nlargest(5).sum() / positive_months.sum()) if positive_months.sum() > 0 else np.nan
    result: dict[str, object] = {
        "start_date": str(frame.index.min().date()),
        "end_date": str(frame.index.max().date()),
        "observations": observations,
        "total_return": total_return,
        "twr": total_return,
        "annualized_return": annualized,
        "xirr": np.nan,
        "xirr_note": "not_applicable_no_external_contributions",
        "annualized_volatility": volatility,
        "maximum_drawdown": max_dd,
        "maximum_drawdown_duration_sessions": max_dd_duration,
        "sharpe_zero_rf": sharpe,
        "annualized_downside_deviation": downside,
        "annualized_gross_turnover": float(frame.gross_turnover.sum() / years) if years > 0 else np.nan,
        "average_positions": float(frame.holding_count.mean()),
        "average_cash_exposure": float(frame.cash_weight.mean()),
        "average_weight_hhi": float(frame.weight_hhi.mean()),
        "average_top5_weight": float(frame.top5_weight.mean()),
        "top5_period_positive_contribution_share": top5_period_share,
    }
    for ticker, benchmark in benchmark_returns.items():
        bench = benchmark.reindex(frame.index).fillna(0.0)
        bench_total = float((1 + bench).prod() - 1)
        bench_ann = float((1 + bench_total) ** (1 / years) - 1) if years > 0 else np.nan
        bench_dd, _ = max_drawdown_stats(bench)
        result[f"{ticker}_total_return"] = bench_total
        result[f"{ticker}_annualized_return"] = bench_ann
        result[f"active_annualized_return_vs_{ticker}"] = annualized - bench_ann
        result[f"drawdown_difference_vs_{ticker}"] = max_dd - bench_dd
        aligned_monthly = pd.concat([monthly.rename("strategy"), ((1 + bench).resample("ME").prod() - 1).rename("benchmark")], axis=1).dropna()
        for months in (12, 24, 36):
            strategy_roll = (1 + aligned_monthly.strategy).rolling(months).apply(np.prod, raw=True) - 1
            benchmark_roll = (1 + aligned_monthly.benchmark).rolling(months).apply(np.prod, raw=True) - 1
            valid = pd.concat([strategy_roll, benchmark_roll], axis=1).dropna()
            result[f"rolling_{months}m_win_rate_vs_{ticker}"] = float((valid.iloc[:, 0] > valid.iloc[:, 1]).mean()) if len(valid) else np.nan
    if attribution is not None and not attribution.empty:
        positive = attribution.loc[attribution.return_contribution > 0, "return_contribution"]
        result["top5_stock_positive_contribution_share"] = float(positive.nlargest(5).sum() / positive.sum()) if positive.sum() > 0 else np.nan
        result["top5_stock_contributors"] = ";".join(attribution.head(5).ticker.astype(str))
    else:
        result["top5_stock_positive_contribution_share"] = np.nan
        result["top5_stock_contributors"] = ""
    return result


def configurations(config: dict, weighting: str = "equal") -> Iterable[Configuration]:
    grid = config["grid"]
    for candidate, size, schedule, retention, version in itertools.product(
        grid["candidates"], grid["portfolio_sizes"], grid["review_schedules"], grid["retention_multiples"], grid["versions"]
    ):
        yield Configuration(candidate, int(size), schedule, float(retention), version, weighting)


def fold_rows(
    configuration: Configuration,
    ledger: pd.DataFrame,
    attribution: pd.DataFrame,
    panels: Panels,
    years: list[int],
    role: str,
) -> list[dict[str, object]]:
    rows = []
    for sequence, year in enumerate(years, start=1):
        start, end = pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31")
        result = metrics(ledger, panels.benchmark_returns, start, end, attribution=None)
        result.update({
            "configuration_id": configuration.id,
            "candidate": configuration.candidate,
            "portfolio_size": configuration.portfolio_size,
            "review_schedule": configuration.schedule,
            "retention_multiple": configuration.retention_multiple,
            "version": configuration.version,
            "weighting": configuration.weighting,
            "fold_id": f"{'D' if role == 'development' else 'E'}{sequence}",
            "fold_role": role,
            "train_start": "2010-01-01",
            "train_end": f"{year - 1}-12-31",
            "test_year": year,
        })
        rows.append(result)
    return rows


def operational_choice(config: dict, config_results: pd.DataFrame, folds: pd.DataFrame, config_sha: str) -> tuple[pd.DataFrame, dict]:
    rules = config["operational_selection"]
    candidates = config_results[(config_results.candidate == "P4") & (config_results.version == "unconstrained")].copy()
    rows = []
    for _, row in candidates.iterrows():
        local = folds[folds.configuration_id.eq(row.configuration_id)]
        active_spy = local.active_annualized_return_vs_SPY.astype(float)
        active_qqq = local.active_annualized_return_vs_QQQ.astype(float)
        values = {
            "configuration_id": row.configuration_id,
            "median_active_twr_vs_SPY": float(active_spy.median()),
            "median_active_twr_vs_QQQ": float(active_qqq.median()),
            "fold_win_rate_vs_SPY": float((active_spy > 0).mean()),
            "fold_win_rate_vs_QQQ": float((active_qqq > 0).mean()),
            "worst_drawdown_difference_vs_SPY": float(local.drawdown_difference_vs_SPY.min()),
            "annualized_gross_turnover": float(row.annualized_gross_turnover),
            "maximum_single_fold_share_of_absolute_active_SPY": float(active_spy.abs().max() / active_spy.abs().sum()) if active_spy.abs().sum() else np.nan,
        }
        gates = {
            "median_spy": values["median_active_twr_vs_SPY"] > float(rules["required_median_active_twr_vs_spy"]),
            "median_qqq": values["median_active_twr_vs_QQQ"] >= float(rules["required_median_active_twr_vs_qqq"]),
            "win_spy": values["fold_win_rate_vs_SPY"] >= float(rules["minimum_fold_win_rate_vs_spy"]),
            "win_qqq": values["fold_win_rate_vs_QQQ"] >= float(rules["minimum_fold_win_rate_vs_qqq"]),
            "drawdown": values["worst_drawdown_difference_vs_SPY"] >= float(rules["minimum_worst_drawdown_difference_vs_spy"]),
            "turnover": values["annualized_gross_turnover"] <= float(rules["maximum_annualized_gross_turnover"]),
            "fold_dependence": values["maximum_single_fold_share_of_absolute_active_SPY"] <= float(rules["maximum_single_fold_share_of_absolute_active_spy"]),
        }
        rows.append({**values, **{f"gate_{key}": value for key, value in gates.items()}, "all_gates_pass": all(gates.values())})
    table = pd.DataFrame(rows)
    passing = table[table.all_gates_pass].copy()
    fallback = "P4_N30_monthly_B2_U_EW"
    if passing.empty:
        selected_id, passed = fallback, False
        reason = "No P4 operational configuration passed every preregistered development gate; frozen reference retained for evaluation only."
    else:
        passing["size_distance"] = (passing.configuration_id.str.extract(r"_N(\d+)_")[0].astype(int) - 30).abs()
        schedule_priority = {"monthly": 0, "biweekly": 1, "weekly": 2, "daily": 3}
        buffer_priority = {2.0: 0, 1.5: 1, 1.0: 2}
        passing["schedule_priority"] = passing.configuration_id.str.extract(r"_N\d+_([^_]+)_")[0].map(schedule_priority)
        passing["buffer_value"] = passing.configuration_id.str.extract(r"_B([0-9.]+)_")[0].astype(float)
        passing["buffer_priority"] = passing.buffer_value.map(buffer_priority)
        passing = passing.sort_values([
            "annualized_gross_turnover", "median_active_twr_vs_QQQ", "size_distance", "schedule_priority", "buffer_priority"
        ], ascending=[True, False, True, True, True])
        selected_id, passed = str(passing.iloc[0].configuration_id), True
        reason = "Selected by the preregistered development-gate and lexicographic rule."
    selected_row = candidates[candidates.configuration_id.eq(selected_id)].iloc[0]
    choice = {
        "schema": "PRICE-WF-OPERATIONAL-CHOICE-1.0.0",
        "configuration_sha256": config_sha,
        "development_gate_passed": passed,
        "selected_configuration_id": selected_id,
        "selected_candidate": str(selected_row.candidate),
        "selected_portfolio_size": int(selected_row.portfolio_size),
        "selected_review_schedule": str(selected_row.review_schedule),
        "selected_retention_multiple": float(selected_row.retention_multiple),
        "selected_version": str(selected_row.version),
        "selected_weighting": str(selected_row.weighting),
        "selection_reason": reason,
        "evaluation_accessed": False,
    }
    return table, choice


def parse_choice(path: Path) -> Configuration:
    choice = json.loads(path.read_text())
    return Configuration(
        choice["selected_candidate"], int(choice["selected_portfolio_size"]), choice["selected_review_schedule"],
        float(choice["selected_retention_multiple"]), choice["selected_version"], choice["selected_weighting"]
    )


def run(stage: str, config_path: Path, output: Path, choice_path: Path | None) -> None:
    config = json.loads(config_path.read_text())
    config_sha = sha256(config_path)
    panels = load_panels(config)
    cache = RankingCache(panels)
    years = config["folds"]["development_test_years" if stage == "development" else "evaluation_test_years"]
    role = stage
    period_start, period_end = pd.Timestamp(f"{min(years)}-01-01"), pd.Timestamp(f"{max(years)}-12-31")
    output.mkdir(parents=True, exist_ok=True)

    all_fold_rows: list[dict[str, object]] = []
    all_config_rows: list[dict[str, object]] = []
    ledgers: dict[str, pd.DataFrame] = {}
    attributions: dict[str, pd.DataFrame] = {}
    grid = list(configurations(config))
    for number, configuration in enumerate(grid, start=1):
        ledger, attribution = simulate(configuration, panels, cache)
        ledgers[configuration.id], attributions[configuration.id] = ledger, attribution
        aggregate = metrics(ledger, panels.benchmark_returns, period_start, period_end, attribution)
        folds = fold_rows(configuration, ledger, attribution, panels, years, role)
        local = pd.DataFrame(folds)
        aggregate.update({
            "configuration_id": configuration.id,
            "candidate": configuration.candidate,
            "portfolio_size": configuration.portfolio_size,
            "review_schedule": configuration.schedule,
            "retention_multiple": configuration.retention_multiple,
            "version": configuration.version,
            "weighting": configuration.weighting,
            "fold_count": len(years),
            "fold_win_rate_vs_SPY": float((local.active_annualized_return_vs_SPY > 0).mean()),
            "fold_win_rate_vs_QQQ": float((local.active_annualized_return_vs_QQQ > 0).mean()),
            "worst_relative_year_vs_SPY": int(local.loc[local.active_annualized_return_vs_SPY.idxmin(), "test_year"]),
            "worst_relative_return_vs_SPY": float(local.active_annualized_return_vs_SPY.min()),
            "best_relative_year_vs_SPY": int(local.loc[local.active_annualized_return_vs_SPY.idxmax(), "test_year"]),
            "best_relative_return_vs_SPY": float(local.active_annualized_return_vs_SPY.max()),
            "worst_relative_year_vs_QQQ": int(local.loc[local.active_annualized_return_vs_QQQ.idxmin(), "test_year"]),
            "worst_relative_return_vs_QQQ": float(local.active_annualized_return_vs_QQQ.min()),
            "best_relative_year_vs_QQQ": int(local.loc[local.active_annualized_return_vs_QQQ.idxmax(), "test_year"]),
            "best_relative_return_vs_QQQ": float(local.active_annualized_return_vs_QQQ.max()),
            "hypothetical_250_contribution_per_target": 250.0 / configuration.portfolio_size,
        })
        all_config_rows.append(aggregate)
        all_fold_rows.extend(folds)
        if number % 24 == 0:
            print(json.dumps({"stage": stage, "completed_configurations": number, "total": len(grid)}), flush=True)

    config_results = pd.DataFrame(all_config_rows).sort_values("configuration_id")
    fold_results = pd.DataFrame(all_fold_rows).sort_values(["configuration_id", "test_year"])
    config_results.to_csv(output / "configuration_results.csv", index=False)
    fold_results.to_csv(output / "fold_results.csv", index=False)
    panels.coverage.to_csv(output / "coverage_by_year.csv", index=False)
    write_json(output / "data_integrity.json", panels.integrity)

    stage_details: dict[str, object] = {}
    if stage == "development":
        candidates, choice = operational_choice(config, config_results, fold_results, config_sha)
        candidates.to_csv(output / "operational_candidates.csv", index=False)
        write_json(output / "frozen_operational_choice.json", choice)
        stage_details["operational_choice"] = choice
    else:
        if choice_path is None or not choice_path.exists():
            raise RuntimeError("Evaluation requires the frozen development choice")
        frozen = json.loads(choice_path.read_text())
        if frozen["configuration_sha256"] != config_sha:
            raise RuntimeError("Frozen choice/configuration hash mismatch")
        selected = parse_choice(choice_path)
        base_ledger, base_attr = ledgers[selected.id], attributions[selected.id]
        best_ticker = str(base_attr.iloc[0].ticker)
        excluded_index = panels.tickers.index(best_ticker)
        removed_ledger, removed_attr = simulate(selected, panels, cache, excluded_ticker=excluded_index)
        rank_config = Configuration(selected.candidate, selected.portfolio_size, selected.schedule, selected.retention_multiple, selected.version, "rank")
        rank_ledger, rank_attr = simulate(rank_config, panels, cache)
        base_metrics = metrics(base_ledger, panels.benchmark_returns, period_start, period_end, base_attr)
        removed_metrics = metrics(removed_ledger, panels.benchmark_returns, period_start, period_end, removed_attr)
        rank_metrics = metrics(rank_ledger, panels.benchmark_returns, period_start, period_end, rank_attr)
        annual = []
        for year in years:
            row = metrics(base_ledger, panels.benchmark_returns, pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31"))
            annual.append({"year": year, **row})
        annual_frame = pd.DataFrame(annual)
        best_year = int(annual_frame.loc[annual_frame.annualized_return.idxmax(), "year"])
        without_best = annual_frame[annual_frame.year.ne(best_year)]
        compounded_without_best = float(np.prod(1 + without_best.total_return) - 1)
        regimes = {
            "covid_drawdown": ("2020-02-19", "2020-03-23"),
            "covid_recovery": ("2020-03-24", "2020-08-18"),
            "2022_bear": ("2022-01-03", "2022-10-12"),
            "post_2022_recovery": ("2022-10-13", "2023-12-29"),
        }
        regime_rows = []
        for name, (start, end) in regimes.items():
            regime_rows.append({"regime": name, **metrics(base_ledger, panels.benchmark_returns, pd.Timestamp(start), pd.Timestamp(end))})
        pd.DataFrame(regime_rows).to_csv(output / "regime_results.csv", index=False)
        robustness = {
            "selected_configuration": selected.id,
            "development_gate_passed": bool(frozen["development_gate_passed"]),
            "remove_best_stock": {"removed_ticker": best_ticker, "base": base_metrics, "sensitivity": removed_metrics},
            "remove_best_calendar_year": {"removed_year": best_year, "remaining_total_return": compounded_without_best, "remaining_year_count": len(without_best)},
            "rank_weighted_sensitivity": {"configuration_id": rank_config.id, "metrics": rank_metrics},
        }
        write_json(output / "robustness.json", robustness)
        base_ledger.loc[(base_ledger.index >= period_start) & (base_ledger.index <= period_end)].to_csv(output / "selected_daily_returns.csv", date_format="%Y-%m-%d")
        base_attr.to_csv(output / "selected_stock_attribution.csv", index=False)
        stage_details["robustness"] = robustness

    qvp = pd.read_csv(ROOT / "outputs/final/current_daily_qvp_ranking.csv")
    portfolio = pd.read_csv(ROOT / "outputs/final/current_daily_qvp_portfolio.csv")
    p_top = set(qvp.dropna(subset=["price_score"]).nsmallest(30, "price_rank").ticker)
    qvp_top = set(portfolio.ticker)
    manifest = {
        "schema": "PRICE-WF-RUN-1.0.0",
        "stage": stage,
        "experiment_id": "EXP-0019" if stage == "development" else "EXP-0020",
        "evidence_label": config["evidence_label"],
        "configuration_path": str(config_path),
        "configuration_sha256": config_sha,
        "code_commit": git_commit(),
        "scanner_freeze_commit": config["scanner_freeze_commit"],
        "scanner_run_id": config["scanner_run_id"],
        "universe_count": int(config["universe"]["expected_count"]),
        "successful_history_count": panels.integrity["successful_history_count"],
        "configuration_count": len(config_results),
        "fold_row_count": len(fold_results),
        "test_years": years,
        "current_qvp_top30_price_top30_overlap_count": len(p_top & qvp_top),
        "current_qvp_top30_price_top30_overlap_tickers": sorted(p_top & qvp_top),
        "files": {},
        **stage_details,
    }
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            manifest["files"][path.name] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    write_json(output / "manifest.json", manifest)
    print(json.dumps({"stage": stage, "output": str(output), "configurations": len(config_results), "fold_rows": len(fold_results)}))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["development", "evaluation"], required=True)
    parser.add_argument("--config", type=Path, default=Path("research/configs/price_component_walkforward_v1.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--choice", type=Path)
    args = parser.parse_args()
    run(args.stage, args.config, args.output, args.choice)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
