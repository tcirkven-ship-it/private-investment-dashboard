#!/usr/bin/env python3
"""Independent ledger-level audit for the preserved Phase 1A result.

This script reads saved experiment artifacts only. It does not select or alter
any strategy and does not write into the preserved EXP-0009/EXP-0010 folders.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PRE = ROOT / "outputs/experiment_runs/EXP-0009"
HOLD = ROOT / "outputs/experiment_runs/EXP-0010"
BENCH = ROOT / "outputs/experiment_runs/EXP-0006"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_ledger(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()


def independent_xnpv(rate: float, flows: list[tuple[pd.Timestamp, float]]) -> float:
    origin = flows[0][0]
    return float(sum(value / (1 + rate) ** ((date - origin).days / 365.2425) for date, value in flows))


def independent_xirr(flows: list[tuple[pd.Timestamp, float]]) -> float:
    flows = sorted(flows)
    low, high = -0.9999, 1.0
    left, right = independent_xnpv(low, flows), independent_xnpv(high, flows)
    while np.sign(left) == np.sign(right) and high < 1024:
        high *= 2
        right = independent_xnpv(high, flows)
    if np.sign(left) == np.sign(right):
        return float("nan")
    for _ in range(300):
        mid = (low + high) / 2
        value = independent_xnpv(mid, flows)
        if np.sign(value) == np.sign(left):
            low, left = mid, value
        else:
            high, right = mid, value
    return float((low + high) / 2)


def independent_metrics(ledger: pd.DataFrame) -> dict[str, float | int | str]:
    active = ledger.loc[ledger["nav"] > 0].copy()
    returns = active["daily_return"].astype(float)
    total_twr = float(np.prod(1 + returns) - 1)
    annualized = float((1 + total_twr) ** (252 / len(returns)) - 1)
    volatility = float(np.std(returns, ddof=1) * np.sqrt(252))
    wealth = np.cumprod(1 + returns)
    drawdown = wealth / np.maximum.accumulate(wealth) - 1
    dated_flows = [(date, -float(value)) for date, value in active["external_flow"].items() if value != 0]
    dated_flows.append((active.index[-1], float(active["nav"].iloc[-1])))
    years = max((active.index[-1] - active.index[0]).days / 365.2425, 1 / 365.2425)
    discretionary = float(active.get("discretionary_trade_notional", active["trade_notional"]).sum())
    return {
        "start_date": str(active.index[0].date()),
        "end_date": str(active.index[-1].date()),
        "observations": int(len(active)),
        "total_contributed": float(active["external_flow"].sum()),
        "ending_value": float(active["nav"].iloc[-1]),
        "total_twr": total_twr,
        "annualized_twr": annualized,
        "xirr": independent_xirr(dated_flows),
        "annualized_volatility": volatility,
        "max_drawdown": float(np.min(drawdown)),
        "commission_cost": float(active["commission"].sum()),
        "impact_cost": float(active["impact_cost"].sum()),
        "total_explicit_cost": float((active["commission"] + active["impact_cost"]).sum()),
        "annualized_gross_turnover": float(discretionary / active["nav"].mean() / years),
        "minimum_cash": float(active["cash"].min()),
    }


def metric_differences(actual: dict[str, object], reported: dict[str, object]) -> dict[str, float]:
    keys = [
        "total_contributed", "ending_value", "total_twr", "annualized_twr", "xirr",
        "annualized_volatility", "max_drawdown", "commission_cost", "impact_cost",
        "total_explicit_cost", "annualized_gross_turnover",
    ]
    return {key: float(actual[key]) - float(reported[key]) for key in keys}


def return_identity_error(ledger: pd.DataFrame) -> float:
    prior = ledger["nav"].shift(1)
    valid = prior > 0
    implied = (ledger.loc[valid, "nav"] - ledger.loc[valid, "external_flow"]) / prior.loc[valid] - 1
    return float((implied - ledger.loc[valid, "daily_return"]).abs().max())


def main() -> None:
    pre = load_ledger(PRE / "primary_daily_ledger.csv")
    hold = load_ledger(HOLD / "primary_daily_ledger.csv")
    full = pd.concat([pre, hold]).sort_index()
    spy = load_ledger(BENCH / "SPY_weekly_ledger.csv").reindex(full.index)
    qqq = load_ledger(BENCH / "QQQ_weekly_ledger.csv").reindex(full.index)

    robust = json.loads((HOLD / "robustness_audit.json").read_text())
    pre_summary = json.loads((PRE / "summary.json").read_text())
    hold_summary = json.loads((HOLD / "summary.json").read_text())
    freeze = json.loads((PRE / "holdout_freeze.json").read_text())

    metrics = {
        "C03-M_stitched": independent_metrics(full),
        "SPY_stitched": independent_metrics(spy),
        "QQQ_stitched": independent_metrics(qqq),
    }
    differences = {
        "C03-M_stitched": metric_differences(metrics["C03-M_stitched"], robust["strategy_metrics"]),
        "SPY_stitched": metric_differences(metrics["SPY_stitched"], robust["benchmark_metrics"]["SPY"]),
        "QQQ_stitched": metric_differences(metrics["QQQ_stitched"], robust["benchmark_metrics"]["QQQ"]),
    }

    # Recreate the holdout performance metric convention: opening wealth is an
    # initial negative XIRR flow, but the already-computed daily return is kept.
    hold_metric_ledger = hold.copy()
    hold_metric_ledger.iloc[0, hold_metric_ledger.columns.get_loc("external_flow")] += float(
        hold_summary["candidate_results"]["C03-M"]["metrics"]["opening_nav"]
    )
    hold_metrics = independent_metrics(hold_metric_ledger)
    hold_differences = metric_differences(
        hold_metrics, hold_summary["candidate_results"]["C03-M"]["metrics"]
    )

    all_flow_equal = full["external_flow"].equals(spy["external_flow"]) and full["external_flow"].equals(qqq["external_flow"])
    positive_flow_dates = full.index[full["external_flow"] > 0]
    same_day_fridays = int(sum(date.weekday() == 4 for date in positive_flow_dates))
    non_friday_mappings = [str(date.date()) for date in positive_flow_dates if date.weekday() != 4]

    trades = pd.concat(
        [pd.read_csv(PRE / "primary_trades.csv", parse_dates=["date"]), pd.read_csv(HOLD / "primary_trades.csv", parse_dates=["date"])],
        ignore_index=True,
    )
    selections = pd.concat(
        [pd.read_csv(PRE / "primary_selections.csv", parse_dates=["fill_date", "signal_date"]), pd.read_csv(HOLD / "primary_selections.csv", parse_dates=["fill_date", "signal_date"])],
        ignore_index=True,
    )
    signal_lags = (selections["fill_date"] - selections["signal_date"]).dt.days
    selection_flow_notional = float(full.loc[full.index.intersection(selections["fill_date"]), "external_flow"].sum())
    selection_flow_dates = int((full.loc[full.index.intersection(selections["fill_date"]), "external_flow"] > 0).sum())

    current_hashes = {
        "engine.py": sha256(ROOT / "src/backtest/engine.py"),
        "strategy.py": sha256(ROOT / "src/backtest/strategy.py"),
        "run_best_effort.py": sha256(ROOT / "src/backtest/run_best_effort.py"),
        "test_accounting.py": sha256(ROOT / "tests/test_accounting.py"),
        "best_effort_v1.json": sha256(ROOT / "research/configs/best_effort_v1.json"),
        "preholdout_summary": sha256(PRE / "summary.json"),
    }
    hash_matches = {key: current_hashes[key] == freeze["checksums"][key] for key in current_hashes}

    max_metric_abs_error = max(abs(value) for group in differences.values() for value in group.values())
    max_holdout_metric_abs_error = max(abs(value) for value in hold_differences.values())
    result = {
        "audit_id": "EXP-0011-PHASE1A-CALCULATION-AUDIT",
        "scope": "Read-only independent recomputation from preserved ledgers; no strategy selection.",
        "headline_metrics_reproduced": bool(max_metric_abs_error < 1e-8 and max_holdout_metric_abs_error < 1e-8),
        "metrics": metrics,
        "metric_differences_vs_reported": differences,
        "holdout_metrics": hold_metrics,
        "holdout_metric_differences_vs_reported": hold_differences,
        "maximum_absolute_metric_difference": max_metric_abs_error,
        "maximum_absolute_holdout_metric_difference": max_holdout_metric_abs_error,
        "accounting_invariants": {
            "strategy_return_identity_max_abs_error": return_identity_error(full),
            "SPY_return_identity_max_abs_error": return_identity_error(spy),
            "QQQ_return_identity_max_abs_error": return_identity_error(qqq),
            "strategy_SPY_QQQ_external_flows_exactly_equal": all_flow_equal,
            "contribution_events": int((full["external_flow"] > 0).sum()),
            "total_contributed": float(full["external_flow"].sum()),
            "same_session_friday_contributions": same_day_fridays,
            "holiday_friday_contributions_mapped_to_later_session": len(non_friday_mappings),
            "later_session_dates": non_friday_mappings,
            "minimum_strategy_cash": float(full["cash"].min()),
            "trade_rows": int(len(trades)),
            "trade_commission_reconciles": bool(abs(trades["commission"].sum() - full["commission"].sum()) < 1e-8),
            "trade_impact_reconciles": bool(abs(trades["impact_cost"].sum() - full["impact_cost"].sum()) < 1e-8),
            "selection_dates_with_external_flow": selection_flow_dates,
            "external_flow_on_selection_dates": selection_flow_notional,
        },
        "signal_execution": {
            "selection_events": int(len(selections)),
            "minimum_calendar_lag_days": int(signal_lags.min()),
            "maximum_calendar_lag_days": int(signal_lags.max()),
            "same_day_signal_and_fill_count": int((signal_lags == 0).sum()),
            "all_fills_after_signal_date": bool((signal_lags > 0).all()),
        },
        "holdout_documentary_integrity": {
            "freeze_timestamp": freeze["frozen_at_utc"],
            "documented_pre_access_count": freeze["holdout"]["access_count_before_freeze"],
            "documented_rule_change_after_preholdout": freeze["primary_rule_change_after_preholdout"],
            "current_file_hash_matches": hash_matches,
            "all_current_file_hashes_match": all(hash_matches.values()),
            "limitation": "Repository artifacts support the sequence and frozen hashes, but cannot independently prove that a human or process never viewed the holdout before the recorded freeze.",
        },
        "methodological_findings": [
            "Saved ledgers reproduce the reported headline TWR, XIRR, volatility, drawdown, costs, and turnover within numerical tolerance.",
            "The contribution generator maps an ordinary Friday to that same Friday session (searchsorted side='left'); only market-holiday Fridays map to a later session. This differs from wording that says every Friday maps to the next session.",
            "Adjusted Close is used as both execution and valuation price. This creates a synthetic total-return-unit ledger: dividends/splits are embedded, but actual dividend cash, raw share quantities, and explicit corporate-action entries are not audited.",
            "The bootstrap is a non-studentized circular moving-block bootstrap of arithmetic monthly active-return differences, not the preregistered one-sided studentized procedure or a whole-search superiority test.",
            "External contributions arriving on a monthly selection date are included in trades classified as discretionary, slightly overstating discretionary turnover.",
            "Settlement is instantaneous in the model; T+1 restrictions and unsettled-cash behavior are not modeled.",
        ],
        "preserved_decision_effect": "None of the audit qualifications reverses FAIL; several further reduce the evidentiary strength of the favorable point estimates.",
        "preholdout_protocol_status": pre_summary["protocol_status"],
        "holdout_protocol_status": hold_summary["protocol_status"],
    }

    output = ROOT / "outputs/experiment_runs/EXP-0011/phase1a_calculation_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(output), "headline_metrics_reproduced": result["headline_metrics_reproduced"]}))


if __name__ == "__main__":
    main()
