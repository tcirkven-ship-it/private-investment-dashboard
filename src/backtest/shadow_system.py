"""Four-model shadow system — ledgers, runner, reporting, activation."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest.price_walkforward import (
    cross_sectional_percentile, review_dates, write_json,
)
from src.backtest.mechanics_audit import fmt_pct, fmt_dec

EVIDENCE_LABEL = "Prospective price-gated Quality-veto shadow research."


def sha256(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


# ================================================================
# Part 2 — Frozen missing-Quality rules
# ================================================================

MISSING_QUALITY_RULES = {
    "computation": "annual statements with 3-month publication lag",
    "coverage_threshold": "bottom 10% excluded only among stocks with valid composite Quality",
    "missing_behavior": "stocks without valid composite Quality remain eligible (not excluded)",
    "missing_label": "DATA_COVERAGE_INSUFFICIENT — not excluded but flagged in report",
    "min_components": "at least 2 of 4 Quality factors must be non-missing for a valid composite",
    "veto_reporting": "report count vetoed, count missing, count valid",
}


# ================================================================
# Part 1 — Corrected Quality metrics table
# ================================================================

def quality_metrics_table() -> str:
    fl = pd.read_csv(ROOT / "data/prospective/daily_qvp/snapshots/2026-06-22T172514Z/analysis/factor_level_current.csv")
    fp = fl.pivot(index="ticker", columns="factor", values="percentile_rank")
    qf = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]
    q = fp[qf].mean(axis=1)
    p_a3 = fp[["M12_1", "M6_1"]].mean(axis=1)
    p_b2 = fp[["M12_1", "M6_1", "TREND200"]].mean(axis=1)

    lines = [
        "# Corrected Quality metrics — canonical table",
        "",
        "All values are cross-sectional percentiles (0-1) from the 2026-06-22 snapshot.",
        "",
        "| Metric | Eligible universe | A3 P100 | A3 G3 | B2 P100 | B2 G3 |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Composite Q median | {q.median():.4f} | {q[p_a3.sort_values(ascending=False).head(30).index].median():.4f} | {_g3_q(q, p_a3):.4f} | {q[p_b2.sort_values(ascending=False).head(30).index].median():.4f} | {_g3_q(q, p_b2):.4f} |",
    ]
    for f in qf:
        lines.append(
            f"| {f} median | {fp[f].median():.4f} | "
            f"{fp[f][p_a3.sort_values(ascending=False).head(30).index].median():.4f} | "
            f"{_g3_component(fp, q, p_a3, f):.4f} | "
            f"{fp[f][p_b2.sort_values(ascending=False).head(30).index].median():.4f} | "
            f"{_g3_component(fp, q, p_b2, f):.4f} |")
    return "\n".join(lines)


def _g3_q(q_ser: pd.Series, p_ser: pd.Series) -> float:
    bottom10 = q_ser.rank(pct=True) <= 0.1
    valid = ~bottom10
    g3_scores = p_ser.where(valid)
    top30 = g3_scores.sort_values(ascending=False).head(30).index
    return float(q_ser[top30].median())


def _g3_component(fp: pd.DataFrame, q_ser: pd.Series, p_ser: pd.Series, factor: str) -> float:
    bottom10 = q_ser.rank(pct=True) <= 0.1
    valid = ~bottom10
    g3_scores = p_ser.where(valid)
    top30 = g3_scores.sort_values(ascending=False).head(30).index
    return float(fp[factor][top30].median())


# ================================================================
# Part 3 — Immutable ledger
# ================================================================

@dataclass
class ShadowLedger:
    model_id: str
    activation_ts: str
    starting_cash: float = 0.0
    cash: float = 0.0
    holdings: dict[str, float] = field(default_factory=dict)
    buy_dates: dict[str, str] = field(default_factory=dict)
    transactions: list[dict] = field(default_factory=list)
    contributions: list[dict] = field(default_factory=list)
    nav_history: list[dict] = field(default_factory=list)
    config_hash: str = ""
    source_run_id: str = ""
    status: str = "CONFIGURED"

    def checksum(self) -> str:
        return sha256(self.__dict__)

    def to_dict(self) -> dict:
        return copy.deepcopy(self.__dict__)


def init_ledgers(config: dict) -> dict[str, ShadowLedger]:
    """Create four empty ledgers with starting capital."""
    cfg_hash = sha256(config)
    ledgers = {}
    for model in config["models"]:
        mid = model["id"]
        ledgers[mid] = ShadowLedger(
            model_id=mid,
            activation_ts=datetime.now(timezone.utc).isoformat(),
            starting_cash=100000.0,
            cash=100000.0,
            config_hash=cfg_hash,
            source_run_id="",
            status="INITIALIZED",
        )
    # Benchmark ledgers
    for bname in ["SPY", "QQQ"]:
        ledgers[bname] = ShadowLedger(
            model_id=bname,
            activation_ts=datetime.now(timezone.utc).isoformat(),
            starting_cash=100000.0,
            cash=100000.0,
            config_hash=cfg_hash,
            status="INITIALIZED",
        )
    return ledgers


def save_ledgers(ledgers: dict[str, ShadowLedger], output_dir: Path) -> None:
    for mid, ledger in ledgers.items():
        (output_dir / f"{mid}_ledger.json").write_text(
            json.dumps(ledger.to_dict(), indent=2, sort_keys=True, default=str) + "\n")


def load_ledgers(output_dir: Path, model_ids: list[str]) -> dict[str, ShadowLedger]:
    ledgers = {}
    for mid in model_ids:
        path = output_dir / f"{mid}_ledger.json"
        if path.exists():
            data = json.loads(path.read_text())
            ledgers[mid] = ShadowLedger(**data)
        else:
            ledgers[mid] = ShadowLedger(model_id=mid, status="CONFIGURED")
    return ledgers


# ================================================================
# Part 5+6 — Shadow runner and report generator
# ================================================================

def run_shadow_decision(
    ledgers: dict[str, ShadowLedger],
    config: dict,
    decision_date: str,
    snapshot_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Idempotent shadow runner for a single decision date."""
    # Check idempotency — has this date already been processed?
    for mid, ledger in ledgers.items():
        if "models" in config and mid in [m["id"] for m in config.get("models", [])]:
            for tx in ledger.transactions:
                if tx.get("decision_date") == decision_date:
                    return {"status": "SKIPPED", "reason": f"{decision_date} already processed for {mid}"}

    result = {"status": "PROCESSED", "models_processed": 0}

    # Load factor-level data for this snapshot
    factor_level = pd.read_csv(snapshot_path / "analysis" / "factor_level_current.csv")
    factor_pivot = factor_level.pivot(index="ticker", columns="factor", values="percentile_rank")

    for model in config.get("models", []):
        mid = model["id"]
        p_factors = ["M12_1", "M6_1"] if model.get("price_backbone") == "A3" else ["M12_1", "M6_1", "TREND200"]
        quality_veto = model.get("quality_veto", False)
        ledger = ledgers.get(mid)
        if ledger is None:
            continue

        p_score = factor_pivot[p_factors].mean(axis=1)

        if quality_veto:
            q_factors = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]
            q_score = factor_pivot[q_factors].mean(axis=1)
            # Missing-Quality: require at least 2 of 4 components
            q_components_ok = factor_pivot[q_factors].notna().sum(axis=1)
            valid_q = q_components_ok >= 2
            q_score_valid = q_score.where(valid_q)
            bottom10 = q_score_valid.rank(pct=True) <= 0.1
            # Missing Quality → stocks remain eligible (not excluded)
            excluded = bottom10 & q_score_valid.notna()
            p_score = p_score.where(~excluded)

        # Select top 30
        selected = p_score.sort_values(ascending=False).head(30)
        tickers_in = selected.index.tolist()

        # Record decision
        entry = {
            "decision_date": decision_date,
            "execution_date": "",  # next valid session — set externally
            "targets": tickers_in,
            "source_snapshot": str(snapshot_path),
            "config_hash": ledger.config_hash,
        }
        ledger.transactions.append(entry)
        result["models_processed"] += 1

    save_ledgers(ledgers, output_dir)
    return result


def generate_report(ledgers: dict[str, ShadowLedger], output_dir: Path) -> str:
    """Generate monthly comparison report."""
    lines = [
        "# Shadow portfolio — monthly comparison report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "| Model | Cash | Holdings | NAV | Return | SPY return | QQQ return | Active vs SPY | Active vs QQQ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mid in ["A3_P100", "A3_G3_QUALITY_VETO", "B2_P100", "B2_G3_QUALITY_VETO"]:
        lgr = ledgers.get(mid)
        if lgr is None:
            continue
        nav = lgr.cash + sum(lgr.holdings.values())
        spy_lev = ledgers.get("SPY")
        qqq_lev = ledgers.get("QQQ")
        spy_ret = spy_lev.cash / 100000.0 - 1 if spy_lev else 0
        qqq_ret = qqq_lev.cash / 100000.0 - 1 if qqq_lev else 0
        ret = nav / 100000.0 - 1
        lines.append(
            f"| {mid} | ${lgr.cash:.2f} | {len(lgr.holdings)} | ${nav:.2f} "
            f"| {fmt_pct(ret)} | {fmt_pct(spy_ret)} | {fmt_pct(qqq_ret)} "
            f"| {fmt_pct(ret - spy_ret)} | {fmt_pct(ret - qqq_ret)} |")

    lines += [
        "",
        "| Matched difference | Value |",
        "|---|---:|",
    ]
    a3p = ledgers.get("A3_P100")
    a3g = ledgers.get("A3_G3_QUALITY_VETO")
    b2p = ledgers.get("B2_P100")
    b2g = ledgers.get("B2_G3_QUALITY_VETO")
    if a3p and a3g:
        a3n = a3p.cash + sum(a3p.holdings.values())
        a3gn = a3g.cash + sum(a3g.holdings.values())
        lines.append(f"| A3 G3 − A3 P100 | {fmt_pct(a3gn - a3n)} |")
    if b2p and b2g:
        b2n = b2p.cash + sum(b2p.holdings.values())
        b2gn = b2g.cash + sum(b2g.holdings.values())
        lines.append(f"| B2 G3 − B2 P100 | {fmt_pct(b2gn - b2n)} |")

    return "\n".join(lines)


# ================================================================
# Main activation
# ================================================================

def activate(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Shadow configuration
    shadow_config = {
        "schema": "YF-SHADOW-PORTFOLIOS-2.0.0",
        "activated": "2026-06-23",
        "activation_status": "INITIALIZED",
        "decision_schedule": "monthly, last session of each month",
        "execution": "next_valid_session_close",
        "cost_bps": 10,
        "initial_capital_usd": 100000.0,
        "quality_veto_rules": MISSING_QUALITY_RULES,
        "models": [
            {"id": "A3_P100", "price_backbone": "A3", "quality_veto": False,
             "entry_condition": "top 30 by Price", "retention": 60},
            {"id": "A3_G3_QUALITY_VETO", "price_backbone": "A3", "quality_veto": True,
             "entry_condition": "top 30 by Price after Q veto", "retention": 60},
            {"id": "B2_P100", "price_backbone": "B2", "quality_veto": False,
             "entry_condition": "top 30 by Price", "retention": 60},
            {"id": "B2_G3_QUALITY_VETO", "price_backbone": "B2", "quality_veto": True,
             "entry_condition": "top 30 by Price after Q veto", "retention": 60},
        ],
        "benchmarks": ["SPY", "QQQ"],
        "reports": ["monthly_comparison"],
    }

    # Part 1 — Quality metrics reconciliation
    qc_lines = quality_metrics_table()
    (output_dir / "corrected_quality_metrics.md").write_text(qc_lines)
    (ROOT / "research/100_shadow_activation_audit.md").write_text(qc_lines)

    # Part 2 — Missing-Quality rules
    rules_lines = [
        "# Shadow operating protocol",
        "",
        "## Missing-Quality behavior",
        "",
        f"- Computation: {MISSING_QUALITY_RULES['computation']}",
        f"- Coverage: {MISSING_QUALITY_RULES['coverage_threshold']}",
        f"- Missing: {MISSING_QUALITY_RULES['missing_behavior']}",
        f"- Label: {MISSING_QUALITY_RULES['missing_label']}",
        f"- Min components: {MISSING_QUALITY_RULES['min_components']}",
        "",
        "## Activation status",
        "",
        "| Model | Status |",
        "|---|---|",
    ]
    for m in shadow_config["models"]:
        rules_lines.append(f"| {m['id']} | INITIALIZED |")
    rules_lines += [
        "| SPY | INITIALIZED |",
        "| QQQ | INITIALIZED |",
        "",
        "## First decision",
        "",
        "The first legitimate prospective decision requires a fresh integrity-passed",
        "scanner snapshot generated on or after the activation date (2026-06-23).",
        "The June 22, 2026 snapshot is NOT a valid prospective decision because",
        "it predates activation. Do not backfill.",
        "",
        "## Idempotency",
        "",
        "The shadow runner checks whether a given decision date has already been",
        "processed before applying any transactions. Rerunning the same date",
        "produces no duplicate events.",
    ]
    (output_dir / "research_101_protocol.md").write_text("\n".join(rules_lines))
    (ROOT / "research/101_shadow_operating_protocol.md").write_text("\n".join(rules_lines))

    # Part 3 — Initialize ledgers
    ledgers = init_ledgers(shadow_config)
    save_ledgers(ledgers, output_dir)

    # Part 7 — Activation manifest
    manifest = {
        "schema": "YF-SHADOW-ACTIVATION-1.0.0",
        "activation_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "INITIALIZED",
        "models": [m["id"] for m in shadow_config["models"]],
        "benchmarks": ["SPY", "QQQ"],
        "initial_capital": 100000.0,
        "decision_schedule": shadow_config["decision_schedule"],
        "config_hash": sha256(shadow_config),
        "prospective_start": None,
        "first_decision_date": None,
    }
    (output_dir / "activation_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n")
    (output_dir / "shadow_config.json").write_text(
        json.dumps(shadow_config, indent=2, sort_keys=True, default=str) + "\n")
    (ROOT / "outputs/final/shadow_activation_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n")

    # Generate initial empty report
    report = generate_report(ledgers, output_dir)
    (output_dir / "monthly_report.md").write_text(report)

    return {"status": "INITIALIZED", "models": len(shadow_config["models"]),
            "manifest_hash": sha256(manifest)}


def main() -> int:
    output = ROOT / "outputs/shadow"
    result = activate(output)
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
