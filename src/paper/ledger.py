"""Superseded execution-heavy rehearsal ledger retained for audit history.

The active simplified protocol uses ``src.paper.simple_ledger``.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import time

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExecutionPolicy:
    submission_time: time = time(15, 45)
    expiration_time: time = time(15, 55)
    buy_limit_offset_bps: float = 10.0
    sell_limit_offset_bps: float = 10.0
    expected_adverse_bps: float = 5.0
    interval_minutes: int = 5
    maximum_first_bar_volume_participation: float = 0.01


@dataclass(frozen=True)
class CommissionPolicy:
    per_whole_share_usd: float = 0.0035
    whole_minimum_usd: float = 0.35
    maximum_fraction_of_trade_value: float = 0.01
    fractional_rate: float = 0.01
    fractional_minimum_usd: float = 0.01


@dataclass(frozen=True)
class Order:
    order_id: str
    decision_id: str
    ticker: str
    side: str
    quantity: float
    limit_price: float
    session_date: str
    share_convention: str = "fractional"
    mandatory: bool = False


@dataclass
class Position:
    ticker: str
    shares: float = 0.0
    suspended: bool = False
    uncertainty_reason: str | None = None
    conservative_price: float | None = None


@dataclass(frozen=True)
class FillResult:
    order_id: str
    status: str
    filled_quantity: float
    fill_price: float | None
    notional: float
    commission: float
    cash_change: float
    remainder_quantity: float
    reason: str


def commission(quantity: float, price: float, policy: CommissionPolicy) -> float:
    notional = abs(quantity * price)
    if notional <= 0:
        return 0.0
    fractional = not math.isclose(abs(quantity), round(abs(quantity)), abs_tol=1e-10)
    if fractional:
        return min(notional * policy.maximum_fraction_of_trade_value,
                   max(policy.fractional_minimum_usd, notional * policy.fractional_rate))
    return min(notional * policy.maximum_fraction_of_trade_value,
               max(policy.whole_minimum_usd, abs(quantity) * policy.per_whole_share_usd))


def limit_price(reference_raw_close: float, side: str, policy: ExecutionPolicy) -> float:
    if not np.isfinite(reference_raw_close) or reference_raw_close <= 0:
        raise ValueError("Reference raw Close must be positive")
    offset = policy.buy_limit_offset_bps if side.upper() == "BUY" else -policy.sell_limit_offset_bps
    return round(reference_raw_close * (1 + offset / 10_000), 4)


def contribution_schedule(trading_dates: pd.DatetimeIndex, start: str, end: str, amount: float = 250.0) -> pd.Series:
    dates = pd.DatetimeIndex(trading_dates).tz_localize(None).normalize().sort_values().unique()
    flows = pd.Series(0.0, index=dates, name="contribution")
    for friday in pd.date_range(start, end, freq="W-FRI"):
        location = dates.searchsorted(friday, side="left")
        if location < len(dates) and dates[location] <= pd.Timestamp(end):
            flows.loc[dates[location]] += amount
    return flows


class PaperLedger:
    def __init__(self, execution: ExecutionPolicy | None = None, costs: CommissionPolicy | None = None) -> None:
        self.execution = execution or ExecutionPolicy()
        self.costs = costs or CommissionPolicy()
        self.cash = 0.0
        self.positions: dict[str, Position] = {}
        self.processed_orders: set[str] = set()
        self.processed_decisions: set[tuple[str, str, str]] = set()
        self.processed_actions: set[str] = set()
        self.events: list[dict] = []

    def contribute(self, date: str, amount: float, event_id: str) -> None:
        if amount <= 0 or event_id in self.processed_actions:
            raise ValueError("Contribution must be positive and unique")
        self.cash += amount
        self.processed_actions.add(event_id)
        self.events.append({"type": "contribution", "date": date, "event_id": event_id, "amount": amount, "cash": self.cash})

    def apply_dividend(self, date: str, ticker: str, per_share: float, event_id: str, special: bool = False) -> float:
        if event_id in self.processed_actions:
            raise ValueError("Duplicate corporate-action event")
        if per_share < 0:
            raise ValueError("Dividend cannot be negative")
        amount = self.positions.get(ticker, Position(ticker)).shares * per_share
        self.cash += amount
        self.processed_actions.add(event_id)
        self.events.append({"type": "special_dividend" if special else "ordinary_dividend", "date": date,
                            "ticker": ticker, "event_id": event_id, "per_share": per_share, "amount": amount, "cash": self.cash})
        return amount

    def apply_split(self, date: str, ticker: str, ratio: float, event_id: str) -> None:
        if event_id in self.processed_actions:
            raise ValueError("Duplicate corporate-action event")
        if not np.isfinite(ratio) or ratio <= 0:
            raise ValueError("Split ratio must be positive")
        position = self.positions.setdefault(ticker, Position(ticker))
        position.shares *= ratio
        self.processed_actions.add(event_id)
        self.events.append({"type": "split", "date": date, "ticker": ticker, "event_id": event_id,
                            "ratio": ratio, "shares": position.shares})

    def suspend_for_exception(self, date: str, ticker: str, reason: str, last_verified_raw_close: float) -> None:
        if not np.isfinite(last_verified_raw_close) or last_verified_raw_close < 0:
            raise ValueError("Conservative price must be nonnegative")
        position = self.positions.setdefault(ticker, Position(ticker))
        position.suspended = True
        position.uncertainty_reason = reason
        position.conservative_price = last_verified_raw_close * 0.5
        self.events.append({"type": "corporate_action_exception", "date": date, "ticker": ticker, "reason": reason,
                            "conservative_rule": "50_percent_of_last_verified_raw_close_pending_manual_resolution",
                            "conservative_price": position.conservative_price})

    def _window(self, bars: pd.DataFrame, session_date: str) -> pd.DataFrame:
        if bars.empty or not {"Open", "High", "Low", "Close"}.issubset(bars.columns):
            return pd.DataFrame()
        frame = bars.copy()
        if not isinstance(frame.index, pd.DatetimeIndex):
            frame.index = pd.to_datetime(frame.index)
        if frame.index.tz is None:
            frame.index = frame.index.tz_localize("America/New_York")
        else:
            frame.index = frame.index.tz_convert("America/New_York")
        day = pd.Timestamp(session_date).date()
        frame = frame[frame.index.date == day]
        frame = frame.between_time(self.execution.submission_time, self.execution.expiration_time, inclusive="both")
        return frame.dropna(subset=["Open", "High", "Low", "Close"])

    def process_order(self, order: Order, bars: pd.DataFrame, fill_fraction: float | None = None) -> FillResult:
        decision_key = (order.decision_id, order.ticker, order.side.upper())
        if order.order_id in self.processed_orders or decision_key in self.processed_decisions:
            raise ValueError("Duplicate order or ticker-side decision")
        self.processed_orders.add(order.order_id)
        self.processed_decisions.add(decision_key)
        if order.quantity <= 0 or (fill_fraction is not None and not 0 <= fill_fraction <= 1):
            raise ValueError("Invalid quantity or fill fraction")
        position = self.positions.setdefault(order.ticker, Position(order.ticker))
        if position.suspended:
            return FillResult(order.order_id, "REJECTED_SUSPENDED", 0, None, 0, 0, 0, order.quantity, position.uncertainty_reason or "suspended")
        window = self._window(bars, order.session_date)
        if window.empty:
            return FillResult(order.order_id, "UNFILLED_MISSING_DATA", 0, None, 0, 0, 0, order.quantity, "no_reconstructable_window_bars")
        side = order.side.upper()
        crossed_rows = window[window["Low"] <= order.limit_price] if side == "BUY" else window[window["High"] >= order.limit_price]
        crossed = not crossed_rows.empty
        if not crossed:
            return FillResult(order.order_id, "UNFILLED_EXPIRED", 0, None, 0, 0, 0, order.quantity, "limit_not_crossed_by_expiration")
        first = crossed_rows.iloc[0]
        if fill_fraction is None:
            bar_volume = float(first.get("Volume", float("nan")))
            if not np.isfinite(bar_volume) or bar_volume < 0:
                return FillResult(order.order_id, "UNFILLED_MISSING_DATA", 0, None, 0, 0, 0, order.quantity, "first_crossed_bar_volume_missing")
            fill_fraction = min(1.0, bar_volume * self.execution.maximum_first_bar_volume_participation / order.quantity)
        adverse = self.execution.expected_adverse_bps / 10_000
        if side == "BUY":
            price = min(order.limit_price, float(first["Close"]) * (1 + adverse))
        elif side == "SELL":
            price = max(order.limit_price, float(first["Close"]) * (1 - adverse))
        else:
            raise ValueError("Side must be BUY or SELL")
        quantity = order.quantity * fill_fraction
        if order.share_convention == "whole":
            quantity = math.floor(quantity)
        if side == "SELL":
            quantity = min(quantity, position.shares)
        if quantity <= 0:
            return FillResult(order.order_id, "UNFILLED_ROUNDING", 0, None, 0, 0, 0, order.quantity, "quantity_rounded_or_clipped_to_zero")
        if side == "BUY":
            estimated_commission = commission(quantity, price, self.costs)
            total = quantity * price + estimated_commission
            if total > self.cash + 1e-10:
                if order.share_convention == "whole":
                    quantity = math.floor(self.cash / price)
                    while quantity > 0 and quantity * price + commission(quantity, price, self.costs) > self.cash + 1e-10:
                        quantity -= 1
                else:
                    quantity = self.cash / (price * (1 + self.costs.fractional_rate))
                if quantity <= 0:
                    return FillResult(order.order_id, "UNFILLED_INSUFFICIENT_CASH", 0, None, 0, 0, 0, order.quantity, "cash_after_commission_insufficient")
            fee = commission(quantity, price, self.costs)
            notional = quantity * price
            cash_change = -(notional + fee)
            if self.cash + cash_change < -1e-8:
                raise AssertionError("Negative cash prevention failed")
            self.cash = max(0.0, self.cash + cash_change)
            position.shares += quantity
        else:
            fee = commission(quantity, price, self.costs)
            notional = quantity * price
            cash_change = notional - fee
            self.cash += cash_change
            position.shares -= quantity
            if position.shares < 1e-10:
                position.shares = 0.0
        status = "FILLED" if math.isclose(quantity, order.quantity, rel_tol=0, abs_tol=1e-8) else "PARTIAL_FILLED_REMAINDER_CANCELLED"
        result = FillResult(order.order_id, status, quantity, price, notional, fee, cash_change,
                            max(0.0, order.quantity - quantity), "archived_window_limit_cross")
        self.events.append({"type": "fill", **asdict(result), "ticker": order.ticker, "side": side,
                            "decision_id": order.decision_id, "cash": self.cash, "shares": position.shares})
        return result

    def nav(self, raw_close: dict[str, float]) -> float:
        total = self.cash
        for ticker, position in self.positions.items():
            price = position.conservative_price if position.suspended else raw_close.get(ticker)
            if price is None or not np.isfinite(price) or price < 0:
                raise ValueError(f"Missing raw Close for {ticker}")
            total += position.shares * price
        return total

    def canonical_state(self) -> dict:
        return {"cash": round(self.cash, 10),
                "positions": {ticker: asdict(position) for ticker, position in sorted(self.positions.items())},
                "events": self.events, "processed_orders": sorted(self.processed_orders),
                "processed_actions": sorted(self.processed_actions)}

    def state_checksum(self) -> str:
        payload = json.dumps(self.canonical_state(), sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(payload.encode()).hexdigest()


def cap_diagnostics(weights: pd.DataFrame, sector_cap: float, industry_cap: float) -> dict:
    required = {"ticker", "weight", "sector", "industry"}
    if not required.issubset(weights.columns):
        raise ValueError("Missing concentration columns")
    sector = weights.groupby("sector")["weight"].sum()
    industry = weights.groupby("industry")["weight"].sum()
    return {"sector_pass": bool((sector <= sector_cap + 1e-12).all()),
            "industry_pass": bool((industry <= industry_cap + 1e-12).all()),
            "max_sector": float(sector.max()) if len(sector) else 0.0,
            "max_industry": float(industry.max()) if len(industry) else 0.0}


def rank_buffer_exit(rank: int | None, portfolio_size: int = 30) -> bool:
    return rank is None or rank > 2 * portfolio_size


def quarterly_trim_notional(current_value: float, nav: float, quarter_end: bool, name_cap: float = 0.075) -> float:
    if not quarter_end or nav <= 0:
        return 0.0
    return max(0.0, current_value - nav * name_cap)
