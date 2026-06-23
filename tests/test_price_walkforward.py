from __future__ import annotations

import unittest
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.backtest.price_walkforward import (
    Configuration,
    Panels,
    RankingCache,
    choose_target,
    cross_sectional_percentile,
    review_dates,
    simulate,
    target_weights,
    load_panels,
)


def panels_fixture() -> Panels:
    dates = pd.bdate_range("2014-01-01", periods=8)
    tickers = ["A", "B", "C"]
    zeros = pd.DataFrame(0.0, index=dates, columns=tickers)
    scores = pd.DataFrame(
        [[0.9, 0.8, 0.7]] * len(dates), index=dates, columns=tickers
    )
    returns = zeros.copy()
    returns.loc[dates[1], "A"] = 0.10
    returns.loc[dates[2], "A"] = 0.10
    return Panels(
        dates=dates,
        tickers=tickers,
        adjusted=pd.DataFrame(100.0, index=dates, columns=tickers),
        raw_close=pd.DataFrame(100.0, index=dates, columns=tickers),
        volume=pd.DataFrame(1_000_000.0, index=dates, columns=tickers),
        returns=returns,
        liquidity_ok=pd.DataFrame(True, index=dates, columns=tickers),
        factors={},
        scores={name: scores.copy() for name in ("P1", "P2", "P3", "P4")},
        benchmark_returns={"SPY": pd.Series(0.0, index=dates), "QQQ": pd.Series(0.0, index=dates)},
        sectors=np.array(["Technology", "Industrials", "Healthcare"]),
        industries=np.array(["Software", "Machinery", "Biotech"]),
        coverage=pd.DataFrame(),
        integrity={},
    )


class PriceWalkForwardTests(unittest.TestCase):
    def test_cross_sectional_direction_and_average_rank(self) -> None:
        frame = pd.DataFrame([[1.0, 2.0, 3.0]], columns=["A", "B", "C"])
        high = cross_sectional_percentile(frame, 1, [0.0, 1.0]).iloc[0]
        low = cross_sectional_percentile(frame, -1, [0.0, 1.0]).iloc[0]
        self.assertEqual(high.idxmax(), "C")
        self.assertEqual(low.idxmax(), "A")
        self.assertAlmostEqual(float(high["B"]), 2 / 3)

    def test_signal_close_cannot_earn_next_session_fill_return(self) -> None:
        panels = panels_fixture()
        config = Configuration("P4", 1, "daily", 1.0, "unconstrained")
        ledger, _ = simulate(config, panels, RankingCache(panels))
        self.assertEqual(float(ledger.loc[panels.dates[1], "daily_return"]), 0.0)
        self.assertAlmostEqual(float(ledger.loc[panels.dates[2], "daily_return"]), 0.10)

    def test_rank_2n_retains_existing_rank_two(self) -> None:
        panels = panels_fixture()
        cache = RankingCache(panels)
        retained, _ = choose_target(
            Configuration("P4", 1, "monthly", 2.0, "unconstrained"), panels, cache, 0, {1: 1.0}
        )
        immediate, _ = choose_target(
            Configuration("P4", 1, "monthly", 1.0, "unconstrained"), panels, cache, 0, {1: 1.0}
        )
        self.assertEqual(retained, [1])
        self.assertEqual(immediate, [0])

    def test_target_weights_preserve_cash_when_underfilled(self) -> None:
        weights, cash = target_weights([0, 1], np.array([1, 2, 3]), 4, "equal")
        self.assertAlmostEqual(sum(weights.values()), 0.5)
        self.assertAlmostEqual(cash, 0.5)

    def test_review_schedules_are_subsets_of_sessions(self) -> None:
        dates = pd.bdate_range("2024-01-01", "2024-03-31")
        daily = review_dates(dates, "daily")
        weekly = review_dates(dates, "weekly")
        monthly = review_dates(dates, "monthly")
        self.assertEqual(daily, set(dates))
        self.assertTrue(monthly.issubset(daily))
        self.assertTrue(weekly.issubset(daily))
        self.assertLess(len(monthly), len(weekly))

    def test_local_aapl_factors_match_frozen_formulas(self) -> None:
        root = Path(__file__).resolve().parents[1]
        config = json.loads((root / "research/configs/price_component_walkforward_v1.json").read_text())
        panels = load_panels(config)
        ticker = "AAPL"
        date = pd.Timestamp("2025-12-31")
        position = panels.dates.get_loc(date)
        series = panels.adjusted[ticker]
        expected_m12 = series.iloc[position - 21] / series.iloc[position - 252] - 1
        expected_m6 = series.iloc[position - 21] / series.iloc[position - 126] - 1
        expected_trend = series.iloc[position] / series.iloc[position - 199 : position + 1].mean() - 1
        expected_vol = np.log(series / series.shift(1)).iloc[position - 251 : position + 1].std(ddof=1) * np.sqrt(252)
        self.assertAlmostEqual(float(panels.factors["M12_1"].loc[date, ticker]), float(expected_m12), places=12)
        self.assertAlmostEqual(float(panels.factors["M6_1"].loc[date, ticker]), float(expected_m6), places=12)
        self.assertAlmostEqual(float(panels.factors["TREND200"].loc[date, ticker]), float(expected_trend), places=12)
        self.assertAlmostEqual(float(panels.factors["VOL252"].loc[date, ticker]), float(expected_vol), places=12)


if __name__ == "__main__":
    unittest.main()
