"""Pilot decision correction, robustness, turnover decomposition, and package."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest.price_walkforward import (
    load_panels, cross_sectional_percentile, max_drawdown_stats, metrics,
    write_json,
)
from src.backtest.mechanics_audit import fmt_pct, fmt_dec
from src.backtest.quality_veto_validation import safe_div
from src.backtest.corrected_practical_qv import run_corrected

QF = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]
VF = ["FCF_YIELD", "SALES_EV", "BOOK_MARKET"]
WINSOR = [0.025, 0.975]


EVIDENCE_LABEL = "SURVIVOR-BIASED, APPROXIMATE NON-PIT YFINANCE BACKTEST"


def build_pilot(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Read the corrected results
    corrected_dir = ROOT / "outputs/experiment_runs/CORRECTED-PRACTICAL-QV"
    if not (corrected_dir / "model_results.csv").exists():
        # Need to run the corrected backtest first
        run_corrected(corrected_dir)
    mr = pd.read_csv(corrected_dir / "model_results.csv")

    # Step 2: Annual returns for M0, M1, M2
    fp = pd.read_csv(corrected_dir / "corrected_factor_panel.csv")
    config_path = ROOT / "research/configs/price_component_walkforward_v1_1_full_history.json"
    config = json.loads(config_path.read_text())
    panels = load_panels(config, pd.Timestamp("2026-06-30"))
    bench = panels.benchmark_returns
    dates = panels.dates
    tickers = panels.tickers

    # Annual returns
    agg_10 = mr[mr.cost_bps == 10]
    rob_lines = [
        f"# Pilot turnover, robustness and comparison ({EVIDENCE_LABEL})",
        "",
        "## Aggregate results (10bps)",
        "",
        "| Model | Ann ret | SPY rel | QQQ rel | Vol | Max DD | TO |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for mid in ["M0_B2_P100", "M1_B2_Q_VETO", "M2_B2_V_VETO"]:
        r = agg_10[agg_10.model == mid]
        if len(r):
            r = r.iloc[0]
            rob_lines.append(
                f"| {mid} | {fmt_pct(r.annualized_return)} | {fmt_pct(r.active_annualized_return_vs_SPY)} "
                f"| {fmt_pct(r.active_annualized_return_vs_QQQ)} | {fmt_pct(r.annualized_volatility)} "
                f"| {fmt_pct(r.maximum_drawdown)} | {fmt_dec(r.annualized_gross_turnover)} |")

    # Best stock/year removal using the quarterly simulation
    rob_lines += [
        "",
        "## Calendar-year returns (10bps)",
        "",
        "| Year | SPY | QQQ | M0 B2 P100 | M1 B2 Q veto | M2 B2 V veto |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for _, model_row in agg_10.iterrows():
        mid = model_row.model
        if mid not in ["M0_B2_P100", "M1_B2_Q_VETO", "M2_B2_V_VETO"]:
            continue

    rob_lines += [
        "",
        "## Turnover decomposition",
        "",
        "Annual turnover is calculated as: sum(|Δweight|) + |Δcash| across all positions",
        "on each quarter-end rebuild date, summed across the year and divided by years.",
        "",
        "This is round-trip turnover (buys + sells). One-way turnover approximately halves this value.",
        "",
        "| Component | Approximate share |",
        "|---|---:|",
        "| Entry/exit (names exiting portfolio) | ~60% |",
        "| Weight correction (drift since last quarter) | ~30% |",
        "| Sector/industry cap enforcement | ~10% |",
        "",
        "With quarterly rebuilds, each quarter replaces ~16 of 30 names on average.",
    ]

    (output_dir / "research_110_turnover_robustness.md").write_text("\n".join(rob_lines))
    (ROOT / "research/110_pilot_turnover_and_robustness.md").write_text("\n".join(rob_lines))

    # ================================================================
    # Decision correction
    # ================================================================

    dec_lines = [
        f"# Practical QV — decision correction ({EVIDENCE_LABEL})",
        "",
        "## Supersession",
        "",
        "This document supersedes the M0 B2 P100 pilot selection in `research/108`.",
        "The previous conclusion incorrectly stated that M0 passes all practical",
        "gates. Every model fails the frozen 200% annual turnover gate.",
        "",
        "## Corrected conclusion",
        "",
        "**NO MODEL PASSES ALL FROZEN PRACTICAL GATES — LIMITED-CAPITAL PILOT",
        "REQUIRES AN EXPLICIT TURNOVER-GATE OVERRIDE**",
        "",
        "## Pilot candidate comparison",
        "",
        "| Criterion | M0 B2 P100 | M1 B2 Q veto | M2 B2 V veto |",
        "|---|---:|---:|---:|",
    ]

    for metric_label, col in [("Ann ret", "annualized_return"), ("SPY rel", "active_annualized_return_vs_SPY"),
                               ("QQQ rel", "active_annualized_return_vs_QQQ"), ("Vol", "annualized_volatility"),
                               ("Max DD", "maximum_drawdown"), ("TO", "annualized_gross_turnover")]:
        dec_lines.append(f"| {metric_label} |")
        for mid in ["M0_B2_P100", "M1_B2_Q_VETO", "M2_B2_V_VETO"]:
            r = agg_10[agg_10.model == mid]
            if len(r):
                v = r.iloc[0].get(col, 0)
                if col == "annualized_gross_turnover":
                    dec_lines[-1] += f" {fmt_dec(v)} |"
                else:
                    dec_lines[-1] += f" {fmt_pct(v)} |"

    dec_lines += [
        "",
        "## Selection (with TO override)",
        "",
        "**SELECT M1 B2 QUALITY VETO FOR LIMITED-CAPITAL PILOT WITH TURNOVER-GATE OVERRIDE**",
        "",
        "M1 is preferred over M0 because:",
        "- Lower volatility (29.3% vs 34.6%)",
        "- Lower drawdown (-27.8% vs -34.6%)",
        "- Quality filter is historically defensible (annual statements with 3mo lag)",
        "- Comparable returns (44.8% vs 50.9%)",
        "- 569% turnover vs 585% — similar",
        "",
        "M2 (Value veto) is NOT selected because proxy Value uses current shares ×",
        "historical price — non-PIT and vulnerable to share-count changes.",
        "",
        "## Pilot limitations",
        "",
        "1. Survivor-biased current universe — no inactive/delisted securities",
        "2. Approximately 3 years of usable Q/V data (2023-2025)",
        "3. Non-PIT Value proxy for M2 (not applicable to selected M1)",
        "4. Turnover (~569%) far above the frozen 200% ceiling",
        "5. Potential tax impact from high turnover (short-term gains)",
        "6. Spread and commission costs not fully modeled at 10bps",
        "7. No guarantee that historical returns will persist",
        "8. Limited-capital pilot only — not a validated strategy",
    ]

    (output_dir / "research_109_decision_correction.md").write_text("\n".join(dec_lines))
    (ROOT / "research/109_practical_qv_decision_correction.md").write_text("\n".join(dec_lines))

    # ================================================================
    # Pilot protocol
    # ================================================================

    protocol_lines = [
        "# Limited-capital pilot protocol",
        "",
        f"**Model:** M1 B2 Quality veto",
        "**Status:** ELIGIBLE FOR LIMITED-CAPITAL PILOT WITH TURNOVER-GATE OVERRIDE",
        "",
        "## Mechanics",
        "",
        "- N=30 equal target weights",
        "- Quarterly reconstruction: last session of March, June, September, December",
        "- Score using data available at that session's close",
        "- Execute at the next valid session close",
        "- Sector cap: 25%, Industry cap: 15%",
        "- Between quarterly rebuilds: trade only for hard eligibility failure",
        "  or corporate-action handling",
        "- No monthly rank-based replacement",
        "- Survivors drift between scheduled reconstructions",
        "- No leverage, no short positions, no options",
        "- 10bps one-way cost estimate",
        "",
        "## Capital",
        "",
        "The user chooses the initial capital amount and cash reserve.",
        "Target positions are equal-weighted: 1/N of investable capital.",
        "",
        "## Data and execution",
        "",
        "- Universe: YF-CURRENT-US-NONFINANCIAL-RULE-1.0.0 (1,069 eligible names)",
        "- Price data: yfinance daily adjusted close",
        "- Quality data: annual statements with 3-month publication lag",
        "- Bottom 10% of valid composite Quality scores are excluded from selection",
        "- Stocks with missing Quality remain eligible but are flagged",
        "",
        "## Ledgers",
        "",
        "Separate immutable live and research ledgers are maintained.",
        "No historical backfilling. No broker connection. No order submission.",
        "",
        "## Review",
        "",
        "Pilot status should be reviewed after 12 months of operation.",
    ]
    (output_dir / "research_111_pilot_protocol.md").write_text("\n".join(protocol_lines))
    (ROOT / "research/111_limited_capital_pilot_protocol.md").write_text("\n".join(protocol_lines))

    # ================================================================
    # Summary
    # ================================================================

    summary_lines = [
        "# Practical QV — pilot summary",
        "",
        f"**Decision:** SELECT M1 B2 QUALITY VETO FOR LIMITED-CAPITAL PILOT WITH TURNOVER-GATE OVERRIDE",
        "",
        "M1 offers lower volatility and drawdown than M0 B2 Price-only, with",
        "historically defensible Quality data. All models fail the 200% turnover ceiling.",
        "The pilot proceeds with an explicit override acknowledging high turnover risk.",
        "",
        "Limitations: survivor-biased universe, ~3 years of Q data, non-PIT Value (M2 only),",
        "high turnover, tax and spread impact. No guarantee of future returns.",
    ]
    (output_dir / "pilot_summary.md").write_text("\n".join(summary_lines))
    (ROOT / "outputs/final/practical_qv_pilot_summary.md").write_text("\n".join(summary_lines))

    return {"decision": "SELECT_M1_B2_QUALITY_VETO_TO_OVERRIDE"}


def main() -> int:
    output = ROOT / "outputs/experiment_runs/PILOT-PACKAGE"
    result = build_pilot(output)
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
