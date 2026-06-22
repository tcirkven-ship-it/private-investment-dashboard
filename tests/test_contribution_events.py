import tempfile
import unittest
from pathlib import Path

from src.paper.contribution_events import ContributionEvent, append_event, read_events


def fixture(event_id="CONTRIB-001", amount=250.0):
    return ContributionEvent(
        event_date="2026-06-22",
        amount=amount,
        currency="USD",
        event_id=event_id,
        created_at_utc="2026-06-22T12:00:00Z",
        source_or_note="explicit user instruction",
        manifest_link="activation_manifest.json",
    )


class ContributionEventTests(unittest.TestCase):
    def test_append_and_checksum_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            written = append_event(path, fixture())
            self.assertEqual(read_events(path), [written])

    def test_zero_contribution_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            self.assertEqual(append_event(path, fixture(amount=0)).amount, 0)

    def test_duplicate_event_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            append_event(path, fixture())
            with self.assertRaises(ValueError):
                append_event(path, fixture())

    def test_non_usd_and_negative_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            with self.assertRaises(ValueError):
                append_event(path, fixture(amount=-1))
            bad = ContributionEvent(**{**fixture().__dict__, "currency": "EUR"})
            with self.assertRaises(ValueError):
                append_event(path, bad)


if __name__ == "__main__":
    unittest.main()
