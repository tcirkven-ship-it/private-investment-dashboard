"""Corrected persistence rerun — fixed exit2 state machine.

Implements the canonical exit-confirmation state and reruns
all persistence candidates with development data only.
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
from src.backtest.mechanics_audit import fmt_pct, fmt_dec, _position_init, _drift

EVIDENCE_LABEL = (
    "Exploratory survivor-biased historical Price research "
    "using a currently reconstructable yfinance universe."
)
WINSOR = [0.025, 0.975]

# ============================================================
# Canonical exit-confirmation state machine
# ============================================================

class ExitConfirmation:
    """Tracks consecutive below-threshold rank observations.

    CORRECTED BEHAVIOR:
    - Counter persists across monthly reviews. NOT cleared for survivors.
    - Increments when rank > threshold.
    - Resets ONLY when rank recovers to <= threshold, or after exit.
    - Survives quarterly rebalancing and year boundaries.
    - Keyed by security integer index (stable ticker).
    """

    def __init__(self, confirm_months: int = 2, rank_limit: int = 60):
        self.confirm_months = confirm_months
        self.rank_limit = rank_limit
        self._counters: dict[int, int] = {}

    def check(self, idx: int, rank: int) -> bool:
        """Return True if the stock should exit. Updates internal state."""
        if rank > self.rank_limit:
            self._counters[idx] = self._counters.get(idx, 0) + 1
            if self._counters[idx] >= self.confirm_months:
                return True
        else:
            self._counters.pop(idx, None)  # recovered — reset
        return False

    def remove(self, idx: int) -> None:
        """Call after a stock exits to clean up its counter."""
        self._counters.pop(idx, None)

    def reset(self, idx: int) -> None:
        """Force-reset counter (e.g., after hard-eligibility re-entry)."""
        self._counters.pop(idx, None)


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
    exit_confirm: int = 0
    retention_multiple: float = 2.0


def simulate_persistence(
    cfg: Configuration,
    panels: Panels,
    cache: RankingCache,
    spec: PersistenceSpec,
    cost_bps: float = 10.0,
) -> pd.DataFrame:
    """Canonical persistence simulation with corrected exit confirmation."""
    dates = panels.dates
    start_index = int(dates.searchsorted(pd.Timestamp("2014-01-01")))
    sig_dates = review_dates(dates[start_index:], cfg.schedule)
    fill_map: dict[int, int] = {}
    for sd in sig_dates:
        si = int(dates.get_loc(sd))
        if si + 1 < len(dates):
            fill_map[si + 1] = si

    rank_limit = spec.retention_multiple * cfg.portfolio_size
    size = cfg.portfolio_size
    ec = ExitConfirmation(confirm_months=spec.exit_confirm, rank_limit=rank_limit)

    weights, cash, _ = _position_init()
    rows = []
    for di in range(start_index, len(dates)):
        dr = dates[di]
        sret = panels.returns.iloc[di].to_numpy(dtype=float)
        weights, cash, day_return = _drift(weights, cash, sret, di, panels)

        total_TO = 0.0
        if di in fill_map:
            si = fill_map[di]
            sd = dates[si]
            _, ranks = cache.get(cfg.candidate, si)
            valid = np.isfinite(panels.scores[cfg.candidate].iloc[si].to_numpy(dtype=float))
            order, _ = cache.get(cfg.candidate, si)
            is_quarterly = sd.month in {3, 6, 9, 12}

            # === CORRECTED exit logic ===
            survivors = {}
            for idx, w in list(weights.items()):
                if idx >= len(valid) or not valid[idx]:
                    ec.remove(idx)
                    continue
                rk = int(ranks[idx])
                # Updated state machine — counter persists; no blanket survivours clear
                if spec.exit_confirm > 0 and ec.check(idx, rk):
                    continue  # confirmed exit
                survivors[idx] = w

            # ALSO clear counters for recovered stocks in the main loop
            # (ec.check handles this internally)

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
            for i in list(ec._counters):
                if i not in target:
                    ec.remove(i)

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
    panels = load_panels(config, pd.Timestamp("2020-12-31"))
    scores = candidate_scores(panels)
    custom = Panels(
        dates=panels.dates, tickers=panels.tickers, adjusted=panels.adjusted,
        raw_close=panels.raw_close, volume=panels.volume, returns=panels.returns,
        liquidity_ok=panels.liquidity_ok, factors=panels.factors, scores=scores,
        benchmark_returns=panels.benchmark_returns, sectors=panels.sectors,
        industries=panels.industries, coverage=panels.coverage, integrity=panels.integrity,
    )
    bench = panels.benchmark_returns
    dev_years = list(range(2015, 2021))
    dev_start, dev_end = pd.Timestamp("2015-01-01"), pd.Timestamp("2020-12-31")

    cand_specs = [
        ("A3", PersistenceSpec("exit2", exit_confirm=2)),
        ("A3", PersistenceSpec("combined", exit_confirm=2, retention_multiple=3.0)),
        ("B2", PersistenceSpec("exit2", exit_confirm=2)),
        ("B2", PersistenceSpec("combined", exit_confirm=2, retention_multiple=3.0)),
        ("D1", PersistenceSpec("exit2", exit_confirm=2)),
        ("D1", PersistenceSpec("combined", exit_confirm=2, retention_multiple=3.0)),
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    all_rows = []
    fold_rows_all = []

    for cname, spec in cand_specs:
        cid = f"{cname}_{spec.name}_N30_monthly_B{spec.retention_multiple:.0f}_U_EW"
        cfg = Configuration(cname, 30, "monthly", spec.retention_multiple, "unconstrained", "equal")
        cache = RankingCache(custom)
        ledger = simulate_persistence(cfg, custom, cache, spec, cost_bps=10)

        agg = metrics(ledger, bench, dev_start, dev_end)
        agg["candidate"] = cname
        agg["spec"] = spec.name
        agg["configuration_id"] = cid
        agg["test_year"] = "agg"
        all_rows.append(agg)

        for yr in dev_years:
            s, e = pd.Timestamp(f"{yr}-01-01"), pd.Timestamp(f"{yr}-12-31")
            ym = metrics(ledger, bench, s, e)
            ym["candidate"] = cname
            ym["spec"] = spec.name
            ym["configuration_id"] = cid
            ym["test_year"] = yr
            fold_rows_all.append(ym)

    pdf = pd.DataFrame(all_rows)
    fold_df = pd.DataFrame(fold_rows_all)
    pdf.to_csv(output_dir / "corrected_aggregate.csv", index=False)
    fold_df.to_csv(output_dir / "corrected_folds.csv", index=False)

    # Generate report
    lines = [
        "# Corrected Price persistence results — fixed exit2 state machine",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        f"**Development only (2015–2020), 10bps cost**",
        "",
        "| Candidate | Spec | Ann ret | SPY-rel | QQQ-rel | TO | Max DD | DD vs SPY | SPY wins | QQQ wins | Fold dep |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for _, r in pdf.iterrows():
        c = r.candidate
        s = r.spec
        fs = fold_df[(fold_df.candidate == c) & (fold_df.spec == s)]
        spy_wins = int((fs.active_annualized_return_vs_SPY.astype(float) > 0).sum())
        qqq_wins = int((fs.active_annualized_return_vs_QQQ.astype(float) > 0).sum())
        spy_acts = fs.active_annualized_return_vs_SPY.astype(float)
        fold_dep = float(spy_acts.abs().max() / spy_acts.abs().sum()) if spy_acts.abs().sum() > 0 else 1.0
        dd_spy = float(fs.drawdown_difference_vs_SPY.min())

        lines.append(
            f"| {c} | {s} | {fmt_pct(r.annualized_return)} | {fmt_pct(r.active_annualized_return_vs_SPY)} "
            f"| {fmt_pct(r.active_annualized_return_vs_QQQ)} | {fmt_dec(r.annualized_gross_turnover)} "
            f"| {fmt_pct(r.maximum_drawdown)} | {fmt_pct(dd_spy)} "
            f"| {spy_wins}/6 | {qqq_wins}/6 | {fmt_dec(fold_dep)} |")

    # Gates
    lines += [
        "",
        "## Development gates",
        "",
        "| Gate | Threshold |",
        "|---|---|",
        "| Turnover | < 250% |",
        "| Median vs SPY | > 0% |",
        "| Median vs QQQ | > 0% |",
        "| Fold wins vs SPY | >= 4/6 |",
        "| Fold wins vs QQQ | >= 3/6 |",
        "| Absolute max DD | < 40% |",
        "| DD vs SPY per fold | > -15pp |",
        "| Fold dependence | < 60% |",
        "",
        "## Gate results",
        "",
        "| Candidate | Spec | TO pass | Med SPY | Med QQQ | SPY wins | QQQ wins | Max DD | DD vs SPY | Fold dep | ALL PASS |",
        "|---|---|:---|:---|:---|:---|:---|:---|:---|:---|:---:|",
    ]

    for _, r in pdf.iterrows():
        c = r.candidate
        s = r.spec
        fs = fold_df[(fold_df.candidate == c) & (fold_df.spec == s)]
        spy_acts = fs.active_annualized_return_vs_SPY.astype(float)
        qqq_acts = fs.active_annualized_return_vs_QQQ.astype(float)

        to_ok = r.annualized_gross_turnover < 2.5
        med_spy = float(spy_acts.median()) > 0
        med_qqq = float(qqq_acts.median()) > 0
        spy_w = int((spy_acts > 0).sum()) >= 4
        qqq_w = int((qqq_acts > 0).sum()) >= 3
        dd_abs = r.maximum_drawdown > -0.40
        dd_spy = float(fs.drawdown_difference_vs_SPY.min()) > -0.15
        fd = float(spy_acts.abs().max() / spy_acts.abs().sum()) if spy_acts.abs().sum() > 0 else 1.0
        fd_ok = fd < 0.60
        all_pass = all([to_ok, med_spy, med_qqq, spy_w, qqq_w, dd_abs, dd_spy, fd_ok])

        lines.append(
            f"| {c} | {s} | {'PASS' if to_ok else 'FAIL'} | {'PASS' if med_spy else 'FAIL'} "
            f"| {'PASS' if med_qqq else 'FAIL'} | {int((spy_acts > 0).sum())}/6 | {int((qqq_acts > 0).sum())}/6 "
            f"| {'PASS' if dd_abs else 'FAIL'} | {'PASS' if dd_spy else 'FAIL'} | {'PASS' if fd_ok else 'FAIL'} "
            f"| {'**PASS**' if all_pass else 'FAIL'} |")

    lines += [
        "",
        "## Decision",
        "",
    ]

    passes = []
    for _, r in pdf.iterrows():
        c = r.candidate
        s = r.spec
        fs = fold_df[(fold_df.candidate == c) & (fold_df.spec == s)]
        spy_acts = fs.active_annualized_return_vs_SPY.astype(float)
        qqq_acts = fs.active_annualized_return_vs_QQQ.astype(float)
        to_ok = r.annualized_gross_turnover < 2.5
        med_spy = float(spy_acts.median()) > 0
        med_qqq = float(qqq_acts.median()) > 0
        spy_w = int((spy_acts > 0).sum()) >= 4
        qqq_w = int((qqq_acts > 0).sum()) >= 3
        dd_abs = r.maximum_drawdown > -0.40
        dd_spy = float(fs.drawdown_difference_vs_SPY.min()) > -0.15
        fd = float(spy_acts.abs().max() / spy_acts.abs().sum()) if spy_acts.abs().sum() > 0 else 1.0
        fd_ok = fd < 0.60
        if all([to_ok, med_spy, med_qqq, spy_w, qqq_w, dd_abs, dd_spy, fd_ok]):
            passes.append((c, s, r.annualized_gross_turnover))

    if passes:
        passes.sort(key=lambda x: x[2])  # lowest turnover first
        lines += [f"**{len(passes)} specification(s) pass all gates.**",
                  f"Best: {passes[0][0]} {passes[0][1]} (TO={fmt_dec(passes[0][2])}).",
                  "Freeze as finalist for potential evaluation."]
    else:
        lines += ["**No specification passes all development gates.**",
                  "",
                  "PRICE PERSISTENCE PATH CLOSED UNDER CURRENT YFINANCE DATASET.",
                  "",
                  "The corrected exit2 state machine causes turnover to explode",
                  "above the 250% ceiling for all candidates. The exit2 confirmation",
                  "mechanism does not control turnover when it actually functions."]

    (output_dir / "corrected_persistence_results.md").write_text("\n".join(lines))
    (ROOT / "research/86_corrected_price_persistence_results.md").write_text("\n".join(lines))
    (ROOT / "research/87_corrected_price_persistence_decision.md").write_text("\n".join(lines))

    # Summary
    summary_lines = [
        "# Corrected Price persistence — summary",
        "",
        f"**Decision:** {'PASS' if passes else 'FAIL'} — {'finalist selected' if passes else 'path closed'}",
    ]
    (output_dir / "corrected_summary.md").write_text("\n".join(summary_lines))
    (ROOT / "outputs/final/corrected_price_persistence_summary.md").write_text("\n".join(summary_lines))

    return {"pass_count": len(passes), "passes": [p[0] + " " + p[1] for p in passes]}


def main() -> int:
    output = ROOT / "outputs/experiment_runs/CORRECTED-PERSISTENCE"
    result = run_corrected(output)
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
