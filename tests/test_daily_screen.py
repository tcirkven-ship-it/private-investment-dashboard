from datetime import datetime, timedelta, timezone
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.daily_screen import (build_changes, completed_session_cutoff,
                              contribution_allocation, latest_completed_session,
                              load_holdings, previous_ranking,
                              publication_run_id_valid, select_constrained,
                              validate_publication)
from src.validation.run_yfinance_checkpoint2 import through_session


class DailyScreenTests(unittest.TestCase):
    def config(self):
        return {"strategy": {"portfolio_size": 4, "sector_cap": .5, "industry_cap": .5}}

    def ranking(self):
        return pd.DataFrame([
            {"ticker": "A", "qvp_score": .9, "unconstrained_rank": 1, "sector": "Tech", "industry": "Software", "latest_close": 10},
            {"ticker": "B", "qvp_score": .8, "unconstrained_rank": 2, "sector": "Tech", "industry": "Software", "latest_close": 20},
            {"ticker": "C", "qvp_score": .7, "unconstrained_rank": 3, "sector": "Tech", "industry": "Hardware", "latest_close": 25},
            {"ticker": "D", "qvp_score": .6, "unconstrained_rank": 4, "sector": "Health", "industry": "Drugs", "latest_close": 30},
            {"ticker": "E", "qvp_score": .5, "unconstrained_rank": 5, "sector": "Energy", "industry": "Oil", "latest_close": 40},
        ])

    def test_before_close_uses_prior_calendar_date(self):
        now = datetime(2026, 6, 22, 15, 0, tzinfo=timezone.utc)  # 11:00 New York
        self.assertEqual(str(completed_session_cutoff(now).date()), "2026-06-21")

    def test_latest_completed_session_ignores_incomplete_current_date(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spy.csv"
            pd.DataFrame({"Close": [100, 101]}, index=["2026-06-18", "2026-06-22"]).to_csv(path)
            now = datetime(2026, 6, 22, 15, 0, tzinfo=timezone.utc)
            self.assertEqual(str(latest_completed_session(path, now).date()), "2026-06-18")

    def test_factor_input_frame_is_cut_at_completed_session(self):
        frame = pd.DataFrame({"Close": [100, 200]}, index=["2026-06-18", "2026-06-22"])
        result = through_session(frame, pd.Timestamp("2026-06-18"))
        self.assertEqual(result.Close.tolist(), [100])

    def test_constraint_replacement_is_deterministic(self):
        portfolio, excluded = select_constrained(self.ranking(), self.config())
        self.assertEqual(portfolio.ticker.tolist(), ["A", "B", "D", "E"])
        self.assertEqual(excluded.iloc[0].ticker, "C")
        self.assertEqual(portfolio.iloc[-1].selection_reason, "constraint_replacement")

    def test_contribution_does_not_change_portfolio_order(self):
        portfolio, _ = select_constrained(self.ranking(), self.config())
        holdings = pd.DataFrame(columns=["ticker", "shares"])
        small, _, _ = contribution_allocation(250, portfolio, holdings, 0, 3)
        large, _, _ = contribution_allocation(5000, portfolio, holdings, 0, 3)
        self.assertEqual(small.ticker.tolist(), large.ticker.tolist())
        self.assertAlmostEqual(small.allocation.sum(), 250)
        self.assertAlmostEqual(large.allocation.sum(), 5000)

    def test_zero_contribution_supported(self):
        portfolio, _ = select_constrained(self.ranking(), self.config())
        allocation, _, residual = contribution_allocation(0, portfolio, pd.DataFrame(columns=["ticker", "shares"]), 0, 3)
        self.assertEqual(float(allocation.allocation.sum()), 0)
        self.assertEqual(residual, 0)

    def test_negative_contribution_rejected(self):
        portfolio, _ = select_constrained(self.ranking(), self.config())
        with self.assertRaises(ValueError):
            contribution_allocation(-1, portfolio, pd.DataFrame(columns=["ticker", "shares"]), 0, 3)

    def test_first_run_does_not_reuse_old_research_list(self):
        current = self.ranking().rename(columns={"qvp_score": "qvp_score"})
        result, changes = build_changes(current, None)
        self.assertTrue(result.previous_rank.isna().all())
        self.assertIsNone(changes["previous_run"])

    def test_holdings_cash_row(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "holdings.csv"
            pd.DataFrame([{"ticker": "A", "shares": 2}, {"ticker": "CASH", "shares": 125}]).to_csv(path, index=False)
            frame, cash = load_holdings(path)
            self.assertEqual(frame.ticker.tolist(), ["A"])
            self.assertEqual(cash, 125)

    def publication_fixture(self, root: Path):
        snapshot, analysis = root / "snapshot", root / "analysis"
        snapshot.mkdir(); analysis.mkdir()
        invoked = datetime.now(timezone.utc)
        raw = {"started_at_utc": (invoked + timedelta(seconds=1)).isoformat()}
        (analysis / "analysis_manifest.json").write_text(json.dumps({"snapshot": str(snapshot)}))
        base = pd.DataFrame({"ticker": ["A", "B"]})
        ranking = pd.DataFrame({"ticker": ["A", "B"], "qvp_score": [.8, None],
                                "data_quality_flags": ["none", "missing_value"]})
        return invoked, raw, snapshot, analysis, base, ranking

    def test_rehearsal_run_id_cannot_publish(self):
        self.assertFalse(publication_run_id_valid("mechanics_smoke_2"))
        self.assertFalse(publication_run_id_valid("daily_rehearsal_1"))
        self.assertTrue(publication_run_id_valid("2026-06-22T120000Z"))

    def test_published_ranking_must_match_current_eligible_universe(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.publication_fixture(Path(directory))
            with self.assertRaisesRegex(RuntimeError, "exactly one row"):
                validate_publication("2026-06-22T120000Z", *args[:5], args[5].iloc[:1], True)

    def test_cached_analysis_snapshot_cannot_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            invoked, raw, snapshot, analysis, base, ranking = self.publication_fixture(Path(directory))
            (analysis / "analysis_manifest.json").write_text(json.dumps({"snapshot": "/tmp/old_checkpoint2"}))
            with self.assertRaisesRegex(RuntimeError, "current source snapshot"):
                validate_publication("2026-06-22T120000Z", invoked, raw, snapshot, analysis, base, ranking, True)

    def test_source_snapshot_cannot_predate_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            invoked, raw, snapshot, analysis, base, ranking = self.publication_fixture(Path(directory))
            raw["started_at_utc"] = (invoked - timedelta(seconds=1)).isoformat()
            with self.assertRaisesRegex(RuntimeError, "predates"):
                validate_publication("2026-06-22T120000Z", invoked, raw, snapshot, analysis, base, ranking, True)

    def test_previous_ranking_ignores_smoke_and_unmanifested_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            smoke = root / "mechanics_smoke_2"; smoke.mkdir()
            pd.DataFrame({"ticker": ["OLD"]}).to_csv(smoke / "ranking.csv", index=False)
            (smoke / "manifest.json").write_text(json.dumps({"classification": "current_decision_support_integrity_passed"}))
            partial = root / "2026-06-22T100000Z"; partial.mkdir()
            pd.DataFrame({"ticker": ["OLD2"]}).to_csv(partial / "ranking.csv", index=False)
            frame, run_id = previous_ranking(root, "2026-06-22T120000Z")
            self.assertIsNone(frame); self.assertIsNone(run_id)


if __name__ == "__main__":
    unittest.main()
