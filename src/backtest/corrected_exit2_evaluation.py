"""Corrected A3 exit2 evaluation — state-machine defect fixed.

The original exit2 implementation cleared the exit-confirmation counter
for ALL survivors, including stocks still below rank 60 whose counter
had not yet reached the confirmation threshold. This prevented any
rank-based exit from ever triggering.

This module uses the corrected logic and regenerates results.
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
    "Post-confirmatory exit-mechanics robustness research "
    "using a survivor-biased historical yfinance universe."
)
WINSOR = [0.025, 0.975]


def _min_obs(s: pd.DataFrame, n: int) -> pd.DataFrame:
    return s.where(s.notna().cumsum() >= n)


def a3_scores(panels: Panels) -> dict[str, pd.DataFrame]:
    adj = panels.adjusted
    M12_1 = _min_obs(adj.shift(21) / adj.shift(252) - 1, 253)
    M6_1 = _min_obs(adj.shift(21) / adj.shift(126) - 1, 127)
    rM12 = cross_sectional_percentile(M12_1, 1, WINSOR)
    rM6 = cross_sectional_percentile(M6_1, 1, WINSOR)
    return {"A3": ((rM12 + rM6) / 2).where(M12_1.notna() & M6_1.notna())}


def simulate_corrected(cfg: Configuration, panels: Panels, cache: RankingCache,
                       exit_confirm: int = 2, cost_bps: float = 0.0) -> pd.DataFrame:
    """Corrected exit2 simulation.

    Fix: exit_signals counter is ONLY cleared when a stock's rank recovers
    to <= 60, OR after the stock actually exits. It is NOT cleared for
    stocks still below 60 that haven't reached the confirmation threshold.
    """
    dates = panels.dates
    start_index = int(dates.searchsorted(pd.Timestamp("2014-01-01")))
    sig_dates = review_dates(dates[start_index:], cfg.schedule)
    fill_map: dict[int, int] = {}
    for sd in sig_dates:
        si = int(dates.get_loc(sd))
        if si + 1 < len(dates):
            fill_map[si + 1] = si

    rank_limit = cfg.retention_multiple * cfg.portfolio_size
    size = cfg.portfolio_size
    weights: dict[int, float] = {}
    cash = 1.0
    exit_signals: dict[int, int] = {}

    rows = []
    for di in range(start_index, len(dates)):
        dr = dates[di]
        sret = panels.returns.iloc[di].to_numpy(dtype=float)
        day_return = 0.0
        pg = cash
        for idx, w in list(weights.items()):
            r = float(sret[idx]) if np.isfinite(sret[idx]) else 0.0
            day_return += w * r
            pg += w * (1.0 + r)
        if pg > 0:
            weights = {i: w * (1.0 + (float(sret[i]) if np.isfinite(sret[i]) else 0.0)) / pg
                       for i, w in weights.items()}
            cash = cash / pg
        else:
            weights, cash = {}, 1.0

        total_TO = 0.0

        if di in fill_map:
            si = fill_map[di]
            sd = dates[si]
            _, ranks = cache.get(cfg.candidate, si)
            valid = np.isfinite(panels.scores[cfg.candidate].iloc[si].to_numpy(dtype=float))
            order, _ = cache.get(cfg.candidate, si)
            is_quarterly = sd.month in {3, 6, 9, 12}

            survivors = {}
            for idx, w in list(weights.items()):
                if idx >= len(valid) or not valid[idx]:
                    continue
                rk = int(ranks[idx])
                below = rk > rank_limit
                if below:
                    exit_signals[idx] = exit_signals.get(idx, 0) + 1
                    if exit_signals[idx] >= exit_confirm:
                        continue  # exit
                else:
                    exit_signals.pop(idx, None)  # clear only when recovered
                survivors[idx] = w

            # FIX: Only clear signals for stocks that have RECOVERED above 60
            # (already done above in the else branch).
            # Do NOT clear signals for ALL survivors.

            sold_set = set(weights) - set(survivors)
            open_slots = size - len(survivors)
            candidates = []
            for idx in order:
                ival = int(idx)
                if len(candidates) >= open_slots:
                    break
                if ival in survivors or not valid[ival]:
                    continue
                candidates.append(ival)

            cash_available = cash + sum(weights[i] for i in sold_set)
            if is_quarterly:
                held = set(survivors) | set(candidates)
                target = {i: 1.0 / size for i in held}
                cash_target = 0.0
            else:
                target = dict(survivors)
                if open_slots > 0 and cash_available > 1e-12:
                    nw = cash_available / len(candidates) if candidates else 0.0
                    for i in candidates:
                        target[i] = nw
                cash_target = max(0.0, cash_available - sum(target.get(i, 0.0) for i in candidates if i in target))

            total_TO = sum(abs(target.get(i, 0.0) - weights.get(i, 0.0)) for i in set(weights) | set(target)) + abs(cash_target - cash)

            weights, cash = target, cash_target
            # Clear signals for exited stocks (they're no longer in target)
            for i in list(exit_signals):
                if i not in target:
                    exit_signals.pop(i, None)

        cost = total_TO * cost_bps / 10000.0
        day_return -= cost
        day_return = max(day_return, -1.0)

        hhi = sum(w * w for w in weights.values())
        t5 = sum(sorted(weights.values(), reverse=True)[:5])
        rows.append({"date": dr, "daily_return": day_return, "gross_turnover": total_TO,
                     "cost": cost, "holding_count": len(weights), "cash_weight": cash,
                     "weight_hhi": hhi, "top5_weight": t5})
    return pd.DataFrame(rows).set_index("date")


def run_corrected(output_dir: Path) -> dict:
    config_path = ROOT / "research/configs/price_component_walkforward_v1_1_full_history.json"
    config = json.loads(config_path.read_text())
    panels = load_panels(config, pd.Timestamp("2025-12-31"))
    scores = a3_scores(panels)
    custom = Panels(
        dates=panels.dates, tickers=panels.tickers, adjusted=panels.adjusted,
        raw_close=panels.raw_close, volume=panels.volume, returns=panels.returns,
        liquidity_ok=panels.liquidity_ok, factors=panels.factors, scores=scores,
        benchmark_returns=panels.benchmark_returns, sectors=panels.sectors,
        industries=panels.industries, coverage=panels.coverage, integrity=panels.integrity,
    )
    bench = panels.benchmark_returns
    cfg = Configuration("A3", 30, "monthly", 2.0, "unconstrained", "equal")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Development (2015-2020)
    dev_cache = RankingCache(custom)
    dev_ledger = simulate_corrected(cfg, custom, dev_cache, exit_confirm=2, cost_bps=10)
    dev_start, dev_end = pd.Timestamp("2015-01-01"), pd.Timestamp("2020-12-31")
    dev_m = metrics(dev_ledger, bench, dev_start, dev_end)

    # Evaluation (2021-2025)
    eval_cache = RankingCache(custom)
    eval_ledger = simulate_corrected(cfg, custom, eval_cache, exit_confirm=2, cost_bps=10)
    eval_start, eval_end = pd.Timestamp("2021-01-01"), pd.Timestamp("2025-12-31")
    eval_m = metrics(eval_ledger, bench, eval_start, eval_end)

    # Annual folds
    eval_annual = {}
    for yr in range(2021, 2026):
        s, e = pd.Timestamp(f"{yr}-01-01"), pd.Timestamp(f"{yr}-12-31")
        eval_annual[yr] = metrics(eval_ledger, bench, s, e)

    # Save
    eval_ledger.to_csv(output_dir / "corrected_ledger.csv", date_format="%Y-%m-%d")

    # Build report
    lines = [
        "# Corrected A3 exit2 evaluation — state-machine defect fixed",
        "",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        "",
        "## Bug description",
        "",
        "The original exit2 implementation cleared the exit-confirmation counter",
        "for ALL survivors at each review, including stocks still below rank 60",
        "whose counter had not yet reached the confirmation threshold.",
        "",
        "Buggy code pattern (present in price_persistence.py, a3_sma150_exit.py,",
        "and a3_exit2_evaluation.py):",
        "",
        "```",
        "for idx in survivors:",
        "    exit_signals.pop(idx, None)  # clears counter for ALL survivors",
        "```",
        "",
        "This prevented any rank-based exit from ever triggering (V0 had 0 full",
        "exits across the entire 2021-2025 evaluation period despite 90.8% of",
        "held-stock-month observations having rank > 60).",
        "",
        "Fix: only clear the counter when the stock's rank recovers to <= 60",
        "(already handled by the `else: exit_signals.pop(idx, None)` branch",
        "in the main loop). Remove the blanket survivors loop.",
        "",
        "## Development reproduction (2015–2020, 10bps cost)",
        "",
        "| Metric | Original (buggy) | Corrected |",
        "|---|---:|---:|",
        f"| Annualized return | +24.69% | {fmt_pct(dev_m['annualized_return'])} |",
        f"| Annual gross turnover | 63.88% | {fmt_dec(dev_m['annualized_gross_turnover'])} |",
        f"| Max drawdown | -36.61% | {fmt_pct(dev_m['maximum_drawdown'])} |",
        "",
        "## Evaluation results (2021–2025, 10bps cost)",
        "",
        "| Metric | Original (buggy) | Corrected | SPY | QQQ |",
        "|---|---:|---:|---:|---:|",
        f"| Annualized return | +23.04% | {fmt_pct(eval_m['annualized_return'])} | {fmt_pct(eval_m.get('SPY_annualized_return', 0))} | {fmt_pct(eval_m.get('QQQ_annualized_return', 0))} |",
        f"| Annual gross turnover | 63.19% | {fmt_dec(eval_m['annualized_gross_turnover'])} | — | — |",
        f"| Max drawdown | -28.44% | {fmt_pct(eval_m['maximum_drawdown'])} | — | — |",
        "",
        "## Level 1 evaluation gates (10bps cost)",
        "",
    ]

    # Check gates
    ann_ret = float(eval_m["annualized_return"])
    to_val = float(eval_m["annualized_gross_turnover"])
    dd_val = float(eval_m["maximum_drawdown"])
    spy_ann = float(eval_m.get("SPY_annualized_return", 1))
    qqq_ann = float(eval_m.get("QQQ_annualized_return", 1))
    spy_act = ann_ret - spy_ann
    qqq_act = ann_ret - qqq_ann

    gates = {
        "Net return > SPY": spy_act > 0,
        "Net return > QQQ": qqq_act > 0,
        "TO < 150%": to_val < 1.5,
        "Max DD > -40%": dd_val > -0.40,
    }
    for gname, gpass in gates.items():
        lines.append(f"- {gname}: {'PASS' if gpass else 'FAIL'}")
    lines.append("")

    all_pass = all(gates.values())
    if all_pass:
        lines += [
            "**All level 1 gates pass.** However, because the development-period",
            "result has CHANGED from the original (the bug affected both development",
            "and evaluation), the previously frozen A3 exit2 cannot be automatically",
            "recertified. A full development-gate review is required before any",
            "QVP weight experiment.",
        ]
    else:
        lines.append("**One or more gates FAIL. A3 exit2 is no longer PASS.**")

    lines += [
        "",
        "## Recommendation",
        "",
        "1. **Fix the bug** in all affected simulator files (price_persistence.py,",
        "   a3_sma150_exit.py, a3_exit2_evaluation.py, sma150_instrumentation_audit.py,",
        "   state_machine_audit.py).",
        "2. **Rerun full development and evaluation** with the corrected code.",
        "3. **Reapply the development gates** from the persistence experiment.",
        "4. **Issue a fresh PASS/FAIL decision** based on the corrected results.",
        "5. **Do not preserve the previous PASS automatically.**",
    ]

    (output_dir / "corrected_evaluation.md").write_text("\n".join(lines))
    (ROOT / "research/84_a3_exit2_state_machine_audit.md").write_text("\n".join(lines))

    return {
        "original_ret": 0.2303846605979977,
        "corrected_ret": float(eval_m["annualized_return"]),
        "original_TO": 0.6319370217259823,
        "corrected_TO": float(eval_m["annualized_gross_turnover"]),
        "gates_pass": all_pass,
    }


def main() -> int:
    output = ROOT / "outputs/audit/corrected_exit2"
    result = run_corrected(output)
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
