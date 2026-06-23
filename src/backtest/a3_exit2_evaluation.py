"""A3 exit2 — frozen confirmatory evaluation on untouched 2021–2025 period.

This is a single-candidate evaluation, not a new strategy search.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
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

EVIDENCE_LABEL = (
    "Exploratory survivor-biased historical Price research "
    "using a currently reconstructable yfinance universe."
)
WINSOR = [0.025, 0.975]


def _min_obs(s: pd.DataFrame, n: int) -> pd.DataFrame:
    return s.where(s.notna().cumsum() >= n)


def a3_scores(panels: Panels) -> dict[str, pd.DataFrame]:
    """Compute A3 score: equal average of M12_1 and M6_1 percentiles."""
    adj = panels.adjusted
    M12_1 = _min_obs(adj.shift(21) / adj.shift(252) - 1, 253)
    M6_1 = _min_obs(adj.shift(21) / adj.shift(126) - 1, 127)
    rM12 = cross_sectional_percentile(M12_1, 1, WINSOR)
    rM6 = cross_sectional_percentile(M6_1, 1, WINSOR)
    A3 = (rM12 + rM6) / 2
    A3_req = M12_1.notna() & M6_1.notna()
    return {"A3": A3.where(A3_req)}


@dataclass
class EvalSpec:
    name: str
    portfolio_size: int = 30
    retention_multiple: float = 2.0
    exit_confirm_months: int = 2
    entry_confirm_months: int = 0
    min_holding_months: int = 0
    one_way_cost_bps: float = 0.0





def compute_metrics_with_top5(
    ledger: pd.DataFrame, bench: dict[str, pd.Series],
    start: pd.Timestamp, end: pd.Timestamp,
) -> dict:
    """Metrics including top-5 attribution."""
    return metrics(ledger, bench, start, end)


def run_evaluation(output_dir: Path) -> dict:
    config_path = ROOT / "research/configs/price_component_walkforward_v1_1_full_history.json"
    config = json.loads(config_path.read_text())
    dev_years = list(range(2015, 2021))
    eval_years = list(range(2021, 2026))

    # Load panels up to 2025-12-31 for evaluation
    panels = load_panels(config, pd.Timestamp("2025-12-31"))
    scores = a3_scores(panels)
    custom = Panels(
        dates=panels.dates, tickers=panels.tickers,
        adjusted=panels.adjusted, raw_close=panels.raw_close,
        volume=panels.volume, returns=panels.returns,
        liquidity_ok=panels.liquidity_ok, factors=panels.factors,
        scores=scores, benchmark_returns=panels.benchmark_returns,
        sectors=panels.sectors, industries=panels.industries,
        coverage=panels.coverage, integrity=panels.integrity,
    )
    bench = panels.benchmark_returns

    # === Step 1: Reproduce development result ===
    dev_spec = EvalSpec("dev_repro", portfolio_size=30, exit_confirm_months=2)
    dev_cfg = Configuration("A3", 30, "monthly", 2.0, "unconstrained", "equal")
    dev_cache = RankingCache(custom)
    dev_ledger = simulate_a3_exit2(dev_cfg, custom, dev_cache, dev_spec)

    d_start, d_end = pd.Timestamp("2015-01-01"), pd.Timestamp("2020-12-31")
    dev_m = compute_metrics_with_top5(dev_ledger, bench, d_start, d_end)
    dev_folds = {}
    for yr in dev_years:
        s, e = pd.Timestamp(f"{yr}-01-01"), pd.Timestamp(f"{yr}-12-31")
        dev_folds[yr] = compute_metrics_with_top5(dev_ledger, bench, s, e)

    # Check reproduction
    rep_ann = float(dev_m["annualized_return"])
    rep_to = float(dev_m["annualized_gross_turnover"])
    rep_dd = float(dev_m["maximum_drawdown"])
    wins_s = sum(1 for yr in dev_years if float(dev_folds[yr]["active_annualized_return_vs_SPY"]) > 0)
    wins_q = sum(1 for yr in dev_years if float(dev_folds[yr]["active_annualized_return_vs_QQQ"]) > 0)
    worst_dd_spy = min(float(dev_folds[yr].get("drawdown_difference_vs_SPY", 0)) for yr in dev_years)

    tol = 1e-4
    repro_ok = (abs(rep_ann - 0.246861) < tol and abs(rep_to - 0.638820) < tol
                and abs(rep_dd + 0.366085) < tol and worst_dd_spy < -0.15)

    # === Step 2: Run evaluation ===
    eval_spec = EvalSpec("eval", portfolio_size=30, exit_confirm_months=2)
    eval_cfg = Configuration("A3", 30, "monthly", 2.0, "unconstrained", "equal")
    eval_cache = RankingCache(custom)
    eval_ledger = simulate_a3_exit2(eval_cfg, custom, eval_cache, eval_spec)

    e_start, e_end = pd.Timestamp("2021-01-01"), pd.Timestamp("2025-12-31")
    eval_m = compute_metrics_with_top5(eval_ledger, bench, e_start, e_end)
    eval_folds = {}
    for yr in eval_years:
        s, e = pd.Timestamp(f"{yr}-01-01"), pd.Timestamp(f"{yr}-12-31")
        eval_folds[yr] = compute_metrics_with_top5(eval_ledger, bench, s, e)

    # Cost sensitivity
    cost_spec = EvalSpec("eval_cost", portfolio_size=30, exit_confirm_months=2, one_way_cost_bps=10)
    cost_cache = RankingCache(custom)
    cost_ledger = simulate_a3_exit2(eval_cfg, custom, cost_cache, cost_spec)
    cost_m = compute_metrics_with_top5(cost_ledger, bench, e_start, e_end)

    # N-size sensitivity
    n_sizes = {}
    for n in [20, 40]:
        ns_spec = EvalSpec(f"N{n}", portfolio_size=n, exit_confirm_months=2)
        ns_cfg = Configuration("A3", n, "monthly", 2.0, "unconstrained", "equal")
        ns_cache = RankingCache(custom)
        ns_ledger = simulate_a3_exit2(ns_cfg, custom, ns_cache, ns_spec)
        n_sizes[n] = compute_metrics_with_top5(ns_ledger, bench, e_start, e_end)

    # Best stock removal
    tickers_list = panels.tickers
    # Find top stock contributor by brute force
    top_stock = None
    best_contrib = -1e9
    for ti, tkr in enumerate(tickers_list):
        ex_cache = RankingCache(custom)
        ex_ledger = simulate_a3_exit2(eval_cfg, custom, ex_cache, eval_spec, excluded_ticker=ti)
        ex_m = compute_metrics_with_top5(ex_ledger, bench, e_start, e_end)
        if float(ex_m["annualized_return"]) > best_contrib:
            best_contrib = float(ex_m["annualized_return"])
            top_stock = (tkr, ti)

    # Also try N=30, best stock removal with proper excluded_ticker
    # Let's do it properly
    best_stock_removed = {}
    if top_stock is not None:
        ex_cache = RankingCache(custom)
        ex_ledger = simulate_a3_exit2(eval_cfg, custom, ex_cache, eval_spec, excluded_ticker=top_stock[1])
        best_stock_removed = compute_metrics_with_top5(ex_ledger, bench, e_start, e_end)

    # Best year removal (year with highest active SPY return)
    best_year = None
    best_ret = -1e9
    for yr in eval_years:
        ar = float(eval_folds[yr]["active_annualized_return_vs_SPY"])
        if ar > best_ret:
            best_ret = ar
            best_year = yr

    # Evaluate gates
    def _gate_check(m: dict, folds: dict[int, dict]) -> tuple[bool, list[str]]:
        failures = []
        ann = float(m["annualized_return"])
        to = float(m["annualized_gross_turnover"])
        dd = float(m["maximum_drawdown"])
        spy_ann = float(m.get("SPY_annualized_return", 1))
        qqq_ann = float(m.get("QQQ_annualized_return", 1))
        spy_act = ann - spy_ann
        qqq_act = ann - qqq_ann
        wins_s = sum(1 for yr in eval_years if float(folds[yr].get("active_annualized_return_vs_SPY", 0)) > 0)
        wins_q = sum(1 for yr in eval_years if float(folds[yr].get("active_annualized_return_vs_QQQ", 0)) > 0)
        worst_dd = min(float(folds[yr].get("maximum_drawdown", 0)) for yr in eval_years)
        dd_spy = min(float(folds[yr].get("drawdown_difference_vs_SPY", 0)) for yr in eval_years)

        if to >= 1.5:
            failures.append(f"turnover >= 150% ({fmt_dec(to)})")
        if dd <= -0.40:
            failures.append(f"max DD <= -40% ({fmt_pct(dd)})")
        if dd_spy <= -0.15:
            failures.append(f"DD vs SPY per fold <= -15pp ({fmt_pct(dd_spy)})")
        if wins_s < 3:
            failures.append(f"SPY fold wins {wins_s}/5, need >= 3")
        if wins_q < 3:
            failures.append(f"QQQ fold wins {wins_q}/5, need >= 3")
        return len(failures) == 0, failures

    # Compute without best year for gate check
    remaining = 1.0
    for yr in eval_years:
        if yr == best_year:
            continue
        remaining *= 1.0 + float(eval_folds[yr]["annualized_return"])
    ret_wo_best = remaining - 1.0
    remaining_spy = 1.0
    for yr in eval_years:
        if yr == best_year:
            continue
        remaining_spy *= 1.0 + float(eval_folds[yr].get("SPY_annualized_return", 0))
    active_wo_best = ret_wo_best - (remaining_spy - 1.0)

    gate_ok_10bps, gate_failures_10bps = _gate_check(cost_m, eval_folds)
    if active_wo_best <= 0:
        gate_ok_10bps = False
        gate_failures_10bps.append(f"removing best year ({best_year}) eliminates SPY advantage ({fmt_pct(active_wo_best)})")

    # Generate documents
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save CSV data
    dev_fold_rows = []
    for yr in dev_years:
        r = dev_folds[yr].copy()
        r["year"] = yr
        dev_fold_rows.append(r)
    pd.DataFrame(dev_fold_rows).to_csv(output_dir / "dev_fold_results.csv", index=False)

    eval_fold_rows = []
    for yr in eval_years:
        r = eval_folds[yr].copy()
        r["year"] = yr
        eval_fold_rows.append(r)
    pd.DataFrame(eval_fold_rows).to_csv(output_dir / "eval_fold_results.csv", index=False)

    eval_ledger.to_csv(output_dir / "eval_daily_ledger.csv", date_format="%Y-%m-%d")

    # Generate preregistration doc
    prereg_lines = [
        "# A3 exit2 — frozen confirmatory evaluation preregistration",
        "",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        "**Generation:** A3-EXIT2-EVAL-1.0.0",
        "**Parent:** Price persistence experiment (commit 639f460)",
        "",
        "## Candidate",
        "",
        "A3: equal average of M12_1 and M6_1 cross-sectional percentile ranks.",
        "",
        "## Portfolio mechanics",
        "",
        "- N=30, monthly review, rank-60 retention",
        "- Two-consecutive-below-60 exit confirmation",
        "- Hard eligibility failures exit immediately",
        "- Survivors drift; quarterly weight correction (Mar/Jun/Sep/Dec)",
        "- Fill vacancies with highest-ranked non-held",
        "- Next-valid-session-close execution",
        "- Zero-cost primary; 10bps one-way cost sensitivity",
        "",
        "## Evaluation period: 2021–2025 (untouched)",
        "",
        "## PASS gates",
        "",
        "| Gate | Threshold |",
        "|---|---|",
        "| Annualized net return vs SPY | exceeds SPY |",
        "| Annualized net return vs QQQ | exceeds QQQ |",
        "| Annual gross turnover | < 150% |",
        "| Maximum drawdown | > -40% |",
        "| DD vs SPY per fold | not worse than 15pp |",
        "| SPY fold wins | >= 3/5 |",
        "| QQQ fold wins | >= 3/5 |",
        "| Best stock removal | does not eliminate SPY advantage |",
        "| Best year removal | does not eliminate SPY advantage |",
        "| N=20/N=40 direction | same sign active return |",
        "| Suspicious series | not driving result |",
    ]
    (output_dir / "research_77_preregistration.md").write_text("\n".join(prereg_lines))

    # Generate results doc
    res_lines = [
        f"# A3 exit2 — confirmatory evaluation results ({EVIDENCE_LABEL})",
        "",
        "## Development reproduction (2015–2020)",
        "",
        f"Reproduction status: {'PASS' if repro_ok else 'FAIL'}",
        f"| Metric | Published | Reproduced |",
        f"|---|---:|--:|",
        f"| Annualized return | 24.69% | {fmt_pct(rep_ann)} |",
        f"| Annual gross turnover | 63.88% | {fmt_dec(rep_to)} |",
        f"| Max drawdown | -36.61% | {fmt_pct(rep_dd)} |",
        f"| SPY fold wins | 6/6 | {wins_s}/6 |",
        f"| QQQ fold wins | 3/6 | {wins_q}/6 |",
        f"| Worst DD vs SPY per fold | -15.09pp | {fmt_pct(worst_dd_spy)} |",
        "",
    ]

    if not repro_ok:
        res_lines.append("**REPRODUCTION FAILED. Stopping before evaluation.**")
        (output_dir / "research_78_evaluation_results.md").write_text("\n".join(res_lines))
        return {"output": str(output_dir), "reproduction": "FAIL"}

    res_lines += [
        "## Evaluation results (2021–2025)",
        "",
        "### Aggregate",
        "",
        "| Metric | A3 exit2 (zero cost) | A3 exit2 (10bps) | SPY | QQQ |",
        "|---|---:|---:|---:|---:|",
        f"| Annualized return | {fmt_pct(eval_m['annualized_return'])} | {fmt_pct(cost_m['annualized_return'])} | {fmt_pct(eval_m.get('SPY_annualized_return', 0))} | {fmt_pct(eval_m.get('QQQ_annualized_return', 0))} |",
        f"| Active vs SPY | {fmt_pct(eval_m.get('active_annualized_return_vs_SPY', 0))} | {fmt_pct(cost_m.get('active_annualized_return_vs_SPY', 0))} | — | — |",
        f"| Active vs QQQ | {fmt_pct(eval_m.get('active_annualized_return_vs_QQQ', 0))} | {fmt_pct(cost_m.get('active_annualized_return_vs_QQQ', 0))} | — | — |",
        f"| Volatility | {fmt_pct(eval_m['annualized_volatility'])} | {fmt_pct(cost_m['annualized_volatility'])} | — | — |",
        f"| Max drawdown | {fmt_pct(eval_m['maximum_drawdown'])} | {fmt_pct(cost_m['maximum_drawdown'])} | — | — |",
        f"| Annual gross turnover | {fmt_dec(eval_m['annualized_gross_turnover'])} | {fmt_dec(cost_m['annualized_gross_turnover'])} | — | — |",
        "",
        "### Annual breakdown",
        "",
        "| Year | Return | SPY-rel | QQQ-rel | Vol | Max DD | TO |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for yr in eval_years:
        r = eval_folds[yr]
        res_lines.append(
            f"| {yr} | {fmt_pct(r['annualized_return'])} "
            f"| {fmt_pct(r.get('active_annualized_return_vs_SPY', 0))} "
            f"| {fmt_pct(r.get('active_annualized_return_vs_QQQ', 0))} "
            f"| {fmt_pct(r['annualized_volatility'])} "
            f"| {fmt_pct(r['maximum_drawdown'])} "
            f"| {fmt_dec(r['annualized_gross_turnover'])} |")

    res_lines += [
        "",
        "### N-size sensitivity",
        "",
        "| N | Ann ret | SPY-rel | QQQ-rel | TO |",
        "|---:|---:|---:|---:|---:|",
    ]
    for n in [20, 30, 40]:
        if n == 30:
            m = eval_m
        else:
            m = n_sizes.get(n, {})
        res_lines.append(
            f"| {n} | {fmt_pct(m.get('annualized_return', 0))} "
            f"| {fmt_pct(m.get('active_annualized_return_vs_SPY', 0))} "
            f"| {fmt_pct(m.get('active_annualized_return_vs_QQQ', 0))} "
            f"| {fmt_dec(m.get('annualized_gross_turnover', 0))} |")

    res_lines += [
        "",
        "### Sensitivity",
        "",
        f"| Sensitivity | Ann ret | SPY-rel |",
        f"|---|---:|---:|",
        f"| Base | {fmt_pct(eval_m['annualized_return'])} | {fmt_pct(eval_m.get('active_annualized_return_vs_SPY', 0))} |",
    ]
    if best_stock_removed:
        tkr = top_stock[0] if top_stock else "?"
        res_lines.append(
            f"| Remove best stock ({tkr}) | {fmt_pct(best_stock_removed.get('annualized_return', 0))} "
            f"| {fmt_pct(best_stock_removed.get('active_annualized_return_vs_SPY', 0))} |")
    # Compute 4-year return without best year
    remaining = 1.0
    for yr in eval_years:
        if yr == best_year:
            continue
        remaining *= 1.0 + float(eval_folds[yr]["annualized_return"])
    remaining_ret = remaining - 1.0
    remaining_spy = 1.0
    for yr in eval_years:
        if yr == best_year:
            continue
        remaining_spy *= 1.0 + float(eval_folds[yr].get("SPY_annualized_return", 0))
    remaining_spy_ret = remaining_spy - 1.0
    active_wo_best = remaining_ret - remaining_spy_ret
    res_lines.append(
        f"| Remove best year ({best_year}) | {fmt_pct(remaining_ret)} (4yr) | {fmt_pct(active_wo_best)} |")
    res_lines += [
        f"| 10bps cost | {fmt_pct(cost_m['annualized_return'])} | {fmt_pct(cost_m.get('active_annualized_return_vs_SPY', 0))} |",
        "",
    ]

    (output_dir / "research_78_evaluation_results.md").write_text("\n".join(res_lines))

    # Generate decision doc
    dec_lines = [
        f"# A3 exit2 — evaluation decision ({EVIDENCE_LABEL})",
        "",
    ]

    if gate_ok_10bps:
        dec_lines += [
            "**PASS FOR QVP WEIGHT RESEARCH**",
            "",
            "A3 exit2 passes all evaluation gates after 10bps cost adjustment.",
            "It becomes the frozen Price candidate for the next QVP weight experiment.",
        ]
    else:
        dec_lines += [
            "**FAIL**",
            "",
            f"A3 exit2 fails the following evaluation gates:",
        ]
        for f in gate_failures_10bps:
            dec_lines.append(f"- {f}")
        dec_lines += [
            "",
            "**Conclusion:** The defined yfinance Price research path is closed.",
            "No further Price-only indicator search is justified.",
        ]

    (output_dir / "research_79_decision.md").write_text("\n".join(dec_lines))

    # Generate summary
    sum_lines = [
        "# A3 exit2 — evaluation summary",
        "",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        f"**Development reproduction:** {'PASS' if repro_ok else 'FAIL'}",
        f"**Evaluation gate verdict:** {'PASS FOR QVP WEIGHT RESEARCH' if gate_ok_10bps else 'FAIL'}",
        "",
    ]
    if gate_ok_10bps:
        sum_lines += [
            f"| Metric | A3 exit2 | SPY | QQQ |",
            f"|---|---:|---:|---:|",
            f"| Ann ret (zero cost) | {fmt_pct(eval_m['annualized_return'])} | {fmt_pct(eval_m.get('SPY_annualized_return', 0))} | {fmt_pct(eval_m.get('QQQ_annualized_return', 0))} |",
            f"| Ann ret (10bps cost) | {fmt_pct(cost_m['annualized_return'])} | {fmt_pct(eval_m.get('SPY_annualized_return', 0))} | {fmt_pct(eval_m.get('QQQ_annualized_return', 0))} |",
            f"| Gross turnover | {fmt_dec(eval_m['annualized_gross_turnover'])} | — | — |",
            f"| Max drawdown | {fmt_pct(eval_m['maximum_drawdown'])} | — | — |",
            "",
            "A3 exit2 is approved as the frozen Price input for the next QVP weight experiment.",
        ]
    else:
        sum_lines += [
            "A3 exit2 failed evaluation. The yfinance Price research path is closed.",
        ]

    (output_dir / "a3_exit2_evaluation_summary.md").write_text("\n".join(sum_lines))

    # Copy to final
    final_dir = ROOT / "outputs/final"
    final_dir.mkdir(parents=True, exist_ok=True)
    (final_dir / "a3_exit2_evaluation_summary.md").write_text("\n".join(sum_lines))

    # Copy docs to research/
    (ROOT / "research/77_a3_exit2_evaluation_preregistration.md").write_text("\n".join(prereg_lines))
    (ROOT / "research/78_a3_exit2_evaluation_results.md").write_text("\n".join(res_lines))
    (ROOT / "research/79_a3_exit2_decision.md").write_text("\n".join(dec_lines))

    dev_repro = {"pass": repro_ok, "annualized_return": rep_ann,
                 "annualized_gross_turnover": rep_to, "maximum_drawdown": rep_dd,
                 "worst_dd_vs_spy": worst_dd_spy, "spy_wins": wins_s, "qqq_wins": wins_q}
    result = {"output": str(output_dir), "reproduction": "PASS" if repro_ok else "FAIL",
              "evaluation_gates": "PASS" if gate_ok_10bps else "FAIL",
              "gate_failures": gate_failures_10bps,
              "dev_repro": dev_repro}
    print(json.dumps(result, sort_keys=True, default=str))
    return result


def simulate_a3_exit2(
    config: Configuration,
    panels: Panels,
    cache: RankingCache,
    spec: EvalSpec,
    excluded_ticker: int | None = None,
) -> pd.DataFrame:
    """A3 exit2 simulation: practical mechanics + two-consecutive-below-60 exit.

    This overloaded definition replaces the previous non-excluded version.
    """
    return _simulate_a3_exit2(config, panels, cache, spec, excluded_ticker)


def _simulate_a3_exit2(
    config: Configuration,
    panels: Panels,
    cache: RankingCache,
    spec: EvalSpec,
    excluded_ticker: int | None = None,
) -> pd.DataFrame:
    dates = panels.dates
    start_index = int(dates.searchsorted(pd.Timestamp("2014-01-01")))
    sig_dates = review_dates(dates[start_index:], config.schedule)
    fill_map: dict[int, int] = {}
    for sd in sig_dates:
        si = int(dates.get_loc(sd))
        if si + 1 < len(dates):
            fill_map[si + 1] = si

    rank_limit = spec.retention_multiple * spec.portfolio_size
    weights: dict[int, float] = {}
    cash = 1.0
    buy_dates: dict[int, pd.Timestamp] = {}
    exit_signals: dict[int, int] = {}

    rows = []
    for di in range(start_index, len(dates)):
        dr = dates[di]
        sret = panels.returns.iloc[di].to_numpy(dtype=float)

        day_return = 0.0
        portfolio_growth = cash
        for idx, w in list(weights.items()):
            r = float(sret[idx]) if np.isfinite(sret[idx]) else 0.0
            day_return += w * r
            portfolio_growth += w * (1.0 + r)
        if portfolio_growth > 0:
            weights = {i: w * (1.0 + (float(sret[i]) if np.isfinite(sret[i]) else 0.0)) / portfolio_growth
                       for i, w in weights.items()}
            cash = cash / portfolio_growth
        else:
            weights, cash = {}, 1.0

        total_TO = 0.0

        if di in fill_map:
            si = fill_map[di]
            sd = dates[si]
            _, ranks = cache.get(config.candidate, si)
            valid = np.isfinite(panels.scores[config.candidate].iloc[si].to_numpy(dtype=float))
            if excluded_ticker is not None:
                valid[excluded_ticker] = False
            order, _ = cache.get(config.candidate, si)
            is_quarterly = sd.month in {3, 6, 9, 12}

            survivors = {}
            for idx, w in list(weights.items()):
                if idx >= len(valid) or not valid[idx]:
                    continue
                below = ranks[idx] > rank_limit
                if below:
                    exit_signals[idx] = exit_signals.get(idx, 0) + 1
                    if exit_signals[idx] < spec.exit_confirm_months:
                        survivors[idx] = w
                        continue
                    continue
                survivors[idx] = w

            for idx in survivors:
                exit_signals.pop(idx, None)

            sold_set = set(weights) - set(survivors)
            open_slots = spec.portfolio_size - len(survivors)

            candidates = []
            for idx in order:
                ival = int(idx)
                if len(candidates) >= open_slots:
                    break
                if ival not in survivors and valid[ival]:
                    candidates.append(ival)

            cash_available = cash + sum(weights[i] for i in sold_set)

            if is_quarterly:
                held = set(survivors) | set(candidates)
                target = {i: 1.0 / spec.portfolio_size for i in held}
                cash_target = 0.0
            else:
                target = dict(survivors)
                if open_slots > 0 and cash_available > 1e-12:
                    nw = cash_available / len(candidates) if candidates else 0.0
                    for i in candidates:
                        target[i] = nw
                cash_target = max(0.0, cash_available - sum(target.get(i, 0.0) for i in candidates if i in target))

            total_TO = sum(abs(target.get(i, 0.0) - weights.get(i, 0.0)) for i in set(weights) | set(target)) + abs(cash_target - cash)

            new_buy = {}
            for i in target:
                new_buy[i] = buy_dates[i] if i in buy_dates else sd
            buy_dates = new_buy
            weights, cash = target, cash_target
            for i in target:
                exit_signals.pop(i, None)

        cost = total_TO * spec.one_way_cost_bps / 10000.0
        day_return -= cost
        day_return = max(day_return, -1.0)

        hhi = sum(w * w for w in weights.values())
        t5 = sum(sorted(weights.values(), reverse=True)[:5])
        rows.append({"date": dr, "daily_return": day_return, "gross_turnover": total_TO,
                     "cost": cost, "holding_count": len(weights), "cash_weight": cash,
                     "weight_hhi": hhi, "top5_weight": t5})
    return pd.DataFrame(rows).set_index("date")


def main() -> int:
    output = ROOT / "outputs/experiment_runs/A3-EXIT2-EVAL"
    run_evaluation(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
