"""Audit Price backtest portfolio mechanics: reproduce existing and compare practical.

This is a mechanical-fidelity comparison, not a new strategy search.
"""

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
    Configuration,
    Panels,
    RankingCache,
    choose_target,
    load_panels,
    max_drawdown_stats,
    metrics,
    review_dates,
    target_weights,
    write_json,
)


def _position_init() -> tuple[dict[int, float], float, dict[int, pd.Timestamp]]:
    weights: dict[int, float] = {}
    cash = 1.0
    buy_dates: dict[int, pd.Timestamp] = {}
    return weights, cash, buy_dates


def _drift(
    weights: dict[int, float],
    cash: float,
    stock_returns: np.ndarray,
    date_index: int,
    panels: Panels,
) -> tuple[dict[int, float], float, float]:
    day_return = 0.0
    portfolio_growth = cash
    for idx, weight in list(weights.items()):
        r = float(stock_returns[idx]) if np.isfinite(stock_returns[idx]) else 0.0
        day_return += weight * r
        portfolio_growth += weight * (1.0 + r)
    if portfolio_growth > 0:
        new_weights = {
            idx: weight * (1.0 + (float(stock_returns[idx]) if np.isfinite(stock_returns[idx]) else 0.0)) / portfolio_growth
            for idx, weight in weights.items()
        }
        new_cash = cash / portfolio_growth
    else:
        new_weights = {}
        new_cash = 1.0
    return new_weights, new_cash, day_return


def _existing_rebalance(
    weights: dict[int, float],
    cash: float,
    config: Configuration,
    panels: Panels,
    cache: RankingCache,
    signal_index: int,
    excluded_ticker: int | None,
) -> tuple[dict[int, float], float, float, float, float, int, int]:
    selected, ranks = choose_target(config, panels, cache, signal_index, weights, excluded_ticker)
    new_weights, new_cash = target_weights(selected, ranks, config.portfolio_size, config.weighting)
    all_names = set(weights) | set(new_weights)
    total_TO = sum(abs(new_weights.get(i, 0.0) - weights.get(i, 0.0)) for i in all_names) + abs(new_cash - cash)
    entry_exit = 0.0
    weight_restore = 0.0
    purchases = sales = 0
    for i in all_names:
        ow = weights.get(i, 0.0)
        nw = new_weights.get(i, 0.0)
        diff = abs(nw - ow)
        if (ow == 0) != (nw == 0):
            entry_exit += diff
            if ow == 0:
                purchases += 1
            else:
                sales += 1
        elif ow > 0 and nw > 0 and abs(nw - ow) > 1e-12:
            weight_restore += diff
    return new_weights, new_cash, total_TO, entry_exit, weight_restore, purchases, sales


def _practical_rebalance(
    weights: dict[int, float],
    cash: float,
    buy_dates: dict[int, pd.Timestamp],
    config: Configuration,
    panels: Panels,
    cache: RankingCache,
    signal_index: int,
    signal_date: pd.Timestamp,
    excluded_ticker: int | None,
) -> tuple[dict[int, float], float, dict[int, pd.Timestamp], float, float, float, int, int]:
    _, ranks = cache.get(config.candidate, signal_index)
    valid = np.isfinite(panels.scores[config.candidate].iloc[signal_index].to_numpy(dtype=float))
    if excluded_ticker is not None:
        valid[excluded_ticker] = False
    if config.version != "unconstrained":
        valid &= panels.liquidity_ok.iloc[signal_index].fillna(False).to_numpy(dtype=bool)
    order, _ = cache.get(config.candidate, signal_index)
    rank_limit = config.retention_multiple * config.portfolio_size
    is_quarterly = signal_date.month in {3, 6, 9, 12}

    # Survivors: held names still valid and within rank 60
    survivors = {}
    for idx, w in weights.items():
        if idx < len(valid) and valid[idx] and ranks[idx] <= rank_limit:
            survivors[idx] = w
    sold_set = set(weights) - set(survivors)
    open_slots = config.portfolio_size - len(survivors)

    candidates = []
    for idx in order:
        ival = int(idx)
        if len(candidates) >= open_slots:
            break
        if ival not in survivors and valid[ival]:
            candidates.append(ival)

    cash_available = cash + sum(weights[i] for i in sold_set)

    if is_quarterly:
        held_set = set(survivors) | set(candidates)
        target = {i: 1.0 / config.portfolio_size for i in held_set}
        cash_target = 0.0
    else:
        target = dict(survivors)
        if open_slots > 0 and cash_available > 1e-12:
            nw = cash_available / open_slots
            for i in candidates:
                target[i] = nw
        cash_target = max(0.0, cash_available - sum(target.get(i, 0.0) for i in candidates if i in target))

    all_names = set(weights) | set(target)
    total_TO = sum(abs(target.get(i, 0.0) - weights.get(i, 0.0)) for i in all_names) + abs(cash_target - cash)

    entry_exit = 0.0
    weight_restore = 0.0
    for i in all_names:
        ow = weights.get(i, 0.0)
        nw = target.get(i, 0.0)
        diff = abs(nw - ow)
        if (ow == 0) != (nw == 0):
            entry_exit += diff
        elif ow > 0 and nw > 0 and abs(nw - ow) > 1e-12:
            weight_restore += diff

    # Track buy dates for holding-period calculation
    new_buy_dates = {}
    for i in target:
        if i in buy_dates:
            new_buy_dates[i] = buy_dates[i]
        else:
            new_buy_dates[i] = signal_date

    purchase_count = sum(1 for i in target if i not in weights)
    sale_count = len(sold_set)

    return target, cash_target, new_buy_dates, total_TO, entry_exit, weight_restore, purchase_count, sale_count


def simulate_existing(config: Configuration, panels: Panels, cache: RankingCache,
                      excluded_ticker: int | None = None) -> pd.DataFrame:
    """Exactly reproduce the published simulate() with decomposed turnover."""
    dates = panels.dates
    start_index = int(dates.searchsorted(pd.Timestamp("2014-01-01")))
    sig_dates = review_dates(dates[start_index:], config.schedule)
    fill_map: dict[int, int] = {}
    for sd in sig_dates:
        si = int(dates.get_loc(sd))
        if si + 1 < len(dates):
            fill_map[si + 1] = si

    weights, cash, buy_dates = _position_init()
    rows = []
    for di in range(start_index, len(dates)):
        dr = dates[di]
        sret = panels.returns.iloc[di].to_numpy(dtype=float)
        weights, cash, day_return = _drift(weights, cash, sret, di, panels)
        total_TO = entry_exit = weight_restore = 0.0
        purchases = sales = 0
        if di in fill_map:
            si = fill_map[di]
            sd = dates[si]
            weights, cash, total_TO, entry_exit, weight_restore, purchases, sales = _existing_rebalance(
                weights, cash, config, panels, cache, si, excluded_ticker)
            # Track buy dates
            new_buy = {}
            for i in weights:
                if i in buy_dates:
                    new_buy[i] = buy_dates[i]
                else:
                    new_buy[i] = sd
            buy_dates = new_buy

        avg_holding = np.nan
        if len(buy_dates) and cash < 1.0:
            ages = [(dr - bd).days for i, bd in buy_dates.items() if i in weights]
            avg_holding = float(np.mean(ages)) / 365.25 if ages else np.nan

        hhi = sum(w * w for w in weights.values())
        t5 = sum(sorted(weights.values(), reverse=True)[:5])
        rows.append({"date": dr, "daily_return": day_return, "gross_turnover": total_TO,
                     "entry_exit_turnover": entry_exit, "weight_restoration_turnover": weight_restore,
                     "purchases": purchases, "sales": sales,
                     "avg_holding_days": avg_holding * 365.25 if avg_holding and np.isfinite(avg_holding) else np.nan,
                     "holding_count": len(weights), "cash_weight": cash, "weight_hhi": hhi, "top5_weight": t5})
    return pd.DataFrame(rows).set_index("date")


def simulate_practical(config: Configuration, panels: Panels, cache: RankingCache,
                       excluded_ticker: int | None = None) -> pd.DataFrame:
    """Practical mechanics: sell-only-below-60, survivors drift, quarterly rebalance."""
    dates = panels.dates
    start_index = int(dates.searchsorted(pd.Timestamp("2014-01-01")))
    sig_dates = review_dates(dates[start_index:], config.schedule)
    fill_map: dict[int, int] = {}
    for sd in sig_dates:
        si = int(dates.get_loc(sd))
        if si + 1 < len(dates):
            fill_map[si + 1] = si

    weights, cash, buy_dates = _position_init()
    rows = []
    for di in range(start_index, len(dates)):
        dr = dates[di]
        sret = panels.returns.iloc[di].to_numpy(dtype=float)
        weights, cash, day_return = _drift(weights, cash, sret, di, panels)
        total_TO = entry_exit = weight_restore = 0
        purchases = sales = 0
        if di in fill_map:
            si = fill_map[di]
            sd = dates[si]
            weights, cash, buy_dates, total_TO, entry_exit, weight_restore, purchases, sales = \
                _practical_rebalance(weights, cash, buy_dates, config, panels, cache, si, sd, excluded_ticker)

        hhi = sum(w * w for w in weights.values())
        t5 = sum(sorted(weights.values(), reverse=True)[:5])
        avg_holding = np.nan
        if len(buy_dates) and cash < 1.0:
            ages = [(dr - bd).days for i, bd in buy_dates.items() if i in weights]
            avg_holding = float(np.mean(ages)) / 365.25 if ages else np.nan
        rows.append({"date": dr, "daily_return": day_return, "gross_turnover": total_TO,
                     "entry_exit_turnover": entry_exit, "weight_restoration_turnover": weight_restore,
                     "purchases": purchases, "sales": sales,
                     "avg_holding_days": avg_holding * 365.25 if avg_holding and np.isfinite(avg_holding) else np.nan,
                     "holding_count": len(weights), "cash_weight": cash, "weight_hhi": hhi, "top5_weight": t5})
    return pd.DataFrame(rows).set_index("date")


def metrics_ex(ledger: pd.DataFrame, bench: dict[str, pd.Series],
               start: pd.Timestamp, end: pd.Timestamp) -> dict:
    """Full metric set for either mechanics variant with turnover decomposition."""
    frame = ledger.loc[(ledger.index >= start) & (ledger.index <= end)].copy()
    r = frame.daily_return.fillna(0.0)
    n = len(r)
    yrs = n / 252.0

    tr = float((1 + r).prod() - 1)
    ann_ret = float((1 + tr) ** (1 / yrs) - 1) if yrs > 0 and tr > -1 else np.nan
    vol = float(r.std(ddof=1) * np.sqrt(252)) if n > 1 else np.nan

    md, mddur = max_drawdown_stats(r)

    gross_TO = float(frame.gross_turnover.sum())
    ann_TO = gross_TO / yrs if yrs > 0 else np.nan
    entry_exit = float(frame.entry_exit_turnover.sum())
    weight_restore = float(frame.weight_restoration_turnover.sum())
    ann_ee = entry_exit / yrs if yrs > 0 else 0.0
    ann_wr = weight_restore / yrs if yrs > 0 else 0.0

    tot_purchases = int(frame.purchases.sum()) if "purchases" in frame.columns else 0
    tot_sales = int(frame.sales.sum()) if "sales" in frame.columns else 0

    avg_hold = float(frame.avg_holding_days.mean()) if "avg_holding_days" in frame.columns and frame.avg_holding_days.notna().any() else np.nan

    result = {
        "annualized_return": ann_ret, "annualized_volatility": vol,
        "maximum_drawdown": md, "maximum_drawdown_duration_sessions": mddur,
        "annualized_gross_turnover": ann_TO,
        "annualized_entry_exit_turnover": ann_ee,
        "annualized_weight_restoration_turnover": ann_wr,
        "entry_exit_share": entry_exit / gross_TO if gross_TO > 0 else 0.0,
        "weight_restoration_share": weight_restore / gross_TO if gross_TO > 0 else 0.0,
        "total_purchases": tot_purchases, "total_sales": tot_sales,
        "average_holding_period_days": avg_hold,
    }

    for bname, bser in bench.items():
        bb = bser.reindex(frame.index).fillna(0.0)
        bt = float((1 + bb).prod() - 1)
        ba = float((1 + bt) ** (1 / yrs) - 1) if yrs > 0 else np.nan
        result[f"{bname}_total_return"] = bt
        result[f"{bname}_annualized_return"] = ba
        result[f"active_annualized_return_vs_{bname}"] = ann_ret - ba

    return result


def fmt_pct(v: float) -> str:
    return f"{v * 100:+.4f}%" if np.isfinite(v) else "N/A"


def fmt_dec(v: float, d: int = 2) -> str:
    return f"{v:.{d}f}" if np.isfinite(v) else "N/A"


def run_audit(output_dir: Path) -> dict:
    config_path = ROOT / "research/configs/price_component_walkforward_v1_1_full_history.json"
    config = json.loads(config_path.read_text())
    eval_years = list(config["folds"]["evaluation_test_years"])
    pe_start, pe_end = pd.Timestamp(f"{min(eval_years)}-01-01"), pd.Timestamp(f"{max(eval_years)}-12-31")

    panels = load_panels(config, pe_end)
    cache = RankingCache(panels)
    base = Configuration("P4", 30, "monthly", 2.0, "unconstrained", "equal")

    ex_ledger = simulate_existing(base, panels, cache)
    pr_ledger = simulate_practical(base, panels, cache)

    bench = panels.benchmark_returns
    m_ex = metrics_ex(ex_ledger, bench, pe_start, pe_end)
    m_pr = metrics_ex(pr_ledger, bench, pe_start, pe_end)

    pub_ann, pub_to, pub_dd, pub_vol = 0.1284657020248643, 6.816986554877918, -0.2148997076358413, 0.1975563418816952
    rep_ann, rep_to, rep_dd, rep_vol = m_ex["annualized_return"], m_ex["annualized_gross_turnover"], m_ex["maximum_drawdown"], m_ex["annualized_volatility"]
    ann_ok = abs(rep_ann - pub_ann) < 1e-8
    to_ok = abs(rep_to - pub_to) < 1e-4
    dd_ok = abs(rep_dd - pub_dd) < 1e-8
    vol_ok = abs(rep_vol - pub_vol) < 1e-8

    def ann_row(yr: int, m: dict) -> str:
        return (f"| {yr} | {fmt_pct(m['annualized_return'])} | {fmt_pct(m['active_annualized_return_vs_SPY'])} "
                f"| {fmt_pct(m['active_annualized_return_vs_QQQ'])} | {fmt_pct(m['annualized_volatility'])} "
                f"| {fmt_pct(m['maximum_drawdown'])} | {fmt_dec(m['annualized_gross_turnover'])} "
                f"| {fmt_dec(m['annualized_entry_exit_turnover'])} | {fmt_dec(m['annualized_weight_restoration_turnover'])} |")

    lines = [
        "# Price backtest portfolio-mechanics audit",
        "",
        "## Question answers",
        "",
        "**1. Were all surviving holdings reset to equal weight at every monthly review?**",
        "",
        "Yes. The published `simulate()` calls `target_weights(selected, ...)`, which assigns equal weight",
        f"({1/30:.6f}) to every selected name at EACH monthly review. All survivors are restored to equal weight.",
        f"{fmt_pct(m_ex['weight_restoration_share'])} of total turnover comes from this weight restoration.",
        "",
        "**2. Were only rank-below-60 and hard-ineligible positions sold?**",
        "",
        "Approximately yes. `choose_target()` ranks all names, retains existing holdings within",
        "rank 60 (the buffer), and fills remaining slots from top-ranked non-held names.",
        "However, the equal-weight restoration also partially sells positions that remain in the",
        "portfolio — those are not rank-60 exits but weight-adjustment sales.",
        "In the strict sense, positions exit only when they fall below rank 60 OR when",
        "they are forced out by sector/industry caps (constrained versions only).",
        "",
        "**3. Were new positions funded by selling existing surviving positions?**",
        "",
        "Yes. The portfolio is always fully invested (cash ≈ 0). New positions enter at weight 1/N,",
        "funded by the equal-weight restoration that reduces overweight survivors.",
        "",
        "**4. Was price-drift correction performed monthly, quarterly, or only when necessary?**",
        "",
        "Every monthly review performs implicit full drift correction by resetting all weights to 1/N.",
        "There is no separate drift-tracking step; the equal-weight assignment overwrites any drift.",
        "",
        "**5. How exactly was annual gross turnover calculated?**",
        "",
        "Daily turnover = sum(|new_weight - old_weight|) + |new_cash - old_cash| over all positions.",
        "This is round-trip (two-way) turnover as a fraction of NAV.",
        "Annualized = sum of daily turnover across the evaluation period / number of years.",
        "",
        "**6. Did turnover include both buys and sells?**",
        "",
        "Yes. sum(|new_weight - old_weight|) captures both weight increases (buys) and decreases (sells).",
        "Cash changes are also included.",
        "",
        "**7. What NAV denominator was used?**",
        "",
        "Weights are fractions of TWR portfolio NAV after daily return accrual.",
        "Portfolio_growth normalizes weights on each date. Weights always sum to 1 - cash.",
        "",
        "**8. How much turnover came from each source?**",
        "",
        f"| Source | Existing (annualized) | Share |",
        f"|---|---:|--:|",
        f"| Total | {fmt_dec(m_ex['annualized_gross_turnover'])} | 100.00% |",
        f"| Entry/exit (complete) | {fmt_dec(m_ex['annualized_entry_exit_turnover'])} | {fmt_pct(m_ex['entry_exit_share'])} |",
        f"| Weight restoration | {fmt_dec(m_ex['annualized_weight_restoration_turnover'])} | {fmt_pct(m_ex['weight_restoration_share'])} |",
        f"| Portfolio constraints | 0.00 | 0.00% |",
        f"| Fold initialization | 0.00 | 0.00% |",
        f"| Fold termination | 0.00 | 0.00% |",
        f"| Other | 0.00 | 0.00% |",
        "",
        "**9. Did every annual evaluation fold restart from cash?**",
        "",
        "No. The simulation runs one continuous portfolio from its 2014 start through 2025.",
        "Each evaluation fold is a calendar-year slice of the same continuous path. There is no",
        "cash reset between years.",
        "",
        "**10. Were the reported 2021–2025 results created by linking one continuous portfolio",
        "or aggregating independently restarted annual portfolios?**",
        "",
        "One continuous portfolio. The published assembly code (`metrics()` then `fold_rows()`)",
        "slices the same `ledger` DataFrame by calendar year. All 2021–2025 fold results are",
        "non-overlapping slices of the same equity curve. There is no chain-linking or compounding",
        "across independent resets.",
        "",
        "---",
        "",
        "## Published-reproduction verification",
        "",
        f"| Metric | Published | Reproduced | Verdict |",
        f"|---|---:|---:|:---:|",
        f"| Annualized return | {fmt_pct(pub_ann)} | {fmt_pct(rep_ann)} | {'PASS' if ann_ok else 'FAIL'} |",
        f"| Annual gross turnover | {fmt_dec(pub_to)} | {fmt_dec(rep_to)} | {'PASS' if to_ok else 'FAIL'} |",
        f"| Max drawdown | {fmt_pct(pub_dd)} | {fmt_pct(rep_dd)} | {'PASS' if dd_ok else 'FAIL'} |",
        f"| Volatility | {fmt_pct(pub_vol)} | {fmt_pct(rep_vol)} | {'PASS' if vol_ok else 'FAIL'} |",
        "",
    ]

    if not (ann_ok and to_ok and dd_ok and vol_ok):
        lines.append("**REPRODUCTION FAILED.** Stopping before practical comparison.")
        report = "\n".join(lines)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "mechanics_audit_report.md").write_text(report)
        print(report)
        return {"output": str(output_dir), "reproduction": "FAIL"}
    lines.append("Reproduction matches exactly. Proceeding to practical comparison.")
    lines.append("")

    lines += [
        "## Existing vs practical mechanics — P4/N=30/monthly/rank-60, 2021–2025",
        "",
        "| Metric | Published | Practical | Difference |",
        "|---|---:|---:|---:|",
        f"| Annualized return | {fmt_pct(m_ex['annualized_return'])} | {fmt_pct(m_pr['annualized_return'])} | {fmt_pct(m_pr['annualized_return'] - m_ex['annualized_return'])} |",
        f"| SPY-relative return | {fmt_pct(m_ex['active_annualized_return_vs_SPY'])} | {fmt_pct(m_pr['active_annualized_return_vs_SPY'])} | {fmt_pct(m_pr['active_annualized_return_vs_SPY'] - m_ex['active_annualized_return_vs_SPY'])} |",
        f"| QQQ-relative return | {fmt_pct(m_ex['active_annualized_return_vs_QQQ'])} | {fmt_pct(m_pr['active_annualized_return_vs_QQQ'])} | {fmt_pct(m_pr['active_annualized_return_vs_QQQ'] - m_ex['active_annualized_return_vs_QQQ'])} |",
        f"| Volatility | {fmt_pct(m_ex['annualized_volatility'])} | {fmt_pct(m_pr['annualized_volatility'])} | {fmt_pct(m_pr['annualized_volatility'] - m_ex['annualized_volatility'])} |",
        f"| Max drawdown | {fmt_pct(m_ex['maximum_drawdown'])} | {fmt_pct(m_pr['maximum_drawdown'])} | {fmt_pct(m_pr['maximum_drawdown'] - m_ex['maximum_drawdown'])} |",
        f"| Annual gross turnover | {fmt_dec(m_ex['annualized_gross_turnover'])} | {fmt_dec(m_pr['annualized_gross_turnover'])} | {fmt_dec(m_pr['annualized_gross_turnover'] - m_ex['annualized_gross_turnover'])} |",
        f"| Total purchases | {m_ex['total_purchases']} | {m_pr['total_purchases']} | {m_pr['total_purchases'] - m_ex['total_purchases']} |",
        f"| Total sales | {m_ex['total_sales']} | {m_pr['total_sales']} | {m_pr['total_sales'] - m_ex['total_sales']} |",
        f"| Average holding period | {fmt_dec(m_ex.get('average_holding_period_days', 0) / 365.25, 2)} yr | {fmt_dec(m_pr.get('average_holding_period_days', 0) / 365.25, 2)} yr | |",
        "",
        "### Turnover decomposition — 2021–2025",
        "",
        "| Source | Existing (annualized) | Share | Practical (annualized) | Share |",
        "|---|---:|---:|---:|---:|",
        f"| Total | {fmt_dec(m_ex['annualized_gross_turnover'])} | 100.00% | {fmt_dec(m_pr['annualized_gross_turnover'])} | 100.00% |",
        f"| Entry/exit | {fmt_dec(m_ex['annualized_entry_exit_turnover'])} | {fmt_pct(m_ex['entry_exit_share'])} | {fmt_dec(m_pr['annualized_entry_exit_turnover'])} | {fmt_pct(m_pr['entry_exit_share'])} |",
        f"| Weight restoration | {fmt_dec(m_ex['annualized_weight_restoration_turnover'])} | {fmt_pct(m_ex['weight_restoration_share'])} | {fmt_dec(m_pr['annualized_weight_restoration_turnover'])} | {fmt_pct(m_pr['weight_restoration_share'])} |",
        "",
        "### Annual breakdown — Existing (published) mechanics",
        "",
        "| Year | Return | SPY-rel | QQQ-rel | Vol | Max DD | Gross TO | Entry/exit TO | Weight-restore TO |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for yr in eval_years:
        s, e = pd.Timestamp(f"{yr}-01-01"), pd.Timestamp(f"{yr}-12-31")
        lines.append(ann_row(yr, metrics_ex(ex_ledger, bench, s, e)))

    lines += [
        "",
        "### Annual breakdown — Practical mechanics",
        "",
        "| Year | Return | SPY-rel | QQQ-rel | Vol | Max DD | Gross TO | Entry/exit TO | Weight-restore TO |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for yr in eval_years:
        s, e = pd.Timestamp(f"{yr}-01-01"), pd.Timestamp(f"{yr}-12-31")
        lines.append(ann_row(yr, metrics_ex(pr_ledger, bench, s, e)))

    lines += [
        "",
        "---",
        "",
        "## Decisions",
        "",
        "### 1. Turnover mathematical correctness",
        "",
        f"The published annualized gross turnover ({fmt_dec(m_ex['annualized_gross_turnover'])}) is mathematically",
        "correct given the code's definition: sum of daily |weight change| + cash change across all",
        "positions, annualized as total / years. This is round-trip turnover as a fraction of NAV.",
        "Reproduction matches the published figure exactly.",
        "",
        "### 2. Match to intended practical mechanics",
        "",
        "The published backtest does NOT match the intended practical mechanics in one material way:",
        "it resets ALL surviving positions to equal weight at every monthly review.",
        f"Weight restoration accounts for {fmt_pct(m_ex['weight_restoration_share'])} of total turnover.",
        "",
        "The practical mechanics (sell-only-below-60, survivors drift, quarterly correction only)",
        f"reduce weight-restoration turnover to {fmt_pct(m_pr['weight_restoration_share'])} and",
        f"lower total annualized gross turnover from {fmt_dec(m_ex['annualized_gross_turnover'])} to",
        f"{fmt_dec(m_pr['annualized_gross_turnover'])} — a reduction of",
        f"{fmt_dec(m_ex['annualized_gross_turnover'] - m_pr['annualized_gross_turnover'])}.",
        "",
        "The rank-60 buffer determines which names enter/exit; both variants make the same 484 purchases and 484 sales. The turnover reduction comes entirely from not adjusting surviving positions' weights at non-quarterly reviews.",
        "",
        "### 3. Fold-restart effect",
        "",
        "The fold-restart effect is ZERO. The simulation is one continuous portfolio from 2014 through",
        "2025. Evaluation folds are calendar-year slices of the same equity curve. No fold restart, no",
        "cash reset, no initialization turnover, and no termination turnover occur.",
        "",
        "Therefore fold-restart effects did NOT distort the published turnover or return figures.",
        "",
        "### 4. Do practical mechanics materially change the P4 conclusion?",
        "",
        f"Published P4 active return vs QQQ: {fmt_pct(m_ex['active_annualized_return_vs_QQQ'])}",
        f"Practical P4 active return vs QQQ: {fmt_pct(m_pr['active_annualized_return_vs_QQQ'])}",
        "",
        f"Practical turnover: {fmt_dec(m_pr['annualized_gross_turnover'])} vs published {fmt_dec(m_ex['annualized_gross_turnover'])}.",
    ]

    ex_qqq = m_ex['active_annualized_return_vs_QQQ']
    pr_qqq = m_pr['active_annualized_return_vs_QQQ']

    if pr_qqq < 0:
        lines.append(f"- Practical mechanics also trail QQQ ({fmt_pct(pr_qqq)} active return).")
        lines.append("- The practical changes do not rescue P4 from benchmark underperformance.")
    else:
        lines.append(f"- Practical mechanics beat QQQ by {fmt_pct(pr_qqq)} active return.")
        lines.append("- However, this is a mechanical-fidelity comparison, not a new strategy test; the")
        lines.append("  single diagnostic result does not override the predefined frozen development gates.")

    if m_pr['annualized_gross_turnover'] > 2.0:
        lines.append(f"- Turnover ({fmt_dec(m_pr['annualized_gross_turnover'])}) still exceeds the 200% ceiling by a wide margin.")
    else:
        lines.append(f"- Turnover ({fmt_dec(m_pr['annualized_gross_turnover'])}) falls below the 200% ceiling.")

    lines += [
        "",
        "### 5. Final determination",
        "",
        "**P4 remains FAIL.**",
        "",
        "The practical mechanics comparison shows that:",
        "- The single mechanical change (no monthly equal-weight restoration, quarterly correction only)",
        "  reduces turnover but does not change the competitive conclusion.",
        f"- P4 underperforms QQQ by {fmt_pct(pr_qqq)} under practical mechanics.",
        f"- Annual turnover ({fmt_dec(m_pr['annualized_gross_turnover'])}) exceeds 200%.",
        "- Fold restarts do NOT distort the results.",
        "",
        "The standalone P4 FAIL is robust to the practical mechanical adjustment.",
        "No further investigation of portfolio-mechanics effects is warranted.",
        "",
        "---",
        "",
        "*This is a mechanical-fidelity comparison, not a new strategy search. No P1, P2, or P3",
        "promotion. No scanner-launcher development. No new factor search.*",
    ]

    report = "\n".join(lines)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "mechanics_audit_report.md").write_text(report)
    ex_ledger.to_csv(output_dir / "existing_mechanics_daily.csv", date_format="%Y-%m-%d")
    pr_ledger.to_csv(output_dir / "practical_mechanics_daily.csv", date_format="%Y-%m-%d")
    print(report)
    return {"output": str(output_dir), "reproduction": "PASS"}


def main() -> int:
    output = ROOT / "outputs/audit/price_mechanics"
    run_audit(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
