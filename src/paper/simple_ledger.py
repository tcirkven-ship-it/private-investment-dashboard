"""Broker-agnostic zero-cost daily-close paper ledger for prospective research."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


COST_DISCLOSURE = "The paper results exclude commissions, spreads, slippage, taxes, currency conversion, and broker-specific charges."


@dataclass
class SimplePosition:
    ticker: str
    shares: float = 0.0
    suspended: bool = False
    uncertainty_reason: str | None = None


@dataclass(frozen=True)
class DailyOrder:
    order_id: str
    decision_id: str
    decision_date: str
    ticker: str
    side: str
    cash_budget: float = 0.0
    quantity: float | None = None
    share_convention: str = "fractional"


@dataclass(frozen=True)
class DailyFill:
    order_id: str
    ticker: str
    side: str
    decision_date: str
    execution_date: str
    raw_close: float
    shares: float
    notional: float
    cash_change: float
    status: str


def valid_raw_closes(frame: pd.DataFrame | pd.Series) -> pd.Series:
    if isinstance(frame, pd.DataFrame):
        if "Close" not in frame.columns:
            raise ValueError("Raw Close column is required")
        series = frame["Close"]
    else:
        series = frame
    result = pd.to_numeric(series, errors="coerce")
    result.index = pd.to_datetime(result.index, utc=True).tz_convert(None).normalize()
    result = result[~result.index.duplicated(keep="last")].sort_index()
    return result[result > 0]


def next_valid_raw_close(frame: pd.DataFrame | pd.Series, decision_date: str | pd.Timestamp) -> tuple[pd.Timestamp, float]:
    """First valid raw Close strictly after a completed-data decision date."""
    prices = valid_raw_closes(frame)
    eligible = prices[prices.index > pd.Timestamp(decision_date).normalize()]
    if eligible.empty:
        raise LookupError("No valid raw Close after decision date")
    return eligible.index[0], float(eligible.iloc[0])


def contribution_events(events: list[tuple[str, float]]) -> pd.DataFrame:
    rows = []
    for sequence, (date, amount) in enumerate(events):
        if amount < 0 or not np.isfinite(amount):
            raise ValueError("Contribution must be zero or positive")
        rows.append({"sequence": sequence, "date": str(pd.Timestamp(date).date()), "amount": float(amount)})
    return pd.DataFrame(rows)


class SimplePaperLedger:
    def __init__(self, fractional: bool = True) -> None:
        self.fractional = fractional
        self.cash = 0.0
        self.positions: dict[str, SimplePosition] = {}
        self.events: list[dict] = []
        self.processed_ids: set[str] = set()

    def contribute(self, date: str, amount: float, event_id: str) -> None:
        if event_id in self.processed_ids or amount < 0 or not np.isfinite(amount):
            raise ValueError("Contribution must be unique and nonnegative")
        self.cash += amount
        self.processed_ids.add(event_id)
        self.events.append({"type": "external_contribution", "date": date, "amount": amount,
                            "event_id": event_id, "cash": self.cash})

    def apply_dividend(self, date: str, ticker: str, per_share: float, event_id: str) -> float:
        if event_id in self.processed_ids or per_share < 0:
            raise ValueError("Dividend must be unique and nonnegative")
        amount = self.positions.get(ticker, SimplePosition(ticker)).shares * per_share
        self.cash += amount
        self.processed_ids.add(event_id)
        self.events.append({"type": "ordinary_dividend", "date": date, "ticker": ticker,
                            "per_share": per_share, "amount": amount, "event_id": event_id, "cash": self.cash})
        return amount

    def apply_split(self, date: str, ticker: str, ratio: float, event_id: str) -> None:
        if event_id in self.processed_ids or ratio <= 0 or not np.isfinite(ratio):
            raise ValueError("Split must be unique with a positive ratio")
        position = self.positions.setdefault(ticker, SimplePosition(ticker))
        position.shares *= ratio
        self.processed_ids.add(event_id)
        self.events.append({"type": "split", "date": date, "ticker": ticker, "ratio": ratio,
                            "shares": position.shares, "event_id": event_id})

    def suspend(self, date: str, ticker: str, reason: str) -> None:
        position = self.positions.setdefault(ticker, SimplePosition(ticker))
        position.suspended = True
        position.uncertainty_reason = reason
        self.events.append({"type": "manual_review_required", "date": date, "ticker": ticker,
                            "reason": reason, "shares_preserved": position.shares, "cash": self.cash})

    def nav(self, raw_closes: dict[str, float]) -> float:
        total = self.cash
        for ticker, position in self.positions.items():
            price = raw_closes.get(ticker)
            if price is None or not np.isfinite(price) or price <= 0:
                raise ValueError(f"Valid raw Close required for {ticker}")
            total += position.shares * price
        return total

    def largest_underweights(self, approved: list[str], raw_closes: dict[str, float], max_names: int = 3) -> list[dict]:
        if not approved or max_names <= 0:
            return []
        nav = self.nav({ticker: raw_closes[ticker] for ticker in self.positions})
        target = nav / len(approved)
        rows = []
        for priority, ticker in enumerate(approved):
            shares = self.positions.get(ticker, SimplePosition(ticker)).shares
            value = shares * raw_closes[ticker]
            rows.append({"ticker": ticker, "priority": priority, "current_value": value,
                         "target_value": target, "deficit": max(0.0, target - value)})
        return sorted(rows, key=lambda x: (-x["deficit"], x["priority"], x["ticker"]))[:max_names]

    def contribution_orders(self, decision_id: str, decision_date: str, approved: list[str],
                            raw_closes_at_decision: dict[str, float], max_names: int = 3) -> list[DailyOrder]:
        underweights = [row for row in self.largest_underweights(approved, raw_closes_at_decision, max_names) if row["deficit"] > 0]
        remaining = self.cash
        orders = []
        for row in underweights:
            budget = min(remaining, row["deficit"])
            if budget <= 0:
                continue
            orders.append(DailyOrder(f"{decision_id}:{row['ticker']}:BUY", decision_id, decision_date,
                                     row["ticker"], "BUY", cash_budget=budget,
                                     share_convention="fractional" if self.fractional else "whole"))
            remaining -= budget
        return orders

    def execute(self, order: DailyOrder, raw_history: pd.DataFrame | pd.Series) -> DailyFill:
        if order.order_id in self.processed_ids:
            raise ValueError("Duplicate order")
        position = self.positions.setdefault(order.ticker, SimplePosition(order.ticker))
        if position.suspended:
            raise ValueError("Suspended positions require manual review")
        execution_date, price = next_valid_raw_close(raw_history, order.decision_date)
        side = order.side.upper()
        if side == "BUY":
            budget = min(order.cash_budget, self.cash)
            shares = budget / price
            if order.share_convention == "whole":
                shares = math.floor(shares)
            notional = shares * price
            self.cash -= notional
            position.shares += shares
            cash_change = -notional
        elif side == "SELL":
            requested = position.shares if order.quantity is None else order.quantity
            shares = min(position.shares, requested)
            notional = shares * price
            self.cash += notional
            position.shares -= shares
            cash_change = notional
        else:
            raise ValueError("Side must be BUY or SELL")
        if self.cash < -1e-9:
            raise AssertionError("Negative cash")
        if abs(self.cash) < 1e-10:
            self.cash = 0.0
        self.processed_ids.add(order.order_id)
        fill = DailyFill(order.order_id, order.ticker, side, order.decision_date,
                         str(execution_date.date()), price, shares, notional, cash_change,
                         "FILLED_NEXT_VALID_RAW_CLOSE" if shares > 0 else "ZERO_QUANTITY_RESIDUAL_CASH")
        self.events.append({"type": "daily_close_fill", **asdict(fill), "cash": self.cash,
                            "position_shares": position.shares, "transaction_cost": 0.0})
        return fill

    def canonical_state(self) -> dict:
        return {"cash": round(self.cash, 10),
                "positions": {ticker: asdict(position) for ticker, position in sorted(self.positions.items())},
                "events": self.events, "processed_ids": sorted(self.processed_ids),
                "cost_disclosure": COST_DISCLOSURE}

    def state_checksum(self) -> str:
        payload = json.dumps(self.canonical_state(), sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(payload.encode()).hexdigest()


def rank_exit(rank: int | None, portfolio_size: int = 30) -> bool:
    return rank is None or rank > 2 * portfolio_size


def quarterly_correction_notional(current_value: float, target_value: float, is_quarterly_review: bool) -> float:
    return max(0.0, current_value - target_value) if is_quarterly_review else 0.0


def concentration_diagnostics(weights: pd.DataFrame, sector_cap: float = .25,
                              industry_cap: float = .15, position_cap: float = .075) -> dict:
    sector = weights.groupby("sector").weight.sum()
    industry = weights.groupby("industry").weight.sum()
    return {"sector_pass": bool((sector <= sector_cap + 1e-12).all()),
            "industry_pass": bool((industry <= industry_cap + 1e-12).all()),
            "position_pass": bool((weights.weight <= position_cap + 1e-12).all())}
