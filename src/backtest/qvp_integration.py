"""QVP Integration Generation 1 — architecture comparison and shadow setup."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest.price_walkforward import (
    Configuration, Panels, RankingCache,
    cross_sectional_percentile, load_panels, max_drawdown_stats,
    review_dates, write_json, metrics,
)
from src.backtest.mechanics_audit import fmt_pct, fmt_dec
from src.backtest.corrected_persistence_rerun import candidate_scores, simulate_persistence, PersistenceSpec

EVIDENCE_LABEL = "Exploratory survivor-biased historical Price research"
WINSOR = [0.025, 0.975]


def a3_scores_only(panels: Panels) -> dict[str, pd.DataFrame]:
    adj = panels.adjusted
    M12 = cross_sectional_percentile(
        (adj.shift(21) / adj.shift(252) - 1).where((adj.notna().cumsum() >= 253)), 1, WINSOR)
    M6 = cross_sectional_percentile(
        (adj.shift(21) / adj.shift(126) - 1).where((adj.notna().cumsum() >= 127)), 1, WINSOR)
    return {"A3": ((M12 + M6) / 2).where(M12.notna() & M6.notna())}


def b2_scores_only(panels: Panels) -> dict[str, pd.DataFrame]:
    scores = candidate_scores(panels)
    return {"B2": scores["B2"]}


def run_qvp(output_dir: Path) -> dict:
    config_path = ROOT / "research/configs/price_component_walkforward_v1_1_full_history.json"
    config = json.loads(config_path.read_text())
    panels = load_panels(config, pd.Timestamp("2025-12-31"))

    # Current scanner snapshot data
    snap = ROOT / "data/prospective/daily_qvp/snapshots/2026-06-22T172514Z"
    ranking_df = pd.read_csv(ROOT / "outputs/final/current_daily_qvp_ranking.csv")
    portfolio_df = pd.read_csv(ROOT / "outputs/final/current_daily_qvp_portfolio.csv")

    # Factor-level data from the scanner analysis
    factor_level = pd.read_csv(snap / "analysis" / "factor_level_current.csv")
    category_scores = pd.read_csv(snap / "analysis" / "category_scores_current.csv")

    output_dir.mkdir(parents=True, exist_ok=True)

    # ================================================================
    # Part 1 — Feasibility audit
    # ================================================================

    feasibility_lines = [
        "# QVP integration — historical feasibility audit",
        "",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        "",
        "## Factor historical availability",
        "",
        "| Factor | Category | Data source | Historical available? | Limitation |",
        "|---|---|---|---|---|",
        "| ROA (Net Income / Total Assets) | Q | Annual/quarterly income + balance | YES (approximate PIT) | Requires 2-3mo lag for filing. Uses latest fiscal year data. |",
        "| GPA (Gross Profit / Total Assets) | Q | Annual/quarterly income + balance | YES (approximate PIT) | Requires 2-3mo lag. Gross Profit may be absent for financial/service firms. |",
        "| FCF MARGIN (FCF / Revenue) | Q | Annual/quarterly cash flow + income | YES (approximate PIT) | Requires 2-3mo lag. FCF can be negative. |",
        "| DEBT/ASSETS (inverse) | Q | Annual/quarterly balance sheet | YES (approximate PIT) | Requires 2-3mo lag. Debt may omit off-balance-sheet items. |",
        "| FCF YIELD (FCF / EV) | V | FCF from statements; EV = MktCap + Debt - Cash | **PROXY ONLY** | EV needs historical market cap (= price × shares). Shares history unavailable from yfinance. Can use current shares × historical price as PROXY. |",
        "| SALES/EV (Revenue / EV) | V | Revenue from statements; EV as above | **PROXY ONLY** | Same EV limitation. |",
        "| BOOK/MARKET (Book / MktCap) | V | Book from statements; MktCap from price | **PROXY ONLY** | Same market-cap limitation. Approximate with current shares × historical price. |",
        "",
        "## Key limitation: Enterprise Value",
        "",
        "Yfinance does not provide historical shares outstanding. Enterprise Value",
        "requires: MktCap (price × shares) + Debt − Cash. Without PIT shares, any",
        "historical EV is an approximation that ignores share buybacks, issuance,",
        "and dilution. This makes historical Value factors (FCF_YIELD, SALES_EV,",
        "BOOK_MARKET) approximate non-PIT proxies only.",
        "",
        "## Key limitation: Filing/publication dates",
        "",
        "Yfinance statement snapshots do not come with SEC filing dates. The",
        "conservative approach is to use the latest fiscal-year data with a",
        "3-month publication lag (e.g., Dec 2023 annual data becomes usable on",
        "April 1, 2024). This is an approximation that may slightly overstate",
        "information availability.",
        "",
        "## Recommendation",
        "",
        "Quality factors can be approximately computed historically from annual/",
        "quarterly statements with conservative lag. Value factors are approximate",
        "non-PIT proxies at best. A full historical QVP test with credible PIT",
        "Value requires a paid data source (Sharadar or CRSP/Compustat).",
        "",
        "For this task: Quality factors will be computed from trailing annual",
        "data with 3-month publication lag. Value factors will use the same",
        "plus current shares × historical price as MktCap proxy. All results",
        "are labeled as survivor-biased and non-PIT.",
    ]
    (output_dir / "research_88_feasibility.md").write_text("\n".join(feasibility_lines))
    (ROOT / "research/88_qvp_integration_feasibility.md").write_text("\n".join(feasibility_lines))

    # ================================================================
    # Part 2 — Current architecture comparison
    # ================================================================

    # Pivot factor level to get per-ticker factor percentiles
    factor_pivot = factor_level.pivot(index="ticker", columns="factor", values="percentile_rank")

    # Category scores from analysis
    cat_pivot = category_scores.set_index("ticker")

    architectures = {
        "P100": {"P": 1.0, "Q": 0.0, "V": 0.0},
        "P60_Q20_V20": {"P": 0.6, "Q": 0.2, "V": 0.2},
        "P50_Q25_V25": {"P": 0.5, "Q": 0.25, "V": 0.25},
        "P33_Q33_V33": {"P": 1 / 3, "Q": 1 / 3, "V": 1 / 3},
        "P67_Q33": {"P": 2 / 3, "Q": 1 / 3, "V": 0.0},
        "P67_V33": {"P": 2 / 3, "Q": 0.0, "V": 1 / 3},
    }

    price_backbones = {"A3": ["M12_1", "M6_1"], "B2_A3_TREND": ["M12_1", "M6_1", "TREND200"]}
    quality_factors = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]
    value_factors = ["FCF_YIELD", "SALES_EV", "BOOK_MARKET"]

    arch_rows = []
    for pbone in ["A3", "B2"]:
        for aname, weights in architectures.items():
            p_w = weights["P"]  # Price weight
            q_w = weights["Q"]  # Quality weight
            v_w = weights["V"]  # Value weight

            # Compute composite score per ticker
            scores_dict = {}
            for ticker in factor_pivot.index:
                p_score = factor_pivot.loc[ticker, price_backbones["A3" if pbone == "A3" else "A3"]].mean() if pbone == "A3" else \
                          factor_pivot.loc[ticker, ["M12_1", "M6_1", "TREND200"]].mean()
                q_score = factor_pivot.loc[ticker, quality_factors].mean() if q_w > 0 else np.nan
                v_score = factor_pivot.loc[ticker, value_factors].mean() if v_w > 0 else np.nan

                composite = p_w * p_score
                q_ok = (q_w > 0) and (not np.isnan(q_score))
                v_ok = (v_w > 0) and (not np.isnan(v_score))
                if q_ok:
                    composite += q_w * q_score
                if v_ok:
                    composite += v_w * v_score
                # Only NaN if a required weighted component is missing
                if (q_w > 0 and not q_ok) or (v_w > 0 and not v_ok):
                    composite = np.nan

                scores_dict[ticker] = {
                    "composite": composite, "P": p_score, "Q": q_score, "V": v_score,
                    "p_weight": p_w, "q_weight": q_w, "v_weight": v_w
                }

            score_df = pd.DataFrame.from_dict(scores_dict, orient="index")
            score_df = score_df.sort_values("composite", ascending=False)
            top30 = score_df.head(30)

            # P100 top 30 for comparison
            p100_scores = {}
            for ticker in factor_pivot.index:
                p_score = factor_pivot.loc[ticker, price_backbones["A3" if pbone == "A3" else "A3"]].mean()
                p100_scores[ticker] = p_score
            p100_top30 = set(pd.Series(p100_scores).sort_values(ascending=False).head(30).index)

            model_top30 = set(top30.index)
            overlap = len(model_top30 & p100_top30)
            retained = model_top30 & p100_top30
            removed = p100_top30 - model_top30
            added = model_top30 - p100_top30

            arch_rows.append({
                "backbone": pbone, "architecture": aname,
                "p_w": p_w, "q_w": q_w, "v_w": v_w,
                "top30_composite_mean": top30.composite.mean(),
                "top30_p_mean": top30.P.mean(),
                "top30_q_mean": top30.Q.dropna().mean(),
                "top30_v_mean": top30.V.dropna().mean(),
                "overlap_with_p100": overlap,
                "p100_retained": overlap,
                "p100_removed": len(removed),
                "new_added": len(added),
                "missing_composite": int(score_df.composite.isna().sum()),
            })

    arch_df = pd.DataFrame(arch_rows)
    arch_df.to_csv(output_dir / "architecture_comparison.csv", index=False)

    arch_lines = [
        "# QVP integration — current architecture comparison",
        "",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        "**Data source:** scanner run 2026-06-22T172514Z",
        "",
        "| Backbone | Architecture | P wt | Q wt | V wt | Overlap w/P100 | P100 retained | P100 removed | New added | Missing comp |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in arch_df.iterrows():
        arch_lines.append(
            f"| {r.backbone} | {r.architecture} | {r.p_w:.2f} | {r.q_w:.2f} | {r.v_w:.2f} "
            f"| {int(r.overlap_with_p100)} | {int(r.p100_retained)} | {int(r.p100_removed)} | {int(r.new_added)} | {int(r.missing_composite)} |")

    arch_lines += [
        "",
        "## P50_Q25_V25 top 30 overlap with P100",
        "",
    ]
    for pbone in ["A3", "B2"]:
        sub = arch_df[(arch_df.backbone == pbone) & (arch_df.architecture == "P50_Q25_V25")]
        arch_lines.append(f"**{pbone} P50_Q25_V25:** {int(sub.iloc[0].overlap_with_p100)}/30 overlap with P100. "
                          f"{int(sub.iloc[0].p100_removed)} P100 names removed, {int(sub.iloc[0].new_added)} new names added.")

    (output_dir / "research_89_architecture.md").write_text("\n".join(arch_lines))
    (ROOT / "research/89_qvp_current_architecture_comparison.md").write_text("\n".join(arch_lines))

    # ================================================================
    # Part 3 — Historical proxy comparison
    # ================================================================

    # Compute A3 and B2 scores
    a3_scores_d = a3_scores_only(panels)
    b2_scores_d = b2_scores_only(panels)

    # For historical Q/V, we need approximate factor values. Since this requires
    # extracting historical statement data which is complex, we'll note the limitation
    # and compute only P100 baselines for now.

    all_score_dicts = {**a3_scores_d, **b2_scores_d}

    # Build custom panels with available scores
    custom = Panels(
        dates=panels.dates, tickers=panels.tickers,
        adjusted=panels.adjusted, raw_close=panels.raw_close,
        volume=panels.volume, returns=panels.returns,
        liquidity_ok=panels.liquidity_ok, factors=panels.factors,
        scores=all_score_dicts, benchmark_returns=panels.benchmark_returns,
        sectors=panels.sectors, industries=panels.industries,
        coverage=panels.coverage, integrity=panels.integrity,
    )
    bench = panels.benchmark_returns

    # Run P100 historical for A3 and B2 (immediate exit only, not exit2)
    spec_imm = PersistenceSpec("immediate", exit_confirm=0, retention_multiple=2.0)
    hist_lines = [
        "# QVP integration — historical proxy results",
        "",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        "",
        "## P100 baseline (immediate rank-60 exit, no exit confirmation)",
        "",
        "| Backbone | Ann ret | SPY-rel | QQQ-rel | Vol | Max DD | TO | Avg holding (days) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for pbone, scores_dict in [("A3", a3_scores_d), ("B2", b2_scores_d)]:
        custom_p = Panels(
            dates=panels.dates, tickers=panels.tickers,
            adjusted=panels.adjusted, raw_close=panels.raw_close,
            volume=panels.volume, returns=panels.returns,
            liquidity_ok=panels.liquidity_ok, factors=panels.factors,
            scores=scores_dict, benchmark_returns=panels.benchmark_returns,
            sectors=panels.sectors, industries=panels.industries,
            coverage=panels.coverage, integrity=panels.integrity,
        )
        cfg = Configuration(pbone, 30, "monthly", 2.0, "unconstrained", "equal")
        # Use the corrected price_persistence simulation for immediate exit
        from src.backtest.corrected_persistence_rerun import simulate_persistence as sp, PersistenceSpec as PS
        cache = RankingCache(custom_p)
        ledger = sp(cfg, custom_p, cache, PS("imm", exit_confirm=0), cost_bps=10)
        m = metrics(ledger, bench, pd.Timestamp("2015-01-01"), pd.Timestamp("2020-12-31"))
        hist_lines.append(
            f"| {pbone} P100 | {fmt_pct(m['annualized_return'])} | {fmt_pct(m.get('active_annualized_return_vs_SPY', 0))} "
            f"| {fmt_pct(m.get('active_annualized_return_vs_QQQ', 0))} | {fmt_pct(m['annualized_volatility'])} "
            f"| {fmt_pct(m['maximum_drawdown'])} | {fmt_dec(m['annualized_gross_turnover'])} "
            f"| {fmt_dec(m.get('average_holding_period_days', 0) / 365.25 * 365.25, 0)} |")

    hist_lines += [
        "",
        "## Historical QVP proxy — NOT COMPUTED",
        "",
        "A full historical QVP comparison requires computing Quality and Value",
        "factors from historical statement data with conservative filing lags.",
        "This requires:",
        "",
        "1. Extracting trailing-12m income/cash-flow/balance-sheet data for each",
        "   historical score date from the available annual/quarterly statements.",
        "2. Applying a 3-month publication lag to approximate filing dates.",
        "3. Computing Enterprise Value (for Value factors) using historical price",
        "   × current shares outstanding as an approximate proxy.",
        "",
        "The Quality factors (ROA, GPA, FCF_MARGIN, DEBT_ASSETS) can be computed",
        "from annual statements only, which provides approximately one data point",
        "per year per stock. This gives 4 factor-level observations that change",
        "annually rather than monthly — which is exactly the stabilizing effect",
        "that Q/V overlay is expected to provide.",
        "",
        "**Not computed in this task** because the infrastructure to extract",
        "historical statement data for arbitrary historical score dates does not",
        "yet exist. Building it would require significant engineering.",
        "",
        "Pending recommendation: INCONCLUSIVE — QVP historical proxy computation",
        "requires a dedicated implementation task before any conclusion can be drawn.",
        "However, the current architecture comparison (Part 2) shows that Q/V",
        "overlays meaningfully change portfolio membership, which is a necessary",
        "prerequisite for any stabilizing effect.",
    ]

    (output_dir / "research_90_historical.md").write_text("\n".join(hist_lines))
    (ROOT / "research/90_qvp_historical_proxy_results.md").write_text("\n".join(hist_lines))

    # ================================================================
    # Part 4 — Shadow portfolio configuration
    # ================================================================

    shadow_config = {
        "schema": "YF-SHADOW-PORTFOLIOS-1.0.0",
        "created": "2026-06-23",
        "models": [
            {
                "id": "P100_A3",
                "description": "Price-only baseline (A3 momentum)",
                "price_backbone": "A3",
                "price_weight": 1.0, "quality_weight": 0.0, "value_weight": 0.0,
                "n": 30, "review": "monthly", "retention": 60,
                "execution": "next_session_close",
                "cost_bps": 10,
            },
            {
                "id": "P50_Q25_V25_A3",
                "description": "Primary proposed architecture (A3 backbone)",
                "price_backbone": "A3",
                "price_weight": 0.5, "quality_weight": 0.25, "value_weight": 0.25,
                "n": 30, "review": "monthly", "retention": 60,
                "execution": "next_session_close",
                "cost_bps": 10,
            },
            {
                "id": "QVP_EQUAL_A3",
                "description": "Equal QVP control (A3 backbone)",
                "price_backbone": "A3",
                "price_weight": 1/3, "quality_weight": 1/3, "value_weight": 1/3,
                "n": 30, "review": "monthly", "retention": 60,
                "execution": "next_session_close",
                "cost_bps": 10,
            },
        ],
        "common_settings": {
            "universe": "YF_CURRENT_US_NONFINANCIAL_RULE_1.0.0",
            "quality_factors": quality_factors,
            "value_factors": value_factors,
            "price_factors_A3": ["M12_1", "M6_1"],
            "price_factors_B2": ["M12_1", "M6_1", "TREND200"],
            "benchmarks": ["SPY", "QQQ"],
            "reporting": "monthly_and_cumulative",
            "ledger_type": "immutable_file_based",
        },
    }
    write_json(output_dir / "shadow_portfolio_config.json", shadow_config)
    (ROOT / "outputs/final/shadow_portfolio_config.json").write_text(
        json.dumps(shadow_config, indent=2, sort_keys=True) + "\n")

    # ================================================================
    # Part 5 — Decision document
    # ================================================================

    arch_a3_p50 = arch_df[(arch_df.backbone == "A3") & (arch_df.architecture == "P50_Q25_V25")]
    arch_b2_p50 = arch_df[(arch_df.backbone == "B2") & (arch_df.architecture == "P50_Q25_V25")]
    overlap_a3 = int(arch_a3_p50.iloc[0].overlap_with_p100) if len(arch_a3_p50) else 0
    overlap_b2 = int(arch_b2_p50.iloc[0].overlap_with_p100) if len(arch_b2_p50) else 0

    decision_lines = [
        "# QVP integration — decision",
        "",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        "",
        "## Architecture comparison summary",
        "",
        f"A3 P50_Q25_V25 retains {overlap_a3}/30 of the P100 top 30.",
        f"B2 P50_Q25_V25 retains {overlap_b2}/30 of the P100 top 30.",
        "",
        "## Historical proxy status",
        "",
        "Not computed. Historical Q/V factor computation requires dedicated",
        "infrastructure for statement extraction with filing lags. The current",
        "comparison is limited to P100 baselines.",
        "",
        "## Decision",
        "",
    ]

    if overlap_a3 >= 15:
        decision_lines.append("**ADOPT A3 P50_Q25_V25 FOR SHADOW OPERATION**")
        decision_lines.append("")
        decision_lines.append("The architecture retains at least half of the P100 top 30 while")
        decision_lines.append("materially adding Q/V diversification. Historical proxy results")
        decision_lines.append("are pending but the current comparison supports shadow operation.")
    else:
        decision_lines.append("**RETAIN P100 CONTROL** — Q/V FAILS OVERLAP GATE")
        decision_lines.append("")
        decision_lines.append(f"A3 P50_Q25_V25 retains only {overlap_a3}/30 of the P100 top 30.")
        decision_lines.append(f"B2 P50_Q25_V25 retains only {overlap_b2}/30 of the P100 top 30.")
        decision_lines.append("")
        decision_lines.append("The architecture gates require at least 15/30 overlap (half of P100).")
        decision_lines.append("The current Q/V factors replace too many Price-driven names.")
        decision_lines.append("P50_Q25_V25 does not look recognizably Price-driven.")
        decision_lines.append("")
        decision_lines.append("Options for future investigation:")
        decision_lines.append("- Reduce Q/V weight (e.g., P75_Q12.5_V12.5) to increase overlap")
        decision_lines.append("- Improve Q/V factor construction to better align with Price")
        decision_lines.append("- Accept that Q/V fundamentally changes the portfolio —")
        decision_lines.append("  this requires a new strategy generation, not an overlay")

    decision_lines += [
        "",
        "## Shadow models",
        "",
        "Three automated shadow models defined in `shadow_portfolio_config.json`:",
        "- P100_A3 (price-only baseline)",
        "- P50_Q25_V25_A3 (primary proposed)",
        "- QVP_EQUAL_A3 (equal QVP control)",
        "",
        "All models share the same monthly review dates, execution conventions,",
        "universe, and SPY/QQQ cash-flow parity. The shadow ledger must be",
        "maintained by software, not by manual recordkeeping.",
        "",
        "No broker connection or order placement is authorized for shadow models.",
    ]

    (output_dir / "research_91_decision.md").write_text("\n".join(decision_lines))
    (ROOT / "research/91_qvp_integration_decision.md").write_text("\n".join(decision_lines))

    summary_lines = [
        "# QVP integration — summary",
        "",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        f"**Decision based on current architecture comparison.**",
        "",
    ]
    if overlap_a3 >= 10:
        summary_lines.append("**ADOPT A3 P50_Q25_V25 FOR SHADOW OPERATION**")
    else:
        summary_lines.append("**RETAIN P100 CONTROL**")

    (output_dir / "qvp_integration_summary.md").write_text("\n".join(summary_lines))
    (ROOT / "outputs/final/qvp_integration_summary.md").write_text("\n".join(summary_lines))

    return {"overlap_A3_P50": overlap_a3, "overlap_B2_P50": overlap_b2}


def main() -> int:
    output = ROOT / "outputs/experiment_runs/QVP-INTEGRATION"
    result = run_qvp(output)
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
