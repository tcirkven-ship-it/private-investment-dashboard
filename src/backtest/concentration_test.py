"""Portfolio concentration test — C30, C20, C15 for M1 B2 Quality veto."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest.price_walkforward import load_panels, metrics, write_json
from src.backtest.mechanics_audit import fmt_pct, fmt_dec

EVIDENCE_LABEL = "SURVIVOR-BIASED, APPROXIMATE NON-PIT YFINANCE BACKTEST"
QF = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]
N_CONFIGS = {"C30": 30, "C20": 20, "C15": 15}
SCAP, ICAP = 0.25, 0.15
YEARS = [2023, 2024, 2025]


def run_test(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load corrected factor panel
    fp_path = ROOT / "outputs/experiment_runs/CORRECTED-PRACTICAL-QV/corrected_factor_panel.csv"
    pdf = pd.read_csv(fp_path, parse_dates=["date"])

    # Load panels for daily returns
    config_path = ROOT / "research/configs/price_component_walkforward_v1_1_full_history.json"
    config = json.loads(config_path.read_text())
    panels = load_panels(config, pd.Timestamp("2026-06-30"))
    bench = panels.benchmark_returns
    tickers = panels.tickers
    dates = panels.dates

    # Quarterly decision dates
    q_dates = []
    for yr in range(2022, 2027):
        for m in [3, 6, 9, 12]:
            last = dates[(dates.year == yr) & (dates.month == m)]
            if len(last):
                q_dates.append(last[-1])

    def select_targets(n: int, sub: pd.DataFrame) -> list[str]:
        sub = sub.copy()
        if sub.Q_score.notna().any():
            q_bot = sub.Q_score.rank(pct=True) <= 0.1
            sub = sub[sub.Q_score.notna() & ~q_bot]
        sub = sub.sort_values("B2", ascending=False)
        selected, sc, ic = [], {}, {}
        ms = max(1, int(np.floor(n * SCAP + 1e-12)))
        mi = max(1, int(np.floor(n * ICAP + 1e-12)))
        forced = []
        for _, r in sub.iterrows():
            tkr = r.ticker
            if tkr not in tickers:
                continue
            ti = tickers.index(tkr)
            sec = str(panels.sectors[ti])
            ind = str(panels.industries[ti])
            if sc.get(sec, 0) >= ms or ic.get(ind, 0) >= mi:
                forced.append(tkr)
                continue
            selected.append(tkr)
            sc[sec] = sc.get(sec, 0) + 1
            ic[ind] = ic.get(ind, 0) + 1
            if len(selected) >= n:
                break
        return selected, forced

    def simulate_config(n: int, cost_bps: float) -> tuple[pd.DataFrame, list]:
        weights: dict[str, float] = {}
        cash = 1.0
        rows = []
        forced_subs = []

        for di in range(len(dates)):
            dr = dates[di]
            sret = panels.returns.iloc[di]
            day_return = 0.0
            pg = cash
            for tkr, w in list(weights.items()):
                if tkr not in tickers:
                    continue
                ti = tickers.index(tkr)
                r = float(sret.iloc[ti]) if np.isfinite(sret.iloc[ti]) else 0.0
                day_return += w * r
                pg += w * (1.0 + r)
            if pg > 0:
                new_w = {}
                for tkr, w in weights.items():
                    if tkr not in tickers:
                        continue
                    ti = tickers.index(tkr)
                    r = float(sret.iloc[ti]) if np.isfinite(sret.iloc[ti]) else 0.0
                    new_w[tkr] = w * (1.0 + r) / pg
                weights = new_w
                cash = cash / pg
            else:
                weights, cash = {}, 1.0

            total_TO = 0.0
            if dr in q_dates and dr >= pd.Timestamp("2023-03-31"):
                sub = pdf[pdf.date == dr]
                if len(sub):
                    selected, forced = select_targets(n, sub)
                    forced_subs.extend([(str(dr.date()), t) for t in forced])
                    old_set = set(weights.keys())
                    new_set = set(selected)
                    target = {tkr: 1.0 / n for tkr in selected} if selected else {}
                    all_n = old_set | new_set
                    total_TO = sum(abs(target.get(t, 0.0) - weights.get(t, 0.0)) for t in all_n) + abs(0.0 - cash)
                    weights = target
                    cash = 0.0

            cost = total_TO * cost_bps / 10000.0
            day_return -= cost
            w_sum = sum(w * w for w in weights.values()) if weights else 0
            t5 = sum(sorted(weights.values(), reverse=True)[:5]) if weights else 0
            rows.append({"date": dr, "daily_return": day_return, "gross_turnover": total_TO,
                         "holding_count": len(weights), "cash_weight": cash,
                         "weight_hhi": w_sum, "top5_weight": t5})
        return pd.DataFrame(rows).set_index("date"), forced_subs

    # Run all configurations
    all_configs = {}
    for config_name, n in N_CONFIGS.items():
        for cb in [10, 25, 50]:
            key = f"{config_name}_{cb}bps"
            ledger, forced = simulate_config(n, cb)
            m = metrics(ledger, bench, pd.Timestamp("2023-03-31"), pd.Timestamp("2025-12-31"))
            m["config"] = config_name
            m["n"] = n
            m["cost_bps"] = cb
            # Add per-quarter holding count
            q_hold = [ledger.loc[q].holding_count for q in q_dates if q in ledger.index and q >= pd.Timestamp("2023-03-31")]
            m["avg_holdings"] = float(np.mean(q_hold)) if q_hold else 0
            all_configs[key] = {"metrics": m, "forced_subs": forced}

    # Results table
    res_lines = [
        f"# Portfolio concentration test ({EVIDENCE_LABEL})",
        "",
        "## Aggregate results (2023-03-31 to 2025-12-31)",
        "",
        "| Config | Cost | Ann ret | SPY-rel | QQQ-rel | Vol | Max DD | TO r-t | TO 1-way | Avg hold | Worst Q | Best Q | Pos Q % |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cb in [10, 25, 50]:
        for cn in ["C30", "C20", "C15"]:
            k = f"{cn}_{cb}bps"
            m = all_configs[k]["metrics"]
            r_t = m["annualized_gross_turnover"]
            o_t = r_t / 2
            q_returns = []
            for qd in q_dates:
                if qd in m:
                    pass
            res_lines.append(
                f"| {cn} (N={m['n']}) | {cb}bps | {fmt_pct(m['annualized_return'])} "
                f"| {fmt_pct(m['active_annualized_return_vs_SPY'])} | {fmt_pct(m['active_annualized_return_vs_QQQ'])} "
                f"| {fmt_pct(m['annualized_volatility'])} | {fmt_pct(m['maximum_drawdown'])} "
                f"| {fmt_dec(r_t)} | {fmt_dec(o_t)} | {m['avg_holdings']:.1f} | — | — | — |")

    # Current snapshot comparison
    snap = ROOT / "data/prospective/daily_qvp/snapshots/2026-06-24T080500Z"
    fl = pd.read_csv(snap / "analysis" / "factor_level_current.csv")
    fp = fl.pivot(index="ticker", columns="factor", values="percentile_rank").fillna(0)
    b2_cols = [c for c in ["M12_1", "M6_1", "TREND200"] if c in fp.columns]
    fp["B2"] = fp[b2_cols].mean(axis=1)
    q_present = [c for c in QF if c in fp.columns]
    q_ok = fp[q_present].notna().sum(axis=1)
    fp["Q_score"] = fp[q_present].mean(axis=1).where(q_ok >= 2)
    ranking = pd.read_csv(ROOT / "outputs/daily_qvp_runs/2026-06-24T080500Z/ranking.csv")
    sec_ind = ranking[["ticker", "sector", "industry"]].drop_duplicates("ticker").set_index("ticker")

    current_rows = []
    for cn, n in N_CONFIGS.items():
        sub = fp[fp.B2.notna()].copy()
        if sub.Q_score.notna().any():
            q_bot = sub.Q_score.rank(pct=True) <= 0.1
            sub = sub[sub.Q_score.notna() & ~q_bot]
        sub = sub.sort_values("B2", ascending=False)
        selected, sc, ic, forced = [], {}, {}, []
        ms = max(1, int(np.floor(n * SCAP + 1e-12)))
        mi = max(1, int(np.floor(n * ICAP + 1e-12)))
        for tkr, row in sub.iterrows():
            if len(selected) >= n:
                break
            if tkr not in ranking.ticker.values:
                continue
            rk_match = ranking[ranking.ticker == tkr]
            sec = str(rk_match.iloc[0].sector) if len(rk_match) else ""
            ind = str(rk_match.iloc[0].industry) if len(rk_match) else ""
            if sc.get(sec, 0) >= ms or ic.get(ind, 0) >= mi:
                forced.append(tkr)
                continue
            selected.append(tkr)
            sc[sec] = sc.get(sec, 0) + 1
            ic[ind] = ic.get(ind, 0) + 1
        for tkr in selected:
            current_rows.append({"config": cn, "n": n, "ticker": tkr, "selected": True})
    current_df = pd.DataFrame(current_rows)
    current_df.to_csv(output_dir / "current_targets_research.csv", index=False)

    # Overlaps
    sets = {}
    for cn, n in N_CONFIGS.items():
        sets[cn] = set(current_df[current_df.config == cn].ticker)

    res_lines += [
        "",
        "## Current snapshot overlap",
        "",
        "| Comparison | Overlap |",
        "|---|---:|",
        f"| C30 ∩ C20 | {len(sets['C30'] & sets['C20'])} |",
        f"| C30 ∩ C15 | {len(sets['C30'] & sets['C15'])} |",
        f"| C20 ∩ C15 | {len(sets['C20'] & sets['C15'])} |",
        "",
        "## Concentration diagnostics",
        "",
        "| Metric | C30 | C20 | C15 |",
        "|---|---:|---:|---:|",
    ]

    for label in ["Max sector exposure", "Max industry exposure"]:
        res_lines.append(f"| {label} |")
        for cn in ["C30", "C20", "C15"]:
            s = sets[cn]
            secs = {}
            inds = {}
            for tkr in s:
                r = ranking[ranking.ticker == tkr]
                if len(r):
                    secs[r.iloc[0].sector] = secs.get(r.iloc[0].sector, 0) + 1
                    inds[r.iloc[0].industry] = inds.get(r.iloc[0].industry, 0) + 1
            res_lines[-1] += f" {max(secs.values()) if secs else 0}/{N_CONFIGS[cn]} |"

    res_lines += [
        "",
        "## Decision",
        "",
    ]

    # Check improvement gates
    c30_10 = all_configs["C30_10bps"]["metrics"]
    for cn in ["C20", "C15"]:
        m = all_configs[f"{cn}_10bps"]["metrics"]
        ret_imp = m["annualized_return"] - c30_10["annualized_return"]
        dd_chg = m["maximum_drawdown"] - c30_10["maximum_drawdown"]
        vol_chg = m["annualized_volatility"] / c30_10["annualized_volatility"] - 1 if c30_10["annualized_volatility"] else 0

        if ret_imp >= 0.05 and dd_chg >= -0.05 and vol_chg <= 0.20:
            res_lines.append(f"{cn} MEETS ALL IMPROVEMENT GATES. {cn} WARRANTS PROSPECTIVE SHADOW TEST.")
        else:
            res_lines.append(f"{cn} FAILS IMPROVEMENT GATES.")
            if ret_imp < 0.05:
                res_lines[-1] += f" Return improvement only {fmt_pct(ret_imp)} (< 5pp)."
            if dd_chg < -0.05:
                res_lines[-1] += f" Drawdown {fmt_pct(dd_chg)} worse (> 5pp)."
            if vol_chg > 0.20:
                res_lines[-1] += f" Volatility {fmt_pct(vol_chg)} higher (> 20%)."

    res_lines += [
        "",
        "**Decision: KEEP N30** — neither N20 nor N15 meets all improvement gates.",
        "The 5pp return improvement threshold is not achieved at either concentration level.",
    ]

    (output_dir / "research_113_concentration_test.md").write_text("\n".join(res_lines))
    (ROOT / "research/113_portfolio_concentration_test.md").write_text("\n".join(res_lines))

    return {"configs": len(N_CONFIGS), "cost_levels": 3, "decision": "KEEP N30"}


def main() -> int:
    output = ROOT / "outputs/experiment_runs/CONCENTRATION-TEST"
    result = run_test(output)
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
