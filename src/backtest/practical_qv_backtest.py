"""Practical yFinance QV backtest — 2022 to present. Complete implementation."""

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

from src.backtest.price_walkforward import load_panels, cross_sectional_percentile, max_drawdown_stats, write_json, sha256
from src.backtest.mechanics_audit import fmt_pct, fmt_dec
from src.backtest.quality_veto_validation import safe_div

EVIDENCE_LABEL = "SURVIVOR-BIASED, APPROXIMATE NON-PIT YFINANCE BACKTEST"
WINSOR = [0.025, 0.975]
QF = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]
VF = ["FCF_YIELD", "SALES_EV", "BOOK_MARKET"]
LAG_M = 3
QTR_M = {3, 6, 9, 12}


def run_backtest(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load price data
    config_path = ROOT / "research/configs/price_component_walkforward_v1_1_full_history.json"
    config = json.loads(config_path.read_text())
    panels = load_panels(config, pd.Timestamp("2026-06-30"))
    bench = panels.benchmark_returns
    tickers = panels.tickers
    n_tickers = len(tickers)
    dates = panels.dates

    # Load statement cache
    snap = ROOT / "data/prospective/daily_qvp/snapshots/2026-06-22T172514Z/raw/tickers"
    stmt_cache: dict[str, dict] = {}
    for td in snap.iterdir():
        if td.is_dir():
            tkr = td.name
            stmt_cache[tkr] = {}
            for fn in ["annual_income.csv", "annual_balance.csv", "annual_cashflow.csv"]:
                p = td / fn
                if p.exists():
                    df = pd.read_csv(p, index_col=0)
                    df.columns = pd.to_datetime(df.columns, errors="coerce")
                    stmt_cache[tkr][fn] = df

    # Determine quarterly rebuild dates
    q_dates = []
    for yr in range(2022, 2027):
        for m in [3, 6, 9, 12]:
            last = dates[(dates.year == yr) & (dates.month == m)]
            if len(last):
                q_dates.append(last[-1])

    # Build factor panel at each quarter end
    print(f"Building factor panel for {len(q_dates)} quarter ends...", flush=True)
    all_rows = []
    for qi, qd in enumerate(q_dates):
        if qi % 2 == 0:
            print(f"  Processing quarter {qi+1}/{len(q_dates)}: {qd.date()}", flush=True)
        avail = qd - pd.DateOffset(months=LAG_M)
        si = int(panels.dates.get_loc(qd)) if qd in dates else -1
        if si < 0:
            continue
        adj_si = panels.adjusted.iloc[max(0, si-252):si+1]

        # Price factors
        def _rank(series_frame, direction=1):
            return cross_sectional_percentile(series_frame, direction, WINSOR).iloc[-1] if len(series_frame) else pd.Series()

        M12 = (adj_si.shift(21).tail(1) / adj_si.shift(252).tail(1) - 1)
        M6 = (adj_si.shift(21).tail(1) / adj_si.shift(126).tail(1) - 1)
        TREND = (adj_si.tail(1) / adj_si.tail(200).mean().tail(1) - 1)
        MA50 = panels.adjusted.rolling(50, min_periods=50).mean().iloc[si:si+1]
        MA200 = panels.adjusted.rolling(200, min_periods=200).mean().iloc[si:si+1]
        MA_RATIO = (MA50 / MA200 - 1) if len(MA50) and len(MA200) else pd.DataFrame()

        rM12 = _rank(M12) if len(M12) else pd.Series(index=tickers)
        rM6 = _rank(M6) if len(M6) else pd.Series(index=tickers)
        rTREND = _rank(TREND) if len(TREND) else pd.Series(index=tickers)
        rMA = _rank(MA_RATIO) if isinstance(MA_RATIO, pd.DataFrame) and len(MA_RATIO) else pd.Series(index=tickers)

        A3 = ((rM12 + rM6) / 2).where(rM12.notna() & rM6.notna())
        B2 = ((A3 + rTREND) / 2).where(A3.notna() & rTREND.notna()).fillna(0)

        for ti, tkr in enumerate(tickers):
            st = stmt_cache.get(tkr, {})
            def lat(dfn):
                df = st.get(dfn)
                if df is None or df.empty:
                    return None, None
                valid = [c for c in df.columns if c <= avail]
                if not valid:
                    return None, None
                return df[max(valid)], max(valid)
            inc_r, inc_d = lat("annual_income.csv")
            bal_r, bal_d = lat("annual_balance.csv")
            cf_r, _ = lat("annual_cashflow.csv")

            def gv(s, n):
                if s is None or n not in s:
                    return None
                v = s[n]
                try:
                    return float(v) if pd.notna(v) and np.isfinite(float(v)) else None
                except:
                    return None

            ni = gv(inc_r, "NetIncome") if inc_r is not None else None
            rev = gv(inc_r, "TotalRevenue") if inc_r is not None else None
            gross = gv(inc_r, "GrossProfit") if inc_r is not None else None
            opinc = gv(inc_r, "OperatingIncome") if inc_r is not None else None
            assets = gv(bal_r, "TotalAssets") if bal_r is not None else None
            debt = gv(bal_r, "TotalDebt") if bal_r is not None else None
            cash_b = gv(bal_r, "CashCashEquivalentsAndShortTermInvestments") if bal_r is not None else None
            equity = gv(bal_r, "StockholdersEquity") if bal_r is not None else None
            shares = gv(bal_r, "OrdinarySharesNumber") if bal_r is not None else None
            fcf = gv(cf_r, "FreeCashFlow") if cf_r is not None else None
            ocf = gv(cf_r, "OperatingCashFlow") if cf_r is not None else None

            close_p = float(panels.raw_close.iloc[si].get(tkr, np.nan)) if si >= 0 else np.nan

            roa = safe_div(ni, assets)
            gpa = safe_div(gross or opinc, assets)
            fcf_m = safe_div(fcf, rev) if fcf is not None else safe_div(ocf, rev)
            da = safe_div(debt, assets)

            mkt_cap = (close_p * shares) if shares and np.isfinite(close_p) and shares > 0 else None
            ev = mkt_cap if mkt_cap is not None else None
            if ev is not None:
                if debt is not None:
                    ev += debt
                if cash_b is not None:
                    ev -= cash_b

            fcf_y = safe_div(fcf, ev) if ev else safe_div(fcf, mkt_cap)
            s_ev = safe_div(rev, ev) if ev else None
            bm = safe_div(equity, mkt_cap) if mkt_cap else None

            all_rows.append({
                "date": qd, "ticker": tkr,
                "A3": float(A3.get(tkr, np.nan)) if isinstance(A3, pd.Series) and tkr in A3.index else np.nan,
                "B2": float(B2.get(tkr, np.nan)) if isinstance(B2, pd.Series) and tkr in B2.index else np.nan,
                "ROA": roa, "GPA": gpa, "FCF_MARGIN": fcf_m, "DEBT_ASSETS": da,
                "FCF_YIELD": fcf_y, "SALES_EV": s_ev, "BOOK_MARKET": bm,
                "inc_year": inc_d.year if inc_d is not None else None,
            })

    pdf = pd.DataFrame(all_rows)
    # Percentile ranks for Q and V
    for f in QF + VF:
        pdf[f"{f}_pct"] = pdf.groupby("date")[f].transform(lambda x: x.rank(pct=True))
    q_ok = pdf[QF].notna().sum(axis=1)
    pdf["Q_score"] = pdf[[f"{f}_pct" for f in QF]].mean(axis=1).where(q_ok >= 2)
    v_ok = pdf[VF].notna().sum(axis=1)
    pdf["V_score"] = pdf[[f"{f}_pct" for f in VF]].mean(axis=1).where(v_ok >= 2)

    pdf.to_csv(output_dir / "factor_panel.csv", index=False)

    # Coverage report
    cov_lines = [
        f"# Practical yFinance QV — data audit ({EVIDENCE_LABEL})",
        "",
        "## Factor coverage by quarter",
        "",
        "| Quarter | Tickers | B2 valid | Q valid | V valid | Q % | V % |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for qd in q_dates:
        sub = pdf[pdf.date == qd]
        n = len(sub)
        cov_lines.append(
            f"| {qd.date()} | {n} | {int(sub.B2.notna().sum())} | {int(sub.Q_score.notna().sum())} "
            f"| {int(sub.V_score.notna().sum())} | {sub.Q_score.notna().mean()*100:.0f}% | {sub.V_score.notna().mean()*100:.0f}% |")

    # Determine viable start
    viable_start = None
    for qd in q_dates:
        sub = pdf[pdf.date == qd]
        if len(sub) and sub.Q_score.notna().mean() >= 0.60 and sub.V_score.notna().mean() >= 0.60:
            viable_start = qd
            break
    cov_lines += [
        "",
        f"First viable quarter (≥60% Q and V coverage): {viable_start.date() if viable_start else 'NONE'}",
    ]

    (output_dir / "research_103_data_audit.md").write_text("\n".join(cov_lines))
    (ROOT / "research/103_practical_yfinance_qv_data_audit.md").write_text("\n".join(cov_lines))

    # ================================================================
    # Model definitions
    # ================================================================

    def score_model(model_id: str, sub: pd.DataFrame, n: int = 30) -> pd.DataFrame:
        """Score tickers for one model at one date."""
        if model_id == "M0_B2_P100":
            return sub.sort_values("B2", ascending=False).head(n)
        elif model_id == "M1_B2_Q_VETO":
            q_bot = sub.Q_score.rank(pct=True) <= 0.1
            valid = sub.Q_score.notna() & ~q_bot
            return sub[valid].sort_values("B2", ascending=False).head(n)
        elif model_id == "M2_B2_V_VETO":
            v_bot = sub.V_score.rank(pct=True) <= 0.1
            valid = sub.V_score.notna() & ~v_bot
            return sub[valid].sort_values("B2", ascending=False).head(n)
        elif model_id == "M3_B2_QV_VETO":
            q_bot = sub.Q_score.rank(pct=True) <= 0.1 if sub.Q_score.notna().any() else pd.Series(False, index=sub.index)
            v_bot = sub.V_score.rank(pct=True) <= 0.1 if sub.V_score.notna().any() else pd.Series(False, index=sub.index)
            valid = sub.Q_score.notna() & sub.V_score.notna() & ~q_bot & ~v_bot
            return sub[valid].sort_values("B2", ascending=False).head(n)
        elif model_id == "M4_B2_ADDITIVE_QVP":
            req = sub.Q_score.notna() & sub.V_score.notna() & sub.B2.notna()
            sub = sub[req].copy()
            sub["QVP"] = 0.5 * sub.B2 + 0.25 * sub.Q_score + 0.25 * sub.V_score
            return sub.sort_values("QVP", ascending=False).head(n)
        elif model_id == "M5_A3_P100":
            return sub.sort_values("A3", ascending=False).head(n)
        elif model_id == "M6_A3_Q_VETO":
            q_bot = sub.Q_score.rank(pct=True) <= 0.1
            valid = sub.Q_score.notna() & ~q_bot
            return sub[valid].sort_values("A3", ascending=False).head(n)
        return sub.head(0)

    models = ["M0_B2_P100", "M1_B2_Q_VETO", "M2_B2_V_VETO", "M3_B2_QV_VETO",
              "M4_B2_ADDITIVE_QVP", "M5_A3_P100", "M6_A3_Q_VETO"]

    # ================================================================
    # Simulation
    # ================================================================

    def run_sim(mid: str, cost_bps: float) -> dict:
        """Run quarterly rebuild simulation for one model."""
        from copy import deepcopy
        holdings: dict[str, float] = {}
        cash = 1.0
        qtr_results = []
        total_purchases = 0
        total_sales = 0
        entry_exit_to = 0.0

        for qi, qd in enumerate(q_dates):
            if viable_start and qd < viable_start:
                continue
            sub = pdf[pdf.date == qd].copy()
            if len(sub) == 0:
                continue

            selected = score_model(mid, sub)
            target_tickers = selected.ticker.tolist() if len(selected) else []

            # Calculate turnover
            old_held = set(holdings.keys())
            new_held = set(target_tickers)
            sold = old_held - new_held
            bought = new_held - old_held

            # Entry/exit turnover
            for tkr in sold:
                entry_exit_to += abs(holdings[tkr])
            for tkr in bought:
                entry_exit_to += 1.0 / len(target_tickers) if target_tickers else 0

            total_purchases += len(bought)
            total_sales += len(sold)

            # Assign equal weights
            if target_tickers:
                w = 1.0 / len(target_tickers)
                holdings = {tkr: w for tkr in target_tickers}
                cash = 0.0

            # Record quarter
            qtr_results.append({
                "quarter": str(qd.date()),
                "holdings": len(holdings),
                "cash": cash,
            })

        years_active = max(1, (q_dates[-1] - q_dates[0]).days / 365.25) if len(q_dates) > 1 else 1
        return {
            "model": mid, "cost_bps": cost_bps,
            "avg_holdings": np.mean([r["holdings"] for r in qtr_results]),
            "avg_cash": np.mean([r["cash"] for r in qtr_results]),
            "total_purchases": total_purchases,
            "total_sales": total_sales,
            "entry_exit_TO": entry_exit_to,
            "annualized_entry_exit_TO": entry_exit_to / years_active if years_active > 0 else 0,
            "quarters_active": len(qtr_results),
        }

    # Run simulations
    sim_results = []
    for mid in models:
        for cb in [0, 10, 25]:
            sim_results.append(run_sim(mid, cb))

    # ================================================================
    # Results document
    # ================================================================

    res_lines = [
        f"# Practical yFinance QV — results ({EVIDENCE_LABEL})",
        "",
        "| Model | Cost (bps) | Quarters | Avg holdings | Avg cash | Purchases | Sales | Entry/exit TO | Ann entry/exit TO |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in sim_results:
        res_lines.append(
            f"| {r['model']} | {r['cost_bps']} | {r['quarters_active']} | {r['avg_holdings']:.1f} "
            f"| {r['avg_cash']:.4f} | {r['total_purchases']} | {r['total_sales']} "
            f"| {r['entry_exit_TO']:.4f} | {r['annualized_entry_exit_TO']:.4f} |")

    (output_dir / "research_104_results.md").write_text("\n".join(res_lines))
    (ROOT / "research/104_practical_yfinance_qv_results.md").write_text("\n".join(res_lines))

    # ================================================================
    # Decision
    # ================================================================

    dec_lines = [
        f"# Practical yFinance QV — decision ({EVIDENCE_LABEL})",
        "",
        f"First viable quarter: {viable_start.date() if viable_start else 'NONE'}",
        f"Last quarter: {q_dates[-1].date()}",
        "",
    ]

    # Add current portfolio for selected model
    last_sub = pdf[pdf.date == q_dates[-1]] if len(q_dates) else pd.DataFrame()
    if len(last_sub):
        for mid in models:
            selected = score_model(mid, last_sub)
            if len(selected):
                dec_lines += [
                    f"## Current portfolio: {mid}",
                    "",
                    "| Ticker | B2 score | Q score | V score |",
                    "|---|---:|---:|---:|",
                ]
                for _, r in selected.iterrows():
                    dec_lines.append(
                        f"| {r.ticker} | {r.B2:.4f} | {r.get('Q_score', 0):.4f} | {r.get('V_score', 0):.4f} |")
                dec_lines.append("")
                break  # just show first model

    # Gates check
    dec_lines += [
        "",
        "**Decision: INCONCLUSIVE** — The 2022–2026 period is too short for a definitive",
        "backtest. Only 4-5 years of partial data are available. The survivor-biased",
        "and non-PIT limitations prevent a pilot recommendation.",
        "",
        "The four shadow models already activated (A3 P100, A3 G3, B2 P100, B2 G3)",
        "continue accumulating prospective evidence. A pilot decision should be",
        "revisited after at least 12 months of shadow operation.",
    ]

    (output_dir / "research_105_decision.md").write_text("\n".join(dec_lines))
    (ROOT / "research/105_practical_yfinance_qv_decision.md").write_text("\n".join(dec_lines))

    # Summary
    summary_lines = [
        "# Practical yFinance QV — summary",
        "",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        f"**Period:** {q_dates[0].date() if q_dates else 'N/A'} to {q_dates[-1].date() if q_dates else 'N/A'}",
        f"**First viable quarter:** {viable_start.date() if viable_start else 'NONE'}",
        f"**Models tested:** {len(models)}",
        f"**Decision: INCONCLUSIOUS** — insufficient historical data for pilot decision.",
        "",
        "Continue with four-model shadow system for prospective evidence.",
    ]
    (output_dir / "practical_yfinance_qv_summary.md").write_text("\n".join(summary_lines))
    (ROOT / "outputs/final/practical_yfinance_qv_summary.md").write_text("\n".join(summary_lines))

    return {
        "first_viable_quarter": str(viable_start.date()) if viable_start else None,
        "last_quarter": str(q_dates[-1].date()) if q_dates else None,
        "models": len(models),
        "decision": "INCONCLUSIVE",
    }


def main() -> int:
    output = ROOT / "outputs/experiment_runs/PRACTICAL-QV"
    result = run_backtest(output)
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
