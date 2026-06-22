"""Append-only contribution events for YF-FWD-SIMPLE-001."""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path


SCHEMA_VERSION = "YF-CONTRIBUTION-EVENT-1.0.0"


@dataclass(frozen=True)
class ContributionEvent:
    event_date: str
    amount: float
    currency: str
    event_id: str
    created_at_utc: str
    source_or_note: str
    manifest_link: str
    checksum: str = ""

    def payload(self) -> dict:
        row = asdict(self)
        row.pop("checksum")
        return {"schema_version": SCHEMA_VERSION, **row}

    def expected_checksum(self) -> str:
        encoded = json.dumps(self.payload(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def finalized(self) -> "ContributionEvent":
        validate_event(self, require_checksum=False)
        return ContributionEvent(**{**asdict(self), "checksum": self.expected_checksum()})


def validate_event(event: ContributionEvent, require_checksum: bool = True) -> None:
    date.fromisoformat(event.event_date)
    timestamp = datetime.fromisoformat(event.created_at_utc.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("created_at_utc must include a timezone")
    if event.currency != "USD":
        raise ValueError("Currency must be USD")
    if not event.event_id.strip() or not event.source_or_note.strip() or not event.manifest_link.strip():
        raise ValueError("Event ID, source/note and manifest linkage are required")
    if not math.isfinite(event.amount) or event.amount < 0:
        raise ValueError("Contribution amount must be finite and nonnegative")
    if require_checksum and event.checksum != event.expected_checksum():
        raise ValueError("Contribution checksum mismatch")


def read_events(path: Path) -> list[ContributionEvent]:
    if not path.exists():
        return []
    events = []
    seen = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        raw = json.loads(line)
        raw.pop("schema_version", None)
        event = ContributionEvent(**raw)
        validate_event(event)
        if event.event_id in seen:
            raise ValueError(f"Duplicate event ID at line {line_number}")
        seen.add(event.event_id)
        events.append(event)
    return events


def append_event(path: Path, event: ContributionEvent) -> ContributionEvent:
    """Validate and append one event without rewriting prior ledger bytes."""
    finalized = event.finalized()
    if finalized.event_id in {existing.event_id for existing in read_events(path)}:
        raise ValueError("Duplicate event ID")
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {**finalized.payload(), "checksum": finalized.checksum}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return finalized
