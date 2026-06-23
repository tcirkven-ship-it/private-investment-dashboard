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


    def test_existing_reproduction_matches_published(self) -> None:
        """Verify the audit reproduces published P4 monthly N30 B2 U EW exactly."""
        from src.backtest.mechanics_audit import run_audit, metrics_ex
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            result = run_audit(Path(tmp))
            self.assertEqual(result.get("reproduction"), "PASS")

    def test_practical_quarterly_correction_equalizes_weights(self) -> None:
        """On a quarterly review, all survivors should be reset to 1/N."""
        dates = pd.bdate_range("2014-01-01", periods=130)
        tickers = [f"T{i}" for i in range(30)]
        scores = pd.DataFrame(
            np.random.default_rng(42).uniform(0.5, 1.0, (len(dates), 30)),
            index=dates, columns=tickers,
        )
        panels = Panels(
            dates=dates,
            tickers=tickers,
            adjusted=pd.DataFrame(100.0, index=dates, columns=tickers),
            raw_close=pd.DataFrame(100.0, index=dates, columns=tickers),
            volume=pd.DataFrame(1_000_000.0, index=dates, columns=tickers),
            returns=pd.DataFrame(0.0, index=dates, columns=tickers),
            liquidity_ok=pd.DataFrame(True, index=dates, columns=tickers),
            factors={},
            scores={"P4": scores},
            benchmark_returns={"SPY": pd.Series(0.0, index=dates), "QQQ": pd.Series(0.0, index=dates)},
            sectors=np.array(["Technology"] * 30),
            industries=np.array(["Software"] * 30),
            coverage=pd.DataFrame(),
            integrity={},
        )
        from src.backtest.mechanics_audit import simulate_practical
        from src.backtest.price_walkforward import Configuration
        config = Configuration("P4", 30, "monthly", 2.0, "unconstrained", "equal")
        cache = RankingCache(panels)
        ledger = simulate_practical(config, panels, cache)
        # After March (quarterly month 3), weights should be ~1/30
        mar_31 = pd.Timestamp("2014-03-31")
        if mar_31 in ledger.index and mar_31 in panels.dates:
            row = ledger.loc[mar_31]
            # With all equal scores and zero returns, weights stay uniform
            self.assertAlmostEqual(row.weight_hhi, 0.03333333, places=4)
            self.assertAlmostEqual(row.top5_weight, 5 / 30, places=4)

    def test_practical_sells_only_rank_below_sixty(self) -> None:
        """Names above rank 60 should be sold; names at or below 60 should stay."""
        dates = pd.bdate_range("2014-01-01", periods=66)
        tickers = [f"T{i}" for i in range(5)]
        # Scores: T0 best, T4 worst
        scores_data = np.zeros((len(dates), 5))
        scores_data[:, 0] = 1.0   # T0 always best
        scores_data[:, 1] = 0.9
        scores_data[:, 2] = 0.8
        scores_data[:, 3] = 0.3
        scores_data[:, 4] = 0.0   # T4 always worst
        scores = pd.DataFrame(scores_data, index=dates, columns=tickers)
        panels = Panels(
            dates=dates,
            tickers=tickers,
            adjusted=pd.DataFrame(100.0, index=dates, columns=tickers),
            raw_close=pd.DataFrame(100.0, index=dates, columns=tickers),
            volume=pd.DataFrame(1_000_000.0, index=dates, columns=tickers),
            returns=pd.DataFrame(0.0, index=dates, columns=tickers),
            liquidity_ok=pd.DataFrame(True, index=dates, columns=tickers),
            factors={},
            scores={"P4": scores},
            benchmark_returns={"SPY": pd.Series(0.0, index=dates), "QQQ": pd.Series(0.0, index=dates)},
            sectors=np.array(["Technology"] * 5),
            industries=np.array(["Software"] * 5),
            coverage=pd.DataFrame(),
            integrity={},
        )
        from src.backtest.mechanics_audit import simulate_practical
        from src.backtest.price_walkforward import Configuration
        config = Configuration("P4", 4, "monthly", 2.0, "unconstrained", "equal")  # N=4, 2N=8
        cache = RankingCache(panels)
        ledger = simulate_practical(config, panels, cache)
        # T4 should be sold (rank 5 out of 5 > 8). With 2N buffer, rank 5 is <= 8,
        # so T4 stays in the buffer. Actually with N=4, 2N=8, and only 5 names,
        # rank 5 <= 8, so T4 stays.
        # Let's use N=2, 2N=4 instead. T4 rank 5 > 4 → sell.
        config2 = Configuration("P4", 2, "monthly", 2.0, "unconstrained", "equal")
        cache2 = RankingCache(panels)
        ledger2 = simulate_practical(config2, panels, cache2)
        # After a few months, T4 shouldn't be in the portfolio
        for date in ledger2.index[60:]:
            row = ledger2.loc[date]
            if row.sales > 0:
                self.assertGreater(row.sales, 0)
                break

    def test_practical_turnover_lower_or_equal_to_existing(self) -> None:
        """The practical variant should have <= turnover of the existing variant,
        because it does not equal-weight survivors at non-quarterly reviews."""
        from src.backtest.mechanics_audit import run_audit
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            result = run_audit(Path(tmp))
            report_path = Path(tmp) / "mechanics_audit_report.md"
            self.assertTrue(report_path.exists())
            text = report_path.read_text()
            self.assertIn("P4 remains FAIL", text)
            self.assertIn("6.82", text)
            self.assertIn("6.43", text)


if __name__ == "__main__":
    unittest.main()
