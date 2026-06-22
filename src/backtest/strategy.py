"""Transparent monthly rank strategy with recurring-contribution routing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.backtest.engine import CostModel, execute_buy, execute_sell, load_yfinance_history


@dataclass(frozen=True)
class StrategySpec:
    candidate_id: str
    signal: str
    portfolio_size: int
    lookback_sessions: int = 252
    skip_sessions: int = 21
    rank_buffer_multiple: float = 2.0
    sector_cap: float = 0.25
    name_drift_cap: float = 0.075
    quarterly_weight_correction: bool = True
    contribution_orders_max: int = 3
    minimum_order_usd: float = 25.0


def load_price_panels(snapshot: Path, tickers: list[str], trading_dates: pd.DatetimeIndex) -> dict[str, pd.DataFrame]:
    fields: dict[str, dict[str, pd.Series]] = {"adj": {}, "close": {}, "volume": {}}
    for ticker in tickers:
        history = load_yfinance_history(snapshot / ticker / "history_daily.csv")
        fields["adj"][ticker] = history["Adj Close"]
        fields["close"][ticker] = history["Close"]
        fields["volume"][ticker] = history["Volume"]
    panels = {name: pd.DataFrame(series).reindex(trading_dates) for name, series in fields.items()}
    panels["adj_valuation"] = panels["adj"].ffill(limit=3)
    panels["close_signal"] = panels["close"].ffill(limit=3)
    return panels


def build_signal_tables(panels: dict[str, pd.DataFrame], spec: StrategySpec) -> dict[str, pd.DataFrame]:
    adjusted = panels["adj_valuation"]
    momentum = adjusted.shift(spec.skip_sessions) / adjusted.shift(spec.lookback_sessions) - 1
    log_returns = np.log(adjusted / adjusted.shift(1))
    volatility = log_returns.rolling(252, min_periods=200).std() * np.sqrt(252)
    dollar_volume = (panels["close_signal"] * panels["volume"]).rolling(63, min_periods=55).median()
    observations = panels["adj"].notna().cumsum()
    return {
        "momentum": momentum,
        "volatility": volatility,
        "dollar_volume": dollar_volume,
        "observations": observations,
    }


def month_end_fill_events(dates: pd.DatetimeIndex) -> dict[pd.Timestamp, pd.Timestamp]:
    month_ends = pd.Series(dates, index=dates).groupby(dates.to_period("M")).last().tolist()
    events: dict[pd.Timestamp, pd.Timestamp] = {}
    for signal_date in month_ends:
        position = dates.searchsorted(signal_date, side="right")
        if position < len(dates):
            events[dates[position]] = pd.Timestamp(signal_date)
    return events


def select_targets(
    signal_date: pd.Timestamp,
    current: set[str],
    panels: dict[str, pd.DataFrame],
    tables: dict[str, pd.DataFrame],
    sectors: dict[str, str],
    spec: StrategySpec,
) -> tuple[list[str], pd.DataFrame]:
    close = panels["close_signal"].loc[signal_date]
    dollar_volume = tables["dollar_volume"].loc[signal_date]
    observations = tables["observations"].loc[signal_date]
    eligible = (observations >= 252) & (close >= 5) & (dollar_volume >= 5_000_000)

    if spec.signal == "momentum":
        score = tables["momentum"].loc[signal_date]
    elif spec.signal == "low_volatility":
        score = -tables["volatility"].loc[signal_date]
    elif spec.signal == "momentum_low_volatility":
        momentum = tables["momentum"].loc[signal_date]
        low_vol = -tables["volatility"].loc[signal_date]
        score = pd.concat([momentum.rank(pct=True), low_vol.rank(pct=True)], axis=1).mean(axis=1)
    elif spec.signal == "equal_weight":
        score = pd.Series(0.0, index=close.index)
    else:
        raise ValueError(f"Unsupported signal: {spec.signal}")

    frame = pd.DataFrame({"score": score, "dollar_volume": dollar_volume, "eligible": eligible})
    frame["sector"] = [sectors.get(ticker, "Unknown") for ticker in frame.index]
    frame = frame[frame["eligible"] & frame["score"].notna() & frame["dollar_volume"].notna()].copy()
    frame["ticker"] = frame.index
    frame = frame.sort_values(["score", "dollar_volume", "ticker"], ascending=[False, False, True])
    frame["rank"] = np.arange(1, len(frame) + 1)
    rank_map = frame["rank"].to_dict()

    maximum_per_sector = max(1, int(np.floor(spec.portfolio_size * spec.sector_cap + 1e-12)))
    selected: list[str] = []
    sector_counts: dict[str, int] = {}

    buffered_current = sorted(
        [ticker for ticker in current if ticker in rank_map and rank_map[ticker] <= spec.rank_buffer_multiple * spec.portfolio_size],
        key=lambda ticker: (rank_map[ticker], ticker),
    )
    for ticker in buffered_current:
        sector = sectors.get(ticker, "Unknown")
        if sector_counts.get(sector, 0) >= maximum_per_sector:
            continue
        selected.append(ticker)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    for ticker in frame.index:
        if len(selected) >= spec.portfolio_size:
            break
        if ticker in selected:
            continue
        sector = sectors.get(ticker, "Unknown")
        if sector_counts.get(sector, 0) >= maximum_per_sector:
            continue
        selected.append(ticker)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    return selected, frame


def simulate_strategy(
    panels: dict[str, pd.DataFrame],
    sectors: dict[str, str],
    flows: pd.Series,
    cost: CostModel,
    spec: StrategySpec,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dates = flows.index
    valuation = panels["adj_valuation"].reindex(dates)
    tables = build_signal_tables(panels, spec)
    fill_events = month_end_fill_events(dates)

    holdings: dict[str, float] = {}
    target: list[str] = []
    cash = 0.0
    previous_nav = 0.0
    ledger_rows: list[dict[str, object]] = []
    trade_rows: list[dict[str, object]] = []
    selection_rows: list[dict[str, object]] = []

    def prices_on(date: pd.Timestamp) -> pd.Series:
        return valuation.loc[date]

    def nav_at(prices: pd.Series) -> float:
        return float(cash + sum(units * float(prices.get(ticker, np.nan)) for ticker, units in holdings.items() if np.isfinite(prices.get(ticker, np.nan))))

    def trade_sell(date: pd.Timestamp, ticker: str, units_to_sell: float, reason: str, discretionary: bool) -> tuple[float, float, float]:
        nonlocal cash
        price = float(prices_on(date).get(ticker, np.nan))
        available = holdings.get(ticker, 0.0)
        units_to_sell = min(max(units_to_sell, 0.0), available)
        proceeds, notional, commission, impact = execute_sell(units_to_sell, price, cost)
        if notional <= 0:
            return 0.0, 0.0, 0.0
        cash += proceeds
        remaining = available - units_to_sell
        if remaining <= 1e-12:
            holdings.pop(ticker, None)
        else:
            holdings[ticker] = remaining
        trade_rows.append({"date": date, "ticker": ticker, "side": "SELL", "reason": reason, "units": units_to_sell, "reference_price": price, "notional": notional, "commission": commission, "impact_cost": impact, "discretionary": discretionary})
        return notional, commission, impact

    def trade_buy(date: pd.Timestamp, ticker: str, budget: float, reason: str, discretionary: bool) -> tuple[float, float, float]:
        nonlocal cash
        budget = min(budget, cash)
        price = float(prices_on(date).get(ticker, np.nan))
        units, notional, commission, impact = execute_buy(budget, price, cost)
        if notional <= 0:
            return 0.0, 0.0, 0.0
        cash -= notional + commission + impact
        if abs(cash) < 1e-8:
            cash = 0.0
        holdings[ticker] = holdings.get(ticker, 0.0) + units
        trade_rows.append({"date": date, "ticker": ticker, "side": "BUY", "reason": reason, "units": units, "reference_price": price, "notional": notional, "commission": commission, "impact_cost": impact, "discretionary": discretionary})
        return notional, commission, impact

    def buy_deficits(date: pd.Timestamp, names: list[str], max_names: int | None, reason: str, discretionary: bool) -> tuple[float, float, float]:
        if not names or cash <= spec.minimum_order_usd:
            return 0.0, 0.0, 0.0
        prices = prices_on(date)
        total_nav = nav_at(prices)
        target_value = total_nav / len(names)
        deficits = []
        for ticker in names:
            price = float(prices.get(ticker, np.nan))
            value = holdings.get(ticker, 0.0) * price if np.isfinite(price) else 0.0
            deficit = max(0.0, target_value - value)
            if deficit >= spec.minimum_order_usd and np.isfinite(price):
                deficits.append((ticker, deficit))
        deficits.sort(key=lambda item: (-item[1], item[0]))
        if max_names is not None:
            deficits = deficits[:max_names]
        total_deficit = sum(value for _, value in deficits)
        if total_deficit <= 0:
            return 0.0, 0.0, 0.0
        available = cash
        totals = [0.0, 0.0, 0.0]
        for ticker, deficit in deficits:
            budget = min(deficit, available * deficit / total_deficit)
            if budget < spec.minimum_order_usd:
                continue
            result = trade_buy(date, ticker, budget, reason, discretionary)
            totals = [left + right for left, right in zip(totals, result)]
        return tuple(totals)  # type: ignore[return-value]

    for date in dates:
        prices = prices_on(date)
        flow = float(flows.loc[date])
        cash += flow
        day_notional = day_commission = day_impact = 0.0
        discretionary_notional = contribution_notional = 0.0
        trades_before = len(trade_rows)
        selection_event = date in fill_events

        if selection_event:
            signal_date = fill_events[date]
            selected, ranking = select_targets(signal_date, set(holdings), panels, tables, sectors, spec)
            old_target = set(target)
            target = selected
            for ticker in sorted(set(holdings) - set(target)):
                result = trade_sell(date, ticker, holdings[ticker], "monthly_rank_exit", True)
                day_notional += result[0]
                discretionary_notional += result[0]
                day_commission += result[1]
                day_impact += result[2]

            current_nav = nav_at(prices)
            if current_nav > 0:
                for ticker in sorted(set(holdings) & set(target)):
                    price = float(prices.get(ticker, np.nan))
                    value = holdings[ticker] * price if np.isfinite(price) else 0.0
                    cap_value = spec.name_drift_cap * current_nav
                    if value > cap_value and price > 0:
                        result = trade_sell(date, ticker, (value - cap_value) / price, "name_drift_cap", True)
                        day_notional += result[0]
                        discretionary_notional += result[0]
                        day_commission += result[1]
                        day_impact += result[2]

            quarterly = spec.quarterly_weight_correction and signal_date.month in {3, 6, 9, 12}
            if quarterly and target:
                current_nav = nav_at(prices)
                target_value = current_nav / len(target)
                for ticker in sorted(set(holdings) & set(target)):
                    price = float(prices.get(ticker, np.nan))
                    value = holdings[ticker] * price if np.isfinite(price) else 0.0
                    if value > target_value and price > 0:
                        result = trade_sell(date, ticker, (value - target_value) / price, "quarterly_weight_correction", True)
                        day_notional += result[0]
                        discretionary_notional += result[0]
                        day_commission += result[1]
                        day_impact += result[2]

            result = buy_deficits(date, target, None, "monthly_entry_or_rebalance", True)
            day_notional += result[0]
            discretionary_notional += result[0]
            day_commission += result[1]
            day_impact += result[2]
            selection_rows.append({"fill_date": date, "signal_date": signal_date, "candidate_id": spec.candidate_id, "eligible_count": int(len(ranking)), "target_count": len(target), "held_from_buffer": len(old_target & set(target)), "quarterly_weight_correction": quarterly})
        elif flow > 0 and target:
            result = buy_deficits(date, target, spec.contribution_orders_max, "weekly_contribution", False)
            day_notional += result[0]
            contribution_notional += result[0]
            day_commission += result[1]
            day_impact += result[2]

        nav = nav_at(prices)
        daily_return = 0.0 if previous_nav <= 0 else (nav - flow) / previous_nav - 1
        weights = {ticker: holdings[ticker] * float(prices.get(ticker, np.nan)) / nav for ticker in holdings if nav > 0 and np.isfinite(prices.get(ticker, np.nan))}
        sector_weights: dict[str, float] = {}
        for ticker, weight in weights.items():
            sector = sectors.get(ticker, "Unknown")
            sector_weights[sector] = sector_weights.get(sector, 0.0) + weight
        ledger_rows.append(
            {
                "date": date,
                "external_flow": flow,
                "cash": cash,
                "nav": nav,
                "daily_return": daily_return,
                "trade_notional": day_notional,
                "discretionary_trade_notional": discretionary_notional,
                "contribution_trade_notional": contribution_notional,
                "commission": day_commission,
                "impact_cost": day_impact,
                "trade_count": len(trade_rows) - trades_before,
                "holding_count": len(holdings),
                "target_count": len(target),
                "max_position_weight": max(weights.values(), default=0.0),
                "max_sector_weight": max(sector_weights.values(), default=0.0),
            }
        )
        if cash < -1e-6:
            raise AssertionError(f"Negative cash on {date}: {cash}")
        previous_nav = nav

    ledger = pd.DataFrame(ledger_rows).set_index("date")
    trades = pd.DataFrame(trade_rows)
    selections = pd.DataFrame(selection_rows)
    return ledger, trades, selections
