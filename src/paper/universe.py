"""Versioned current-universe refresh state machine for prospective research."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class EligibilityState(str, Enum):
    ELIGIBLE = "eligible"
    GRACE = "ordinary_failure_grace_1_of_2"
    TEMPORARY_DATA_FAILURE = "temporary_data_failure"
    SUSPENDED_HARD_EVENT = "suspended_hard_event"
    PERMANENT_EXCLUSION = "permanent_exclusion"


@dataclass(frozen=True)
class SecurityState:
    ticker: str
    state: EligibilityState
    ordinary_failure_count: int = 0
    sector: str | None = None
    industry: str | None = None
    reason: str = ""
    new_orders_allowed: bool = False
    exit_required: bool = False


@dataclass(frozen=True)
class ReviewObservation:
    ticker: str
    eligible_now: bool
    screen_present: bool = True
    data_complete: bool = True
    ordinary_failure_reason: str | None = None
    hard_event_reason: str | None = None
    permanent_exclusion_reason: str | None = None
    sector: str | None = None
    industry: str | None = None


def transition(previous: SecurityState | None, observation: ReviewObservation) -> tuple[SecurityState, dict]:
    """Apply one monthly review; data failures do not consume eligibility grace."""
    old = previous.state.value if previous else "unseen"
    failures = previous.ordinary_failure_count if previous else 0
    if observation.hard_event_reason:
        current = SecurityState(observation.ticker, EligibilityState.SUSPENDED_HARD_EVENT, failures,
                                observation.sector, observation.industry, observation.hard_event_reason, False, False)
    elif observation.permanent_exclusion_reason:
        current = SecurityState(observation.ticker, EligibilityState.PERMANENT_EXCLUSION, failures,
                                observation.sector, observation.industry, observation.permanent_exclusion_reason, False, True)
    elif not observation.data_complete:
        current = SecurityState(observation.ticker, EligibilityState.TEMPORARY_DATA_FAILURE, failures,
                                observation.sector, observation.industry, "temporary_data_failure", False, False)
    elif observation.eligible_now:
        reason = "newly_eligible_next_monthly_selection" if previous is None else "eligibility_confirmed"
        if previous and (previous.sector != observation.sector or previous.industry != observation.industry):
            reason = "classification_change_verified_and_caps_recomputed"
        current = SecurityState(observation.ticker, EligibilityState.ELIGIBLE, 0, observation.sector,
                                observation.industry, reason, True, False)
    else:
        failures += 1
        reason = observation.ordinary_failure_reason or ("screen_disappearance" if not observation.screen_present else "ordinary_eligibility_failure")
        if failures >= 2:
            current = SecurityState(observation.ticker, EligibilityState.PERMANENT_EXCLUSION, failures,
                                    observation.sector, observation.industry, f"two_consecutive_reviews:{reason}", False, True)
        else:
            current = SecurityState(observation.ticker, EligibilityState.GRACE, failures,
                                    observation.sector, observation.industry, reason, False, False)
    audit = {"ticker": observation.ticker, "previous_state": old, "new_state": current.state.value,
             "reason": current.reason, "ordinary_failure_count": current.ordinary_failure_count,
             "new_orders_allowed": current.new_orders_allowed, "exit_required": current.exit_required,
             "observation": asdict(observation)}
    return current, audit


def resolve_duplicate_share_classes(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Retain highest market cap, then liquidity, then ticker for each normalized issuer."""
    ordered = sorted(rows, key=lambda x: (str(x["normalized_issuer_name"]), -float(x["market_cap"]),
                                          -float(x["median_dollar_volume"]), str(x["ticker"])))
    seen, retained, decisions = set(), [], []
    for row in ordered:
        issuer = row["normalized_issuer_name"]
        keep = issuer not in seen
        seen.add(issuer)
        if keep:
            retained.append(row)
        decisions.append({"ticker": row["ticker"], "normalized_issuer_name": issuer, "retained": keep,
                          "reason": "highest_market_cap_then_liquidity_then_ticker" if keep else "duplicate_issuer_share_class"})
    return retained, decisions
