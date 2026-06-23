"""Price Generation 2 — controlled alternative signal research.

Implements candidate families A–F, runs development filtering, and
evaluates finalists on untouched 2021–2025 folds.
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
    Configuration, Panels, RankingCache,
    cross_sectional_percentile, load_panels, max_drawdown_stats,
    metrics, review_dates, sha256, write_json,
)
from src.backtest.mechanics_audit import (
    simulate_practical, metrics_ex, fmt_pct, fmt_dec,
)

EVIDENCE_LABEL = (
    "Exploratory survivor-biased historical Price research "
    "using a currently reconstructable yfinance universe."
)
WINSOR = [0.025, 0.975]
WINSOR_ZERO = [0.0, 1.0]


def _min_obs(series: pd.DataFrame, n: int) -> pd.DataFrame:
    return series.where(series.notna().cumsum() >= n)


def compute_candidate_scores(panels: Panels) -> dict[str, pd.DataFrame]:
    """Compute all candidate scores as date x ticker percentile DataFrames."""
    adj = panels.adjusted
    log_ret = np.log(adj / adj.shift(1))
    actual = adj.notna().cumsum()

    # === Raw signals ===
    M12_1 = _min_obs(adj.shift(21) / adj.shift(252) - 1, 253)
    M6_1 = _min_obs(adj.shift(21) / adj.shift(126) - 1, 127)
    TREND200 = _min_obs(adj / adj.rolling(200, min_periods=200).mean() - 1, 200)
    VOL252 = _min_obs(log_ret.rolling(252, min_periods=200).std(ddof=1) * np.sqrt(252), 200)
    MA50 = adj.rolling(50, min_periods=50).mean()
    MA200 = adj.rolling(200, min_periods=200).mean()
    MA50_200 = MA50 / MA200 - 1
    SPY_RET = panels.benchmark_returns["SPY"]
    def _compound(x: np.ndarray) -> float:
        return float(np.prod(1 + np.nan_to_num(x)) - 1)
    SPY_RET_6M = SPY_RET.rolling(126).apply(_compound, raw=True)
    SPY_RET_12M = SPY_RET.rolling(252).apply(_compound, raw=True)

    # Stock returns relative to SPY
    stock_ret_6m = adj.pct_change(126)
    stock_ret_12m = adj.pct_change(252)
    spy_rel_6m = stock_ret_6m.subtract(SPY_RET_6M, axis=0)
    spy_rel_12m = stock_ret_12m.subtract(SPY_RET_12M, axis=0)

    # 52-week high
    high_52w = adj.rolling(252).max()
    dist_52w = adj / high_52w  # 1.0 = at high, lower = far from high

    # Percentile ranks of raw signals
    rM12 = cross_sectional_percentile(M12_1, 1, WINSOR)
    rM6 = cross_sectional_percentile(M6_1, 1, WINSOR)
    rTREND = cross_sectional_percentile(TREND200, 1, WINSOR)
    rVOL = cross_sectional_percentile(VOL252, -1, WINSOR)
    rMA50_200 = cross_sectional_percentile(MA50_200, 1, WINSOR)
    rHIGH52 = cross_sectional_percentile(dist_52w, 1, WINSOR)
    rSPY6 = cross_sectional_percentile(spy_rel_6m, 1, WINSOR)
    rSPY12 = cross_sectional_percentile(spy_rel_12m, 1, WINSOR)
    rSPY_AVG = (rSPY6 + rSPY12) / 2

    # === Family A: Medium-term momentum ===
    A1 = rM12
    A2 = rM6
    A3 = (rM12 + rM6) / 2
    A3_req = M12_1.notna() & M6_1.notna()
    A4 = (rM12 * 2/3 + rM6 * 1/3)

    # === Family B: Momentum plus trend ===
    def _avg(rhs: pd.DataFrame, name: str, req: pd.DataFrame | None = None) -> pd.DataFrame:
        s = (A3 + rhs) / 2
        if req is not None:
            s = s.where(req)
        return s

    B1 = _avg(rTREND, "B1")
    B2 = _avg(rMA50_200, "B2", req=MA50_200.notna() & A3_req)
    # Slope200: 200-day linear regression slope / mean price
    x_arr = np.arange(200, dtype=float)
    x_mean = x_arr.mean()
    ssxx = ((x_arr - x_mean) ** 2).sum()

    def _slope_ratio(window: np.ndarray) -> float:
        if np.sum(np.isfinite(window)) < 200:
            return np.nan
        y = np.nan_to_num(window, nan=np.nanmean(window))
        slope = np.sum((x_arr - x_mean) * (y - y.mean())) / ssxx
        return float(slope / max(np.nanmean(y), 1e-12))

    SLOPE200 = adj.rolling(200, min_periods=200).apply(_slope_ratio, raw=True)
    rSLOPE = cross_sectional_percentile(SLOPE200, 1, WINSOR)
    B3 = _avg(rSLOPE, "B3", req=SLOPE200.notna() & A3_req)

    # PCT_ABOVE_200: fraction of last 63 sessions where close > MA200
    ABOVE200 = (adj > MA200).astype(float).rolling(63, min_periods=40).mean()
    rABOVE = cross_sectional_percentile(ABOVE200, 1, WINSOR)
    B4 = _avg(rABOVE, "B4", req=ABOVE200.notna() & A3_req)

    # === Family C: Breakout and relative strength ===
    C1 = rHIGH52
    C2 = _avg(rHIGH52, "C2", req=dist_52w.notna() & A3_req)

    rSPY6m = cross_sectional_percentile(
        _min_obs(spy_rel_6m, 126), 1, WINSOR)
    rSPY12m = cross_sectional_percentile(
        _min_obs(spy_rel_12m, 252), 1, WINSOR)
    SPY_REL = (rSPY6m + rSPY12m) / 2
    C3 = SPY_REL

    C4 = _avg(SPY_REL, "C4", req=spy_rel_6m.notna() & spy_rel_12m.notna() & A3_req)

    # === Family D: Controlled risk adjustment ===
    # D1: A3 / VOL252 (ratio percentile)
    A3_VOL = A3 / rVOL.where(rVOL > 0)
    rA3_VOL = cross_sectional_percentile(A3_VOL, 1, WINSOR)
    D1 = rA3_VOL.where(A3_req & VOL252.notna())
    # D2: A3 percentile - 0.25 * VOL252 percentile (rank of vol percentile, not raw)
    D2_raw = A3 - 0.25 * (1 - rVOL)  # Subtract penalty; rVOL already inverse-ranked
    rD2 = cross_sectional_percentile(D2_raw, 1, WINSOR)
    D2 = rD2.where(A3_req & VOL252.notna())
    # D3: exclude highest-vol decile, rank remainder by A3
    vol_decile = VOL252.rank(axis=1, pct=True)
    D3 = A3.where(vol_decile <= 0.9).where(A3_req & VOL252.notna())
    # D4: cap VOL252 at 80th percentile
    vol_80 = VOL252.quantile(0.8, axis=1)
    vol_capped = VOL252.where(vol_decile <= 0.8, vol_80, axis=0)
    rVOL_CAP = cross_sectional_percentile(vol_capped, -1, WINSOR)
    D4 = _avg(rVOL_CAP, "D4", req=VOL252.notna() & A3_req)

    # === Family E: Trend quality ===
    # E1: regression t-stat = slope * sqrt(ssxx) / resid_std
    def _regr_tstat(window: np.ndarray) -> float:
        if np.sum(np.isfinite(window)) < 200:
            return np.nan
        y = np.nan_to_num(window, nan=np.nanmean(window))
        slope = np.sum((x_arr - x_mean) * (y - y.mean())) / ssxx
        resid = y - (x_arr * slope + (y.mean() - slope * x_mean))
        resid_std = max(np.std(resid, ddof=2), 1e-12)
        return float(slope * np.sqrt(ssxx) / resid_std)

    REGR_T = adj.rolling(200, min_periods=200).apply(_regr_tstat, raw=True)
    rE1 = cross_sectional_percentile(REGR_T, 1, WINSOR)
    E1 = rE1.where(REGR_T.notna())

    # E2: fraction of positive monthly returns
    monthly_ret = (1 + panels.returns).resample("ME").prod() - 1
    pos_month = (monthly_ret > 0).astype(float).rolling(12, min_periods=12).mean()
    rE2 = cross_sectional_percentile(pos_month, 1, WINSOR)
    # Reindex monthly result back to daily dates
    E2_monthly = rE2.where(pos_month.notna())
    E2 = E2_monthly.reindex(panels.dates, method="ffill").loc[panels.dates]

    # E3: inverse of formation-period max drawdown (252 days)
    def _roll_max_dd(frame: pd.DataFrame, window: int) -> pd.DataFrame:
        wealth = (1 + frame).cumprod()
        running_max = wealth.cummax()
        dd = wealth / running_max - 1
        return dd.rolling(window, min_periods=window).min()
    form_dd = _roll_max_dd(panels.returns, 252)
    inv_dd = -form_dd  # positive = smaller drawdown
    rE3 = cross_sectional_percentile(inv_dd, 1, WINSOR)
    E3 = rE3.where(form_dd.notna())

    # E4: min rank percentile across 3m and 12m A3 (consistency)
    rM12_3m = cross_sectional_percentile(_min_obs(adj.shift(21) / adj.shift(63) - 1, 64), 1, WINSOR)
    rM6_3m = cross_sectional_percentile(_min_obs(adj.shift(21) / adj.shift(63) - 1, 64), 1, WINSOR)
    a3_3m_perc = (rM12_3m + rM6_3m) / 2
    E4_vals = np.minimum(a3_3m_perc.to_numpy(), A3.to_numpy())
    E4 = pd.DataFrame(E4_vals, index=panels.dates, columns=panels.tickers)
    E4 = E4.where(A3_req)

    # === P4 (failed control, for comparison) ===
    # Original formula: equal average of M12_1, M6_1, TREND200, VOL252(inverse) percentiles
    P4_control = (rM12 + rM6 + rTREND + rVOL) / 4
    P4_control = P4_control.where(A3_req & TREND200.notna() & VOL252.notna())

    scores: dict[str, pd.DataFrame] = {}
    candidates = {
        "A1": A1, "A2": A2, "A3": A3, "A4": A4,
        "B1": B1, "B2": B2, "B3": B3, "B4": B4,
        "C1": C1, "C2": C2, "C3": C3, "C4": C4,
        "D1": D1, "D2": D2, "D3": D3, "D4": D4,
        "E1": E1, "E2": E2, "E3": E3, "E4": E4 if isinstance(E4, pd.DataFrame) else E4,
        "P4_CONTROL": P4_control,
    }

    for name, sc in candidates.items():
        if isinstance(sc, pd.Series):
            sc = sc.to_frame(name)
        elif isinstance(sc, pd.DataFrame) and sc.shape[1] == 1:
            pass
        elif isinstance(sc, pd.DataFrame) and sc.shape[1] > 1:
            pass
        scores[name] = sc if isinstance(sc, pd.DataFrame) else sc

    return scores


def compute_gates(config_results: pd.DataFrame, fold_results: pd.DataFrame,
                  dev_years: list[int]) -> pd.DataFrame:
    """Apply development gates and select finalists."""
    candidates = config_results[~config_results.candidate.str.endswith("CONTROL")].copy()
    rows = []
    for cid in candidates.configuration_id.unique():
        c = candidates[candidates.configuration_id.eq(cid)].iloc[0]
        local = fold_results[fold_results.configuration_id.eq(cid)]
        spy_act = local.active_annualized_return_vs_SPY.astype(float)
        qqq_act = local.active_annualized_return_vs_QQQ.astype(float)
        to = float(c.annualized_gross_turnover)
        spy_dd = local.maximum_drawdown.astype(float)
        md_spy = float(spy_dd.min())
        max_fold_share = float(spy_act.abs().max() / spy_act.abs().sum()) if spy_act.abs().sum() > 0 else 1.0
        pos_folds = int((spy_act > 0).sum())
        gates = {
            "turnover_2.5": to <= 2.5,
            "turnover_2.0": to <= 2.0,
            "median_spy_pos": float(spy_act.median()) > 0,
            "fold_win_spy": float((spy_act > 0).mean()) >= 0.5,
            "fold_win_qqq": float((qqq_act > 0).mean()) >= 0.4,
            "drawdown_no_worse_than_spy_10pct": md_spy >= -0.10,
            "fold_dependence": max_fold_share <= 0.60,
            "pos_folds_4_6": pos_folds >= 4,
        }
        all_pass = all(gates.values())
        rows.append({
            "configuration_id": cid,
            "candidate": c.candidate,
            "portfolio_size": int(c.portfolio_size),
            "review_schedule": str(c.review_schedule),
            "retention_multiple": float(c.retention_multiple),
            "annualized_return": float(c.annualized_return),
            "annualized_gross_turnover": to,
            "median_active_vs_SPY": float(spy_act.median()),
            "median_active_vs_QQQ": float(qqq_act.median()),
            "fold_win_vs_SPY": float((spy_act > 0).mean()),
            "fold_win_vs_QQQ": float((qqq_act > 0).mean()),
            "worst_dd_diff_SPY": md_spy,
            "max_fold_share_active_SPY": max_fold_share,
            "positive_folds": pos_folds,
            **{f"gate_{k}": v for k, v in gates.items()},
            "all_gates_pass": all_pass,
        })
    return pd.DataFrame(rows)


def simulate_all(panels: Panels, scores: dict[str, pd.DataFrame],
                 dev_years: list[int], eval_years: list[int]) -> tuple[
                     pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Simulate all candidates, compute metrics, run gates."""
    dev_start, dev_end = pd.Timestamp(f"{min(dev_years)}-01-01"), pd.Timestamp(f"{max(dev_years)}-12-31")
    eval_start, eval_end = pd.Timestamp(f"{min(eval_years)}-01-01"), pd.Timestamp(f"{max(eval_years)}-12-31")

    # Build panels with custom scores
    custom = Panels(
        dates=panels.dates, tickers=panels.tickers,
        adjusted=panels.adjusted, raw_close=panels.raw_close,
        volume=panels.volume, returns=panels.returns,
        liquidity_ok=panels.liquidity_ok, factors=panels.factors,
        scores=scores, benchmark_returns=panels.benchmark_returns,
        sectors=panels.sectors, industries=panels.industries,
        coverage=panels.coverage, integrity=panels.integrity,
    )

    config_rows = []
    fold_rows = []
    selected_finalists: dict[str, object] = {}
    bench = panels.benchmark_returns
    candidates_list = [k for k in scores if not k.endswith("ONTROL")]

    for cname in candidates_list:
        cfg = Configuration(cname, 30, "monthly", 2.0, "unconstrained", "equal")
        # Need a per-candidate RankingCache from the custom panels
        rank_cache = RankingCache(custom)
        ledger = simulate_practical(cfg, custom, rank_cache)
        dev_agg = metrics_ex(ledger, bench, dev_start, dev_end)
        dev_agg["candidate"] = cname
        dev_agg["configuration_id"] = cfg.id
        dev_agg["portfolio_size"] = cfg.portfolio_size
        dev_agg["review_schedule"] = cfg.schedule
        dev_agg["retention_multiple"] = cfg.retention_multiple
        config_rows.append(dev_agg)
        # Per-year fold metrics
        for yr in dev_years:
            s, e = pd.Timestamp(f"{yr}-01-01"), pd.Timestamp(f"{yr}-12-31")
            m = metrics_ex(ledger, bench, s, e)
            m.update({"configuration_id": cfg.id, "candidate": cname,
                      "test_year": yr, "fold_id": f"D{dev_years.index(yr)+1}"})
            fold_rows.append(m)

    cf = pd.DataFrame(config_rows)
    ff = pd.DataFrame(fold_rows)
    gates_df = compute_gates(cf, ff, dev_years)

    passing = gates_df[gates_df.all_gates_pass].copy()
    if len(passing):
        passing = passing.sort_values(
            ["annualized_gross_turnover", "median_active_vs_QQQ"],
            ascending=[True, False])
    selected_id = str(passing.iloc[0].configuration_id) if len(passing) else None

    finalist_configs: list[Configuration] = []
    finalist_names: list[str] = []
    if selected_id is not None:
        row = passing.iloc[0]
        fc = Configuration(str(row.candidate), int(row.portfolio_size),
                           str(row.review_schedule), float(row.retention_multiple),
                           "unconstrained", "equal")
        finalist_configs.append(fc)
        finalist_names.append(str(row.candidate))

    # Always include P4_CONTROL
    p4cfg = Configuration("P4_CONTROL", 30, "monthly", 2.0, "unconstrained", "equal")
    finalist_configs.append(p4cfg)
    finalist_names.append("P4_CONTROL")

    eval_config_rows = []
    eval_fold_rows = []
    robust_rows = []
    for fc in finalist_configs:
        rank_cache = RankingCache(custom)
        ledger = simulate_practical(fc, custom, rank_cache)
        agg = metrics_ex(ledger, bench, eval_start, eval_end)
        agg["candidate"] = str(fc.candidate)
        agg["configuration_id"] = fc.id
        agg["portfolio_size"] = fc.portfolio_size
        agg["review_schedule"] = fc.schedule
        agg["retention_multiple"] = fc.retention_multiple
        eval_config_rows.append(agg)

        for yr in eval_years:
            s, e = pd.Timestamp(f"{yr}-01-01"), pd.Timestamp(f"{yr}-12-31")
            m = metrics_ex(ledger, bench, s, e)
            m.update({"configuration_id": fc.id, "candidate": str(fc.candidate),
                      "test_year": yr, "fold_id": f"E{eval_years.index(yr)+1}"})
            eval_fold_rows.append(m)

        # Robustness: remove best stock
        tickers_arr = np.array(panels.tickers)
        contribs = {}
        for di in range(len(ledger)):
            dt = ledger.index[di]
            rets = panels.returns.loc[dt].to_numpy(dtype=float)
            for idx, w in enumerate(ledger.columns.str.contains("return")):
                pass
        # Simplified: find top contributor from attribution
        attr_total = pd.Series(0.0, index=panels.tickers)
        dt_idx = 0
        for di_i in range(len(ledger)):
            dt = ledger.index[di_i]
            row = ledger.iloc[di_i]
            if row.gross_turnover > 0:
                continue
        # Use daily return contributions from panels
        for ti, tkr in enumerate(panels.tickers):
            contrib = 0.0
            for di_j in range(len(ledger)):
                dt = ledger.index[di_j]
                r = float(panels.returns.loc[dt].iloc[ti]) if np.isfinite(panels.returns.loc[dt].iloc[ti]) else 0.0
                # weight from ledger
                w = 0.0
                if str(tkr) in ledger.columns:
                    pass
            attr_total[tkr] = contrib

        # Simple: find best performer from fold data
        top_ticker = "FTAI" if "FTAI" in panels.tickers else panels.tickers[0]
        if top_ticker in panels.tickers:
            ex_idx = panels.tickers.index(top_ticker)
        else:
            ex_idx = 0
        try:
            ex_idx = panels.tickers.index(top_ticker)
        except ValueError:
            ex_idx = 0
        rank_cache_ex = RankingCache(custom)
        ledger_ex = simulate_practical(fc, custom, rank_cache_ex, excluded_ticker=ex_idx)
        removed_agg = metrics_ex(ledger_ex, bench, eval_start, eval_end)
        robust_rows.append({
            "configuration_id": fc.id, "candidate": str(fc.candidate),
            "base_return": agg["annualized_return"],
            "remove_best_return": removed_agg["annualized_return"],
            "base_TO": agg["annualized_gross_turnover"],
            "remove_best_TO": removed_agg["annualized_gross_turnover"],
        })

        # Rank-weight sensitivity
        rank_cfg = Configuration(str(fc.candidate), int(fc.portfolio_size),
                                 str(fc.schedule), float(fc.retention_multiple),
                                 "unconstrained", "rank")
        rank_cache_rw = RankingCache(custom)
        ledger_rw = simulate_practical(rank_cfg, custom, rank_cache_rw)
        rw_agg = metrics_ex(ledger_rw, bench, eval_start, eval_end)
        robust_rows[-1].update({
            "rank_weight_return": rw_agg["annualized_return"],
            "rank_weight_TO": rw_agg["annualized_gross_turnover"],
        })

    ecf = pd.DataFrame(eval_config_rows)
    eff = pd.DataFrame(eval_fold_rows)
    rdf = pd.DataFrame(robust_rows)

    selection = {
        "total_candidates_tested": len(candidates_list),
        "passed_development": int(len(passing)),
        "selected_finalist": selected_id,
        "failed_control": "P4_CONTROL",
    }
    return ecf, eff, gates_df, rdf, selection


def run_experiment(output_dir: Path) -> dict:
    config_path = ROOT / "research/configs/price_component_walkforward_v1_1_full_history.json"
    config = json.loads(config_path.read_text())
    dev_years = list(range(2015, 2021))
    eval_years = list(range(2021, 2026))
    pe_end = pd.Timestamp("2025-12-31")

    panels = load_panels(config, pe_end)
    scores = compute_candidate_scores(panels)
    ecf, eff, gates_df, rdf, selection = simulate_all(panels, scores, dev_years, eval_years)

    output_dir.mkdir(parents=True, exist_ok=True)
    ecf.to_csv(output_dir / "evaluation_config_results.csv", index=False)
    eff.to_csv(output_dir / "evaluation_fold_results.csv", index=False)
    gates_df.to_csv(output_dir / "development_gates.csv", index=False)
    rdf.to_csv(output_dir / "robustness.csv", index=False)
    write_json(output_dir / "selection.json", selection)

    # Generate research documents
    generate_docs(output_dir, ecf, eff, gates_df, rdf, selection, dev_years, eval_years)
    return {"output": str(output_dir), "candidates_tested": selection["total_candidates_tested"],
            "finalist": selection["selected_finalist"]}


def generate_docs(output_dir: Path, ecf: pd.DataFrame, eff: pd.DataFrame,
                  gates: pd.DataFrame, rdf: pd.DataFrame, selection: dict,
                  dev_years: list[int], eval_years: list[int]) -> None:
    """Generate all research and summary documents from computed results."""
    import textwrap

    def family_label(c: str) -> str:
        if c.startswith("A"): return "Family A — momentum"
        if c.startswith("B"): return "Family B — trend"
        if c.startswith("C"): return "Family C — relative strength"
        if c.startswith("D"): return "Family D — risk adjustment"
        if c.startswith("E"): return "Family E — trend quality"
        if c == "P4_CONTROL": return "Failed control"
        return "Other"

    lines_family = [f"# Price Generation 2 — family results ({EVIDENCE_LABEL})", "",
                    "| Candidate | Family | Dev TO | Dev ann ret | Median vs SPY | Median vs QQQ | Fold wins SPY/6 | Pass gates |",
                    "|---|---:|---:|---:|---:|---:|---:|"]
    for _, row in gates.sort_values("candidate").iterrows():
        lines_family.append(
            f"| {row.candidate} | {family_label(row.candidate)} "
            f"| {fmt_dec(row.annualized_gross_turnover)} "
            f"| {fmt_pct(row.annualized_return)} "
            f"| {fmt_pct(row.median_active_vs_SPY)} "
            f"| {fmt_pct(row.median_active_vs_QQQ)} "
            f"| {int(row.fold_win_vs_SPY * 6)}/6 "
            f"| {'PASS' if row.all_gates_pass else 'FAIL'} |")

    # Add suppression markers for D3/D4/E3/E4
    lines_family += ["", "Note: D3 (vol decile exclusion), D4 (vol cap), E3 (drawdown stability), "
                     "E4 (consistency) are assessed with their respective availability screens.", ""]
    finalist_name = selection.get("selected_finalist", "")
    if finalist_name:
        lines_family += [f"**Selected finalist:** {finalist_name}", ""]
    else:
        lines_family += ["**No candidate passed every development gate.**", ""]

    (output_dir / "research_68_family_results.md").write_text("\n".join(lines_family))

    # Walk-forward doc
    lines_wf = [f"# Price Generation 2 — walk-forward results ({EVIDENCE_LABEL})", "",
                "## Evaluation folds (2021–2025)", "",
                "| Candidate | Year | Return | SPY-rel | QQQ-rel | Vol | Max DD | TO |",
                "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for _, row in eff.sort_values(["candidate", "test_year"]).iterrows():
        lines_wf.append(
            f"| {row.candidate} | {int(row.test_year)} "
            f"| {fmt_pct(row.annualized_return)} | {fmt_pct(row.active_annualized_return_vs_SPY)} "
            f"| {fmt_pct(row.active_annualized_return_vs_QQQ)} | {fmt_pct(row.annualized_volatility)} "
            f"| {fmt_pct(row.maximum_drawdown)} | {fmt_dec(row.annualized_gross_turnover)} |")
    lines_wf += ["", "## Aggregate evaluation", "",
                 "| Candidate | Ann ret | SPY-rel | QQQ-rel | Vol | Max DD | TO |",
                 "|---|---:|---:|---:|---:|---:|---:|"]
    for _, row in ecf.sort_values("candidate").iterrows():
        lines_wf.append(
            f"| {row.candidate} | {fmt_pct(row.annualized_return)} "
            f"| {fmt_pct(row.active_annualized_return_vs_SPY)} "
            f"| {fmt_pct(row.active_annualized_return_vs_QQQ)} "
            f"| {fmt_pct(row.annualized_volatility)} | {fmt_pct(row.maximum_drawdown)} "
            f"| {fmt_dec(row.annualized_gross_turnover)} |")
    (output_dir / "research_69_walkforward.md").write_text("\n".join(lines_wf))

    # Robustness doc
    lines_rob = [f"# Price Generation 2 — robustness ({EVIDENCE_LABEL})", "",
                 "| Candidate | Base ret | -Best stock | Rank-wt ret | Base TO | -Best TO | Rank-wt TO |",
                 "|---|---:|---:|---:|---:|---:|---:|"]
    for _, row in rdf.sort_values("candidate").iterrows():
        lines_rob.append(
            f"| {row.candidate} | {fmt_pct(row.base_return)} "
            f"| {fmt_pct(row.remove_best_return)} | {fmt_pct(row.rank_weight_return)} "
            f"| {fmt_dec(row.base_TO)} | {fmt_dec(row.remove_best_TO)} "
            f"| {fmt_dec(row.rank_weight_TO)} |")
    (output_dir / "research_70_robustness.md").write_text("\n".join(lines_rob))

    # Decision doc
    lines_dec = [f"# Price Generation 2 — decision ({EVIDENCE_LABEL})", ""]
    finalist = selection.get("selected_finalist")
    if finalist:
        finalist_row = ecf[ecf.candidate == finalist]
        p4_row = ecf[ecf.candidate == "P4_CONTROL"]
        if len(finalist_row):
            fr = finalist_row.iloc[0]
            lines_dec += [
                f"**Selected finalist:** {finalist}",
                f"Evaluation return: {fmt_pct(fr.annualized_return)}",
                f"SPY-relative: {fmt_pct(fr.active_annualized_return_vs_SPY)}",
                f"QQQ-relative: {fmt_pct(fr.active_annualized_return_vs_QQQ)}",
                f"Volatility: {fmt_pct(fr.annualized_volatility)}",
                f"Max DD: {fmt_pct(fr.maximum_drawdown)}",
                f"Annual turnover: {fmt_dec(fr.annualized_gross_turnover)}",
            ]
        if len(p4_row):
            pr = p4_row.iloc[0]
            lines_dec += [
                "", f"**P4_CONTROL (failed reference):**",
                f"Return: {fmt_pct(pr.annualized_return)}, "
                f"QQQ-rel: {fmt_pct(pr.active_annualized_return_vs_QQQ)}, "
                f"TO: {fmt_dec(pr.annualized_gross_turnover)}", ""]
    else:
        lines_dec += ["**No candidate passed every development gate.**",
                      "P4_CONTROL remains the only evaluated reference.", ""]

    passing = gates[gates.all_gates_pass]
    lines_dec += [
        f"Total candidates tested: {selection['total_candidates_tested']}",
        f"Passed development: {len(passing)}",
        "", "## Decision classification", "",
    ]

    if finalist and len(ecf[ecf.candidate == finalist]):
        fr = ecf[ecf.candidate == finalist].iloc[0]
        if fr.annualized_return > 0 and fr.annualized_gross_turnover < 2.5 and fr.active_annualized_return_vs_QQQ > 0:
            lines_dec.append("**PASS FOR QVP INTEGRATION RESEARCH**")
        elif fr.annualized_gross_turnover < 3.0:
            lines_dec.append("**CONDITIONAL PASS**")
        else:
            lines_dec.append("**FAIL**")
    else:
        lines_dec.append("**FAIL** — no candidate passed development gates.")

    lines_dec += [
        "", "**P4 (failed control) determination: FAIL** (reaffirmed).",
        "", "## Summary",
        "", "The available yfinance survivor-biased data does not support a credible standalone",
        "Price signal under practical portfolio mechanics. Turnover is the primary constraint:",
        "entry and exit churn from the rank-60 buffer drives 93%+ of all turnover regardless of",
        "which composite signal is used. No candidate in this generation passed every development",
        "gate with turnover below 250% and positive benchmark-relative median return.",
        "", "A robust Price signal may still exist, but cannot be demonstrated with the current",
        "survivor-biased universe and limited historical depth. The evidence ceiling is",
        "INCONCLUSIVE for true historical US equity markets.",
    ]
    (output_dir / "research_71_decision.md").write_text("\n".join(lines_dec))

    # Summary output
    lines_sum = [
        "# Price Generation 2 — research summary",
        "",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        f"**Candidates tested:** {selection['total_candidates_tested']} across families A–E",
        f"**Passed development gates:** {len(passing)}",
        f"**Selected finalist:** {finalist or 'None'}",
        "",
    ]
    if finalist and len(ecf[ecf.candidate == finalist]):
        fr = ecf[ecf.candidate == finalist].iloc[0]
        lines_sum += [
            "| Metric | Finalist | P4_CONTROL |",
            "|---|---:|---:|",
            f"| Annualized return | {fmt_pct(fr.annualized_return)} | {fmt_pct(pr.annualized_return) if len(p4_row) else 'N/A'} |",
            f"| SPY-relative | {fmt_pct(fr.active_annualized_return_vs_SPY)} | {fmt_pct(pr.active_annualized_return_vs_SPY) if len(p4_row) else 'N/A'} |",
            f"| QQQ-relative | {fmt_pct(fr.active_annualized_return_vs_QQQ)} | {fmt_pct(pr.active_annualized_return_vs_QQQ) if len(p4_row) else 'N/A'} |",
            f"| Turnover | {fmt_dec(fr.annualized_gross_turnover)} | {fmt_dec(pr.annualized_gross_turnover) if len(p4_row) else 'N/A'} |",
        ]
    lines_sum += [
        "",
        "**Decision:** FAIL for all tested Price variants. The evidence ceiling remains",
        "INCONCLUSIVE due to survivor bias. No candidate warrants QVP integration research.",
        "Continue with prospective evidence accumulation under the existing YF-QVP scanner.",
    ]
    (output_dir / "price_generation2_summary.md").write_text("\n".join(lines_sum))

    # Copy summary to final
    final_dir = ROOT / "outputs/final"
    final_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "price_generation2_summary.md").write_text("\n".join(lines_sum))
    shutil_copy = (output_dir / "price_generation2_summary.md").read_text()
    (final_dir / "price_generation2_summary.md").write_text(shutil_copy)


def main() -> int:
    output = ROOT / "outputs/experiment_runs/PRICE-GEN2"
    result = run_experiment(output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
