from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.data.audit_yfinance_capabilities import clean_json, sector_query, write_frame
from src.validation.analyze_yfinance_capability_audit import (
    ALL_FRAME_ENDPOINTS,
    conceptual_presence,
    factor_available,
)


class YFinancePhase1BTests(unittest.TestCase):
    def empty_frames(self) -> dict[str, pd.DataFrame]:
        return {endpoint: pd.DataFrame() for endpoint in ALL_FRAME_ENDPOINTS}

    def test_missing_is_not_zero(self) -> None:
        frames = self.empty_frames()
        frames["annual_income"] = pd.DataFrame(
            {pd.Timestamp("2025-12-31"): [0.0, float("nan")]},
            index=["NetIncome", "TotalRevenue"],
        )
        self.assertTrue(conceptual_presence(frames, "net_income"))
        self.assertFalse(conceptual_presence(frames, "revenue"))

    def test_factor_requires_every_input(self) -> None:
        frames = self.empty_frames()
        frames["annual_income"] = pd.DataFrame({"2025": [10.0]}, index=["NetIncome"])
        frames["annual_balance"] = pd.DataFrame({"2025": [100.0]}, index=["TotalAssets"])
        info = {"__ticker_dir": "/nonexistent"}
        self.assertTrue(factor_available(["net_income", "total_assets"], frames, info))
        frames["annual_balance"].loc["TotalAssets"] = float("nan")
        self.assertFalse(factor_available(["net_income", "total_assets"], frames, info))

    def test_json_cleaner_removes_nan(self) -> None:
        cleaned = clean_json({"x": float("nan"), "y": 1.0})
        self.assertEqual(cleaned, {"x": None, "y": 1.0})

    def test_frame_manifest_has_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frame.csv"
            result = write_frame(path, pd.DataFrame({"x": [1.0, math.nan]}))
            self.assertTrue(path.exists())
            self.assertEqual(result["rows"], 2)
            self.assertEqual(result["nonmissing_cells"], 1)
            self.assertEqual(len(result["sha256"]), 64)

    def test_sector_query_is_yfinance_equity_query(self) -> None:
        payload = sector_query("Technology").to_dict()
        text = str(payload)
        self.assertIn("Technology", text)
        self.assertIn("intradaymarketcap", text)
        self.assertIn("avgdailyvol3m", text)


if __name__ == "__main__":
    unittest.main()
