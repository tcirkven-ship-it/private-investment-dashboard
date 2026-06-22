from __future__ import annotations

import unittest

import pandas as pd

from src.paper.simple_ledger import (COST_DISCLOSURE, DailyOrder, SimplePaperLedger,
    SimplePosition, concentration_diagnostics, contribution_events, next_valid_raw_close,
    quarterly_correction_notional, rank_exit)
from src.paper.universe import EligibilityState, ReviewObservation, SecurityState, transition


def closes(values: list[tuple[str, float | None]]) -> pd.DataFrame:
    return pd.DataFrame({"Close": [value for _, value in values],
                         "Adj Close": [999.0 for _ in values]}, index=pd.to_datetime([date for date, _ in values]))


class SimplifiedForwardLedgerTests(unittest.TestCase):
    def test_no_same_day_close_after_decision(self) -> None:
        date, price = next_valid_raw_close(closes([("2026-05-29", 100), ("2026-06-01", 101)]), "2026-05-29")
        self.assertEqual(str(date.date()), "2026-06-01")
        self.assertEqual(price, 101)

    def test_next_valid_session_skips_missing_close(self) -> None:
        date, price = next_valid_raw_close(closes([("2026-06-01", None), ("2026-06-02", 102)]), "2026-05-29")
        self.assertEqual((str(date.date()), price), ("2026-06-02", 102.0))

    def test_adjusted_close_is_not_execution_price(self) -> None:
        _, price = next_valid_raw_close(closes([("2026-06-01", 101)]), "2026-05-29")
        self.assertEqual(price, 101)
        self.assertNotEqual(price, 999)

    def test_variable_and_irregular_contributions(self) -> None:
        frame = contribution_events([("2026-01-02", 0), ("2026-01-09", 250),
                                     ("2026-02-17", 500), ("2026-04-03", 1000),
                                     ("2026-05-11", 123.45)])
        self.assertEqual(frame.amount.tolist(), [0, 250, 500, 1000, 123.45])

    def test_negative_contribution_rejected(self) -> None:
        with self.assertRaises(ValueError): contribution_events([("2026-01-01", -1)])

    def test_fractional_arithmetic_and_zero_cost(self) -> None:
        ledger = SimplePaperLedger(); ledger.contribute("2026-05-29", 250, "c1")
        fill = ledger.execute(DailyOrder("o1", "d1", "2026-05-29", "ABC", "BUY", 250), closes([("2026-06-01", 100)]))
        self.assertEqual(fill.shares, 2.5)
        self.assertEqual(ledger.cash, 0)
        self.assertIn("exclude commissions", COST_DISCLOSURE)

    def test_whole_share_sensitivity_retains_residual_cash(self) -> None:
        ledger = SimplePaperLedger(fractional=False); ledger.contribute("2026-05-29", 250, "c1")
        fill = ledger.execute(DailyOrder("o1", "d1", "2026-05-29", "ABC", "BUY", 250, share_convention="whole"), closes([("2026-06-01", 100)]))
        self.assertEqual(fill.shares, 2)
        self.assertEqual(ledger.cash, 50)

    def test_no_negative_cash_when_budget_exceeds_cash(self) -> None:
        ledger = SimplePaperLedger(); ledger.contribute("2026-05-29", 50, "c1")
        fill = ledger.execute(DailyOrder("o1", "d1", "2026-05-29", "ABC", "BUY", 500), closes([("2026-06-01", 100)]))
        self.assertEqual(fill.notional, 50)
        self.assertGreaterEqual(ledger.cash, 0)

    def test_raw_close_valuation(self) -> None:
        ledger = SimplePaperLedger(); ledger.positions["ABC"] = SimplePosition("ABC", 2)
        self.assertEqual(ledger.nav({"ABC": 100}), 200)
        with self.assertRaises(ValueError): ledger.nav({})

    def test_dividend_posted_once(self) -> None:
        ledger = SimplePaperLedger(); ledger.positions["ABC"] = SimplePosition("ABC", 10)
        self.assertEqual(ledger.apply_dividend("2026-06-01", "ABC", 2, "div1"), 20)
        with self.assertRaises(ValueError): ledger.apply_dividend("2026-06-01", "ABC", 2, "div1")

    def test_forward_and_reverse_splits_preserve_value(self) -> None:
        ledger = SimplePaperLedger(); ledger.positions["ABC"] = SimplePosition("ABC", 10)
        ledger.apply_split("2026-06-01", "ABC", 2, "s1")
        self.assertEqual(ledger.nav({"ABC": 50}), 1000)
        ledger.apply_split("2026-06-02", "ABC", .25, "s2")
        self.assertEqual(ledger.nav({"ABC": 200}), 1000)

    def test_manual_review_suspends_activity_and_preserves_state(self) -> None:
        ledger = SimplePaperLedger(); ledger.cash = 10; ledger.positions["ABC"] = SimplePosition("ABC", 2)
        ledger.suspend("2026-06-01", "ABC", "acquisition_unresolved")
        self.assertEqual((ledger.cash, ledger.positions["ABC"].shares), (10, 2))
        with self.assertRaises(ValueError):
            ledger.execute(DailyOrder("o1", "d1", "2026-06-01", "ABC", "BUY", 10), closes([("2026-06-02", 100)]))

    def test_underweight_routing_uses_at_most_three_and_does_not_sell(self) -> None:
        ledger = SimplePaperLedger(); ledger.contribute("2026-05-29", 250, "c1")
        approved = [f"T{i}" for i in range(30)]
        prices = {ticker: 10 for ticker in approved}
        orders = ledger.contribution_orders("d1", "2026-05-29", approved, prices)
        self.assertEqual(len(orders), 3)
        self.assertTrue(all(order.side == "BUY" for order in orders))
        self.assertAlmostEqual(sum(order.cash_budget for order in orders), 25)

    def test_ranking_is_independent_of_contribution_amount(self) -> None:
        approved = ["A", "B", "C"]
        prices = {ticker: 10 for ticker in approved}
        rankings = []
        for amount in [0, 250, 500, 1000]:
            ledger = SimplePaperLedger(); ledger.contribute("2026-05-29", amount, f"c{amount}")
            rankings.append([x["ticker"] for x in ledger.largest_underweights(approved, prices)])
        self.assertTrue(all(value == approved for value in rankings))

    def test_contribution_and_benchmark_parity(self) -> None:
        events = [("2026-01-02", 250), ("2026-01-17", 500), ("2026-03-11", 0), ("2026-04-01", 1000)]
        states = []
        for _ in ["strategy", "SPY", "QQQ"]:
            ledger = SimplePaperLedger()
            for index, (date, amount) in enumerate(events): ledger.contribute(date, amount, f"c{index}")
            states.append((ledger.cash, [e["amount"] for e in ledger.events]))
        self.assertEqual(states[0], states[1]); self.assertEqual(states[1], states[2])

    def test_sell_uses_next_valid_close(self) -> None:
        ledger = SimplePaperLedger(); ledger.positions["ABC"] = SimplePosition("ABC", 2)
        fill = ledger.execute(DailyOrder("o1", "d1", "2026-05-29", "ABC", "SELL", quantity=1), closes([("2026-06-01", 100)]))
        self.assertEqual((fill.cash_change, ledger.positions["ABC"].shares), (100, 1))

    def test_deterministic_reconstruction(self) -> None:
        def run() -> str:
            ledger = SimplePaperLedger(); ledger.contribute("2026-05-29", 250, "c1")
            ledger.execute(DailyOrder("o1", "d1", "2026-05-29", "ABC", "BUY", 250), closes([("2026-06-01", 100)]))
            return ledger.state_checksum()
        self.assertEqual(run(), run())

    def test_rank_exit(self) -> None:
        self.assertFalse(rank_exit(60)); self.assertTrue(rank_exit(61)); self.assertTrue(rank_exit(None))

    def test_two_review_eligibility_exit(self) -> None:
        state = SecurityState("ABC", EligibilityState.ELIGIBLE, new_orders_allowed=True)
        state, _ = transition(state, ReviewObservation("ABC", False, ordinary_failure_reason="liquidity"))
        self.assertFalse(state.exit_required)
        state, _ = transition(state, ReviewObservation("ABC", False, ordinary_failure_reason="liquidity"))
        self.assertTrue(state.exit_required)

    def test_quarterly_correction(self) -> None:
        self.assertEqual(quarterly_correction_notional(100, 75, False), 0)
        self.assertEqual(quarterly_correction_notional(100, 75, True), 25)

    def test_sector_industry_and_position_limits(self) -> None:
        frame = pd.DataFrame([{"weight": .08, "sector": "T", "industry": "S"},
                              {"weight": .20, "sector": "T", "industry": "H"}])
        result = concentration_diagnostics(frame)
        self.assertFalse(result["sector_pass"])
        self.assertFalse(result["position_pass"])

    def test_zero_contribution_is_valid_noop(self) -> None:
        ledger = SimplePaperLedger(); ledger.contribute("2026-05-29", 0, "c0")
        self.assertEqual(ledger.cash, 0)


if __name__ == "__main__":
    unittest.main()
