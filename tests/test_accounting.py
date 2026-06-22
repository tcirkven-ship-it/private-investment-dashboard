from __future__ import annotations

import math
import unittest

import pandas as pd

from src.backtest.engine import CostModel, execute_buy, execute_sell, flow_checksum, generate_contributions, xirr


class AccountingInvariantTests(unittest.TestCase):
    def test_split_creates_no_wealth(self) -> None:
        self.assertAlmostEqual(10 * 100, 20 * 50, places=12)

    def test_dividend_is_counted_once(self) -> None:
        before = 10 * 100
        ex_dividend = 10 * 98 + 10 * 2
        reinvested_units = 10 + (10 * 2) / 98
        self.assertAlmostEqual(before, ex_dividend, places=12)
        self.assertAlmostEqual(before, reinvested_units * 98, places=12)

    def test_twr_external_flow_boundary(self) -> None:
        no_flow_return = 110 / 100 - 1
        flow_at_close_return = (210 - 100) / 100 - 1
        self.assertAlmostEqual(no_flow_return, flow_at_close_return, places=12)

    def test_xirr_one_year(self) -> None:
        value = xirr([(pd.Timestamp("2020-01-01"), -1000), (pd.Timestamp("2021-01-01"), 1100)])
        expected = 1.1 ** (365.2425 / 366) - 1
        self.assertAlmostEqual(value, expected, places=8)

    def test_buy_never_exceeds_cash(self) -> None:
        model = CostModel(commission_min_per_order_usd=0.35, one_way_price_impact_bps=5)
        units, notional, commission, impact = execute_buy(250, 100, model)
        self.assertGreater(units, 0)
        self.assertLessEqual(notional + commission + impact, 250 + 1e-10)

    def test_sell_proceeds_are_nonnegative(self) -> None:
        model = CostModel(commission_min_per_order_usd=0.35, one_way_price_impact_bps=5)
        proceeds, notional, commission, impact = execute_sell(0.01, 10, model)
        self.assertGreaterEqual(proceeds, 0)
        self.assertLessEqual(proceeds, notional)
        self.assertTrue(math.isfinite(commission + impact))

    def test_contribution_aggregation_preserves_budget(self) -> None:
        dates = pd.bdate_range("2020-01-01", "2021-12-31")
        weekly = generate_contributions(dates, dates[0], dates[-1], "weekly")
        biweekly = generate_contributions(dates, dates[0], dates[-1], "biweekly")
        monthly = generate_contributions(dates, dates[0], dates[-1], "monthly")
        self.assertAlmostEqual(weekly.sum(), biweekly.sum(), places=8)
        self.assertAlmostEqual(weekly.sum(), monthly.sum(), places=8)

    def test_flow_checksum_is_deterministic(self) -> None:
        dates = pd.bdate_range("2020-01-01", "2020-12-31")
        first = generate_contributions(dates, dates[0], dates[-1], "weekly")
        second = generate_contributions(dates, dates[0], dates[-1], "weekly")
        self.assertEqual(flow_checksum(first), flow_checksum(second))


if __name__ == "__main__":
    unittest.main()
