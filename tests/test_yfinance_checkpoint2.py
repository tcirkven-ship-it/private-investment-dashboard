import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.validation.run_yfinance_checkpoint2 import Statements, growth, safe_div, semantic_row
from src.data.archive_yfinance_snapshot import archive


class YFinanceCheckpoint2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.aliases = json.loads(Path("research/configs/yfinance_statement_aliases_v1.json").read_text())

    def test_alias_resolution_is_name_based_and_ordered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            pd.DataFrame({"2025": [12.0]}, index=["OperatingRevenue"]).to_csv(path / "trailing_income.csv")
            statements = Statements(path, self.aliases)
            value, source = statements.current("revenue")
            self.assertEqual(value, 12.0)
            self.assertEqual(source["alias"], "OperatingRevenue")

    def test_unknown_alias_remains_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            pd.DataFrame({"2025": [12.0]}, index=["RevenueMaybe"]).to_csv(path / "trailing_income.csv")
            value, source = Statements(path, self.aliases).current("revenue")
            self.assertIsNone(value)
            self.assertEqual(source["reason"], "no_accepted_alias_value")

    def test_sum_four_quarters_requires_four(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            pd.DataFrame({"q4": [4], "q3": [3], "q2": [2]}, index=["TotalRevenue"]).to_csv(path / "quarterly_income.csv")
            values, _ = Statements(path, self.aliases).values("revenue", "quarterly_income:sum4")
            self.assertEqual(values, [])

    def test_annual_quarterly_reconciliation_aligns_dates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            pd.DataFrame({"2025-12-31": [100]}, index=["TotalRevenue"]).to_csv(path / "annual_income.csv")
            pd.DataFrame({"2026-03-31": [999], "2025-12-31": [40], "2025-09-30": [30], "2025-06-30": [20], "2025-03-31": [10]}, index=["TotalRevenue"]).to_csv(path / "quarterly_income.csv")
            actual, expected, _ = Statements(path, self.aliases).aligned_annual_quarterly("revenue")
            self.assertEqual((actual, expected), (100.0, 100.0))

    def test_dated_quarterly_uses_explicit_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            pd.DataFrame({"2025-06-30": [3], "2025-03-31": [2]}, index=["NetIncome"]).to_csv(path / "quarterly_income.csv")
            series = Statements(path, self.aliases).dated_quarterly("net_income")
            self.assertEqual(series.tolist(), [2.0, 3.0])

    def test_invalid_denominator_is_missing(self) -> None:
        self.assertIsNone(safe_div(10, 0))
        self.assertIsNone(safe_div(10, -2))

    def test_growth_rejects_sign_change(self) -> None:
        self.assertIsNone(growth([10, -5]))
        self.assertAlmostEqual(growth([12, 10]), 0.2)

    def test_semantic_tolerance(self) -> None:
        self.assertTrue(semantic_row("x", "ABC", 99, 100, .02)["pass"])
        self.assertFalse(semantic_row("x", "ABC", 90, 100, .02)["pass"])

    def test_content_addressed_archive_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snap = root / "snapshot"
            snap.mkdir()
            (snap / "a.txt").write_text("same")
            (snap / "b.txt").write_text("same")
            result = archive(snap, root / "store", root / "manifest.json")
            self.assertEqual(result["file_count"], 2)
            self.assertEqual(sum(x["object_created"] for x in result["files"]), 1)


if __name__ == "__main__":
    unittest.main()
