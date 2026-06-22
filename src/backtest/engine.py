"""Small deterministic research ledger for contribution-funded portfolios."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CostModel:
    commission_min_per_order_usd: float
    one_way_price_impact_bps: float

    @property
    def impact_rate(self) -> float:
        return self.one_way_price_impact_bps / 10_000.0


def load_yfinance_history(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["Date"] = pd.to_datetime(frame["Date"], utc=True).dt.tz_convert(None).dt.normalize()
    frame = frame.set_index("Date").sort_index()
    if frame.index.has_duplicates:
        raise ValueError(f"Duplicate dates: {path}")
    return frame.apply(pd.to_numeric, errors="coerce")


def generate_contributions(
    trading_dates: pd.DatetimeIndex,
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
    frequency: str,
    weekly_amount: float = 250.0,
) -> pd.Series:
    """Create equal-annual-budget Friday flows mapped to the next session."""
    dates = pd.DatetimeIndex(trading_dates).sort_values().unique()
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    fridays = pd.date_range(start=start_ts, end=end_ts, freq="W-FRI")
    schedule: list[tuple[pd.Timestamp, float]] = []
    if frequency == "weekly":
        schedule = [(date, weekly_amount) for date in fridays]
    elif frequency == "biweekly":
        for index in range(0, len(fridays), 2):
            group = fridays[index : index + 2]
            schedule.append((group[-1], weekly_amount * len(group)))
    elif frequency == "monthly":
        grouped: dict[pd.Period, list[pd.Timestamp]] = {}
        for date in fridays:
            grouped.setdefault(date.to_period("M"), []).append(date)
        schedule = [(group[-1], weekly_amount * len(group)) for group in grouped.values()]
    else:
        raise ValueError(f"Unsupported contribution frequency: {frequency}")

    flows = pd.Series(0.0, index=dates, name="external_flow")
    for scheduled, amount in schedule:
        position = dates.searchsorted(scheduled, side="left")
        if position < len(dates):
            mapped = dates[position]
            if start_ts <= mapped <= end_ts:
                flows.loc[mapped] += amount
    return flows.loc[(flows.index >= start_ts) & (flows.index <= end_ts)]


def flow_checksum(flows: pd.Series) -> str:
    payload = "\n".join(f"{date.date()},{value:.8f}" for date, value in flows.items() if value != 0)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def xnpv(rate: float, dated_flows: list[tuple[pd.Timestamp, float]]) -> float:
    if rate <= -1:
        return np.inf
    origin = dated_flows[0][0]
    return float(sum(value / ((1 + rate) ** ((date - origin).days / 365.2425)) for date, value in dated_flows))


def xirr(dated_flows: list[tuple[pd.Timestamp, float]], tolerance: float = 1e-10) -> float:
    dated_flows = sorted((pd.Timestamp(date), float(value)) for date, value in dated_flows)
    if not any(value < 0 for _, value in dated_flows) or not any(value > 0 for _, value in dated_flows):
        return float("nan")
    low, high = -0.9999, 1.0
    low_value, high_value = xnpv(low, dated_flows), xnpv(high, dated_flows)
    while np.sign(low_value) == np.sign(high_value) and high < 1_000:
        high *= 2
        high_value = xnpv(high, dated_flows)
    if np.sign(low_value) == np.sign(high_value):
        return float("nan")
    for _ in range(300):
        mid = (low + high) / 2
        mid_value = xnpv(mid, dated_flows)
        if abs(mid_value) < tolerance:
            return mid
        if np.sign(mid_value) == np.sign(low_value):
            low, low_value = mid, mid_value
        else:
            high, high_value = mid, mid_value
    return (low + high) / 2


def execute_buy(cash_budget: float, price: float, cost: CostModel) -> tuple[float, float, float, float]:
    """Return units, notional, commission and impact; total spend <= budget."""
    if not np.isfinite(price) or price <= 0 or cash_budget <= cost.commission_min_per_order_usd:
        return 0.0, 0.0, 0.0, 0.0
    commission = cost.commission_min_per_order_usd
    notional = (cash_budget - commission) / (1 + cost.impact_rate)
    impact = notional * cost.impact_rate
    units = notional / price
    return units, notional, commission, impact


def execute_sell(units: float, price: float, cost: CostModel) -> tuple[float, float, float, float]:
    """Return cash proceeds, notional, commission and impact for a sale."""
    if units <= 0 or not np.isfinite(price) or price <= 0:
        return 0.0, 0.0, 0.0, 0.0
    notional = units * price
    impact = notional * cost.impact_rate
    commission = min(cost.commission_min_per_order_usd, max(0.0, notional - impact))
    proceeds = max(0.0, notional - impact - commission)
    return proceeds, notional, commission, impact


def simulate_benchmark(price: pd.Series, flows: pd.Series, cost: CostModel) -> pd.DataFrame:
    price = price.reindex(flows.index).ffill(limit=3)
    units = 0.0
    cash = 0.0
    previous_nav = 0.0
    rows: list[dict[str, float | pd.Timestamp]] = []
    for date in flows.index:
        current_price = float(price.loc[date])
        flow = float(flows.loc[date])
        cash += flow
        commission = impact = notional = 0.0
        if cash > cost.commission_min_per_order_usd and np.isfinite(current_price):
            bought, notional, commission, impact = execute_buy(cash, current_price, cost)
            units += bought
            cash -= notional + commission + impact
            if abs(cash) < 1e-8:
                cash = 0.0
        nav = cash + units * current_price
        daily_return = 0.0 if previous_nav <= 0 else (nav - flow) / previous_nav - 1
        rows.append(
            {
                "date": date,
                "external_flow": flow,
                "price": current_price,
                "units": units,
                "cash": cash,
                "nav": nav,
                "daily_return": daily_return,
                "trade_notional": notional,
                "commission": commission,
                "impact_cost": impact,
            }
        )
        previous_nav = nav
    return pd.DataFrame(rows).set_index("date")


def max_drawdown(return_series: pd.Series) -> tuple[float, int]:
    wealth = (1 + return_series.fillna(0)).cumprod()
    drawdown = wealth / wealth.cummax() - 1
    max_dd = float(drawdown.min())
    duration = 0
    current = 0
    for value in drawdown:
        current = 0 if value >= -1e-12 else current + 1
        duration = max(duration, current)
    return max_dd, duration


def performance_metrics(ledger: pd.DataFrame, benchmark_returns: pd.Series | None = None) -> dict[str, float | int]:
    active = ledger.loc[ledger["nav"] > 0].copy()
    returns = active["daily_return"].astype(float)
    observations = len(returns)
    total_twr = float((1 + returns).prod() - 1)
    annualized_twr = float((1 + total_twr) ** (252 / max(1, observations)) - 1)
    volatility = float(returns.std(ddof=1) * np.sqrt(252)) if observations > 1 else float("nan")
    downside = returns[returns < 0]
    downside_volatility = float(downside.std(ddof=1) * np.sqrt(252)) if len(downside) > 1 else float("nan")
    sharpe = float(returns.mean() / returns.std(ddof=1) * np.sqrt(252)) if returns.std(ddof=1) > 0 else float("nan")
    sortino = float(returns.mean() / downside.std(ddof=1) * np.sqrt(252)) if len(downside) > 1 and downside.std(ddof=1) > 0 else float("nan")
    max_dd, drawdown_days = max_drawdown(returns)
    flows = [(date, -float(value)) for date, value in active["external_flow"].items() if value != 0]
    flows.append((active.index[-1], float(active["nav"].iloc[-1])))
    years = max((active.index[-1] - active.index[0]).days / 365.2425, 1 / 365.2425)
    average_nav = float(active["nav"].mean())
    turnover_column = "discretionary_trade_notional" if "discretionary_trade_notional" in active.columns else "trade_notional"
    contribution_notional = float(active["contribution_trade_notional"].sum()) if "contribution_trade_notional" in active.columns else 0.0
    discretionary_notional = float(active[turnover_column].sum())
    metrics: dict[str, float | int] = {
        "start_date": str(active.index[0].date()),
        "end_date": str(active.index[-1].date()),
        "observations": observations,
        "total_contributed": float(active["external_flow"].sum()),
        "ending_value": float(active["nav"].iloc[-1]),
        "total_twr": total_twr,
        "annualized_twr": annualized_twr,
        "xirr": float(xirr(flows)),
        "annualized_volatility": volatility,
        "annualized_downside_volatility": downside_volatility,
        "sharpe_zero_rf": sharpe,
        "sortino_zero_rf": sortino,
        "max_drawdown": max_dd,
        "max_drawdown_duration_sessions": drawdown_days,
        "calmar": annualized_twr / abs(max_dd) if max_dd < 0 else float("nan"),
        "commission_cost": float(active["commission"].sum()),
        "impact_cost": float(active["impact_cost"].sum()),
        "total_explicit_cost": float((active["commission"] + active["impact_cost"]).sum()),
        "trade_notional": float(active["trade_notional"].sum()),
        "discretionary_trade_notional": discretionary_notional,
        "contribution_trade_notional": contribution_notional,
        "annualized_gross_turnover": float(discretionary_notional / average_nav / years) if average_nav > 0 else float("nan"),
        "average_cash_weight": float((active["cash"] / active["nav"]).replace([np.inf, -np.inf], np.nan).fillna(0).mean()),
    }
    if benchmark_returns is not None:
        aligned = pd.concat([returns.rename("strategy"), benchmark_returns.rename("benchmark")], axis=1).dropna()
        if len(aligned) > 2 and aligned["benchmark"].var(ddof=1) > 0:
            beta = aligned.cov().loc["strategy", "benchmark"] / aligned["benchmark"].var(ddof=1)
            alpha_daily = aligned["strategy"].mean() - beta * aligned["benchmark"].mean()
            active_returns = aligned["strategy"] - aligned["benchmark"]
            metrics.update(
                {
                    "beta": float(beta),
                    "annualized_alpha_zero_rf": float(alpha_daily * 252),
                    "information_ratio": float(active_returns.mean() / active_returns.std(ddof=1) * np.sqrt(252)) if active_returns.std(ddof=1) > 0 else float("nan"),
                }
            )
    return metrics


def json_dump(data: object, path: Path) -> None:
    def clean(value: object) -> object:
        if isinstance(value, dict):
            return {str(key): clean(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [clean(item) for item in value]
        if isinstance(value, (np.floating, float)):
            return None if not np.isfinite(value) else float(value)
        if isinstance(value, (np.integer, int)):
            return int(value)
        if isinstance(value, (np.bool_, bool)):
            return bool(value)
        return value

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean(data), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
