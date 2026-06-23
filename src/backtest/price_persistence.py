"""Price persistence experiment — controlled mechanics variations.

Tests shortlisted signals (A3, B2, D1) with revised entry/exit mechanics
using development-only data. No evaluation unless gates pass.
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
    review_dates, write_json,
)
from src.backtest.mechanics_audit import (
    _position_init, _drift, _practical_rebalance,
    fmt_pct, fmt_dec,
)
from src.backtest.price_walkforward import metrics as compute_metrics

EVIDENCE_LABEL = (
    "Exploratory survivor-biased historical Price research "
    "using a currently reconstructable yfinance universe."
)
WINSOR = [0.025, 0.975]


def _min_obs(s: pd.DataFrame, n: int) -> pd.DataFrame:
    return s.where(s.notna().cumsum() >= n)


def candidate_scores(panels: Panels) -> dict[str, pd.DataFrame]:
    """Compute A3, B2, D1 scores."""
    adj = panels.adjusted
    M12_1 = _min_obs(adj.shift(21) / adj.shift(252) - 1, 253)
    M6_1 = _min_obs(adj.shift(21) / adj.shift(126) - 1, 127)
    rM12 = cross_sectional_percentile(M12_1, 1, WINSOR)
    rM6 = cross_sectional_percentile(M6_1, 1, WINSOR)
    A3 = (rM12 + rM6) / 2
    A3_req = M12_1.notna() & M6_1.notna()

    MA50 = adj.rolling(50, min_periods=50).mean()
    MA200 = adj.rolling(200, min_periods=200).mean()
    MA50_200 = MA50 / MA200 - 1
    rMA50_200 = cross_sectional_percentile(MA50_200, 1, WINSOR)
    B2 = (A3 + rMA50_200) / 2
    B2_req = MA50_200.notna() & A3_req

    log_ret = np.log(adj / adj.shift(1))
    VOL252 = _min_obs(log_ret.rolling(252, min_periods=200).std(ddof=1) * np.sqrt(252), 200)
    rVOL = cross_sectional_percentile(VOL252, -1, WINSOR)
    A3_VOL = A3 / rVOL.where(rVOL > 0, np.nan)
    D1 = cross_sectional_percentile(A3_VOL, 1, WINSOR)
    D1_req = A3_req & VOL252.notna()

    return {
        "A3": A3.where(A3_req),
        "B2": B2.where(B2_req),
        "D1": D1.where(D1_req),
    }


@dataclass
class PersistenceSpec:
    name: str
    min_holding_months: int = 0
    exit_confirm_months: int = 0
    retention_multiple: float = 2.0
    entry_confirm_months: int = 0


def simulate_persistence(
    config: Configuration,
    panels: Panels,
    cache: RankingCache,
    spec: PersistenceSpec,
) -> pd.DataFrame:
    """Practical mechanics with persistence modifications."""
    dates = panels.dates
    start_index = int(dates.searchsorted(pd.Timestamp("2014-01-01")))
    sig_dates = review_dates(dates[start_index:], config.schedule)
    fill_map: dict[int, int] = {}
    for sd in sig_dates:
        si = int(dates.get_loc(sd))
        if si + 1 < len(dates):
            fill_map[si + 1] = si

    rank_limit = spec.retention_multiple * config.portfolio_size
    weights, cash, buy_dates = _position_init()
    entry_signal_dates: dict[int, int] = {}  # idx -> first signal idx confirming entry
    exit_signals: dict[int, int] = {}  # idx -> count of consecutive below-rank observations

    rows = []
    for di in range(start_index, len(dates)):
        dr = dates[di]
        sret = panels.returns.iloc[di].to_numpy(dtype=float)
        weights, cash, day_return = _drift(weights, cash, sret, di, panels)
        total_TO = 0
        if di in fill_map:
            si = fill_map[di]
            sd = dates[si]
            _, ranks = cache.get(config.candidate, si)
            valid = np.isfinite(panels.scores[config.candidate].iloc[si].to_numpy(dtype=float))
            order, _ = cache.get(config.candidate, si)
            sig_date = sd
            is_quarterly = sig_date.month in {3, 6, 9, 12}

            # === Entry confirmation ===
            # Compute which names have been score-eligible for entry_confirm_months
            entry_ok = set()
            if spec.entry_confirm_months > 0:
                # Check if name has been in top-30 for consecutive reviews
                for ti, val in enumerate(valid):
                    if not val:
                        continue
                    tkr_idx = ti
                    if tkr_idx not in entry_signal_dates:
                        if ranks[ti] <= config.portfolio_size:
                            entry_signal_dates[tkr_idx] = 1
                        continue
                    if ranks[ti] <= config.portfolio_size:
                        entry_signal_dates[tkr_idx] += 1
                    else:
                        del entry_signal_dates[tkr_idx]
                        continue
                    if entry_signal_dates[tkr_idx] >= spec.entry_confirm_months:
                        entry_ok.add(tkr_idx)
            else:
                for ti, _ in enumerate(valid):
                    if valid[ti]:
                        entry_ok.add(ti)

            # === Exit mechanics ===
            survivors = {}
            for idx, w in list(weights.items()):
                if idx >= len(valid) or not valid[idx]:
                    continue
                below = ranks[idx] > rank_limit
                if below and spec.exit_confirm_months > 0:
                    exit_signals[idx] = exit_signals.get(idx, 0) + 1
                    if exit_signals[idx] < spec.exit_confirm_months:
                        survivors[idx] = w
                        continue
                    else:
                        continue
                elif below:
                    continue

                # Minimum holding period
                if spec.min_holding_months > 0 and idx in buy_dates:
                    months_held = (sd.year - buy_dates[idx].year) * 12 + (sd.month - buy_dates[idx].month)
                    if months_held < spec.min_holding_months and ranks[idx] <= rank_limit * 1.5:
                        survivors[idx] = w
                        continue
                survivors[idx] = w

            # Clear exit signals for survivors
            for idx in survivors:
                exit_signals.pop(idx, None)

            sold_set = set(weights) - set(survivors)
            open_slots = config.portfolio_size - len(survivors)

            # Candidates: highest-ranked that pass entry confirmation
            candidates = []
            for idx in order:
                ival = int(idx)
                if len(candidates) >= open_slots:
                    break
                if ival not in survivors and valid[ival] and ival in entry_ok:
                    candidates.append(ival)

            cash_available = cash + sum(weights[i] for i in sold_set)

            if is_quarterly:
                held = set(survivors) | set(candidates)
                target = {i: 1.0 / config.portfolio_size for i in held}
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
                if i in buy_dates:
                    new_buy[i] = buy_dates[i]
                else:
                    new_buy[i] = sd
                    entry_signal_dates[i] = 0
            buy_dates = new_buy
            weights, cash = target, cash_target
            # Reset exit signals for new entries
            for i in target:
                exit_signals.pop(i, None)

        hhi = sum(w * w for w in weights.values())
        t5 = sum(sorted(weights.values(), reverse=True)[:5])
        rows.append({"date": dr, "daily_return": day_return, "gross_turnover": total_TO,
                     "holding_count": len(weights), "cash_weight": cash,
                     "weight_hhi": hhi, "top5_weight": t5})
    return pd.DataFrame(rows).set_index("date")


def run_persistence(output_dir: Path) -> dict:
    config_path = ROOT / "research/configs/price_component_walkforward_v1_1_full_history.json"
    config = json.loads(config_path.read_text())
    panels = load_panels(config, pd.Timestamp("2020-12-31"))
    scores = candidate_scores(panels)

    custom = Panels(
        dates=panels.dates, tickers=panels.tickers,
        adjusted=panels.adjusted, raw_close=panels.raw_close,
        volume=panels.volume, returns=panels.returns,
        liquidity_ok=panels.liquidity_ok, factors=panels.factors,
        scores=scores, benchmark_returns=panels.benchmark_returns,
        sectors=panels.sectors, industries=panels.industries,
        coverage=panels.coverage, integrity=panels.integrity,
    )

    candidates = ["A3", "B2", "D1"]
    specs = [
        PersistenceSpec("base"),
        PersistenceSpec("min3", min_holding_months=3),
        PersistenceSpec("exit2", exit_confirm_months=2),
        PersistenceSpec("rank90", retention_multiple=3.0),
        PersistenceSpec("entry2", entry_confirm_months=2),
        PersistenceSpec("combined", min_holding_months=3, exit_confirm_months=2, retention_multiple=3.0, entry_confirm_months=2),
    ]
    dev_years = list(range(2015, 2021))
    dev_start, dev_end = pd.Timestamp("2015-01-01"), pd.Timestamp("2020-12-31")
    bench = panels.benchmark_returns

    all_rows = []
    for cname in candidates:
        for sp in specs:
            cid = f"{cname}_{sp.name}_N30_monthly_B{sp.retention_multiple:.0f}_U_EW"
            cfg = Configuration(cname, 30, "monthly", sp.retention_multiple, "unconstrained", "equal")
            cache = RankingCache(custom)
            ledger = simulate_persistence(cfg, custom, cache, sp)
            agg = compute_metrics(ledger, bench, dev_start, dev_end)
            agg["candidate"] = cname
            agg["spec"] = sp.name
            agg["configuration_id"] = cid
            agg["min_holding"] = sp.min_holding_months
            agg["exit_confirm"] = sp.exit_confirm_months
            agg["retention"] = sp.retention_multiple
            agg["entry_confirm"] = sp.entry_confirm_months
            for yr in dev_years:
                s, e = pd.Timestamp(f"{yr}-01-01"), pd.Timestamp(f"{yr}-12-31")
                ym = compute_metrics(ledger, bench, s, e)
                ym["configuration_id"] = cid
                ym["candidate"] = cname
                ym["spec"] = sp.name
                ym["test_year"] = yr
                all_rows.append(ym)
            agg["test_year"] = "agg"
            all_rows.append(agg)

    pdf = pd.DataFrame(all_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf.to_csv(output_dir / "persistence_results.csv", index=False)
    write_json(output_dir / "done.json", {"status": "complete"})

    # Separate aggregate (test_year is string 'agg') from fold rows
    agg_rows = pdf[pdf.test_year == "agg"].copy() if len(pdf) else pd.DataFrame()
    fold_rows = pdf[pdf.test_year != "agg"].copy() if len(pdf) else pd.DataFrame()

    lines = [
        f"# Price persistence experiment ({EVIDENCE_LABEL})",
        "",
        "## Development-only results (2015–2020)",
        "",
        "| Candidate | Spec | Ann ret | SPY-rel | QQQ-rel | Vol | Max DD | TO | Wins SPY | Wins QQQ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for _, row in agg_rows.iterrows():
        fs = fold_rows[(fold_rows.candidate == row.candidate) & (fold_rows.spec == row.spec)]
        wins_s = int((fs.active_annualized_return_vs_SPY.astype(float) > 0).sum()) if len(fs) else 0
        wins_q = int((fs.active_annualized_return_vs_QQQ.astype(float) > 0).sum()) if len(fs) else 0
        to_val = float(row.annualized_gross_turnover) if pd.notna(row.annualized_gross_turnover) else 0
        lines.append(
            f"| {row.candidate} | {row.spec} "
            f"| {fmt_pct(row.annualized_return)} | {fmt_pct(row.active_annualized_return_vs_SPY)} "
            f"| {fmt_pct(row.active_annualized_return_vs_QQQ)} | {fmt_pct(row.annualized_volatility)} "
            f"| {fmt_pct(row.maximum_drawdown)} | {fmt_dec(to_val)} "
            f"| {wins_s}/6 | {wins_q}/6 |")

    lines += [
        "",
        "## Revised development gates",
        "",
        "| Gate | Threshold |",
        "|---|---|",
        "| Turnover | < 250% (prefer < 200%) |",
        "| Median vs SPY | > 0% |",
        "| Median vs QQQ | > 0% |",
        "| Fold wins vs SPY | >= 4/6 |",
        "| Fold wins vs QQQ | >= 3/6 |",
        "| Absolute max DD | < 40% |",
        "| Max DD vs SPY per fold | not worse than 15pp |",
        "| Fold dependence | max share < 60% |",
        "| Best stock removal | does not eliminate advantage |",
        "| Best year removal | does not eliminate advantage |",
        "| N-size direction | N=20/30/40 same direction |",
        "| Suspicious series | not driving result |",
        "",
    ]

    (output_dir / "research_75_persistence_results.md").write_text("\n".join(lines))
    return {"output": str(output_dir), "configurations": len(all_rows)}


def main() -> int:
    output = ROOT / "outputs/experiment_runs/PRICE-PERSISTENCE"
    result = run_persistence(output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
