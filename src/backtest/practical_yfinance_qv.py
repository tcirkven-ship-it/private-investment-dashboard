"""Practical yFinance QV backtest — 2022 to present. All-in-one implementation."""

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
    load_panels, cross_sectional_percentile, max_drawdown_stats,
    write_json,
)
from src.backtest.mechanics_audit import fmt_pct, fmt_dec

EVIDENCE_LABEL = "SURVIVOR-BIASED, APPROXIMATE NON-PIT YFINANCE BACKTEST"
WINSOR = [0.025, 0.975]
PUBLICATION_LAG_M = 3
QF = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]
VF = ["FCF_YIELD", "SALES_EV", "BOOK_MARKET"]


def safe_div(n, d):
    if n is None or d is None or d == 0:
        return None
    return float(n) / float(d)


# ============================================================
# Part 1 — Historical data panel
# ============================================================

def build_historical_panel(panels, stmt_cache: dict, score_dates: list[pd.Timestamp]
                          ) -> tuple[pd.DataFrame, dict]:
    """Build complete factor panel for all score dates."""
    rows = []
    adj = panels.adjusted
    close = panels.raw_close

    for sd in score_dates:
        sd_ts = pd.Timestamp(sd)
        si = panels.dates.get_loc(sd_ts) if sd_ts in panels.dates else None
        if si is None:
            continue
        avail = sd_ts - pd.DateOffset(months=PUBLICATION_LAG_M)

        # Price factors at this date
        adj_sd = adj.iloc[si]
        M12_r = cross_sectional_percentile(
            (adj.shift(21) / adj.shift(252) - 1).iloc[si:si+1], 1, WINSOR).iloc[0]
        M6_r = cross_sectional_percentile(
            (adj.shift(21) / adj.shift(126) - 1).iloc[si:si+1], 1, WINSOR).iloc[0]
        TREND_r = cross_sectional_percentile(
            (adj / adj.rolling(200, min_periods=200).mean() - 1).iloc[si:si+1], 1, WINSOR).iloc[0]
        MA50 = adj.rolling(50, min_periods=50).mean().iloc[si]
        MA200 = adj.rolling(200, min_periods=200).mean().iloc[si]
        MA50_200_r = cross_sectional_percentile(
            (MA50 / MA200 - 1).to_frame().T, 1, WINSOR).iloc[0]

        for ticker in panels.tickers:
            ti = panels.tickers.index(ticker)
            p12 = M12_r.get(ticker, np.nan)
            p6 = M6_r.get(ticker, np.nan)
            A3 = np.nanmean([p12, p6]) if np.isfinite(p12) and np.isfinite(p6) else np.nan
            tr = TREND_r.get(ticker, np.nan)
            B2 = np.nanmean([A3, tr]) if np.isfinite(A3) and np.isfinite(tr) else np.nan

            # Quality from statements
            st = stmt_cache.get(ticker, {})
            def _latest(df_name):
                df = st.get(df_name)
                if df is None or df.empty:
                    return None
                valid = df.columns[df.columns <= avail]
                return df[valid[-1]] if len(valid) else None

            inc = _latest("annual_income.csv")
            bal = _latest("annual_balance.csv")
            cf = _latest("annual_cashflow.csv")
            close_p = close.iloc[si].get(ticker, np.nan)

            def gv(s, n):
                if s is None or n not in s.index:
                    return None
                v = s[n]
                try:
                    v = float(v) if pd.notna(v) else None
                    return v if np.isfinite(v) else None
                except:
                    return None

            ni = gv(inc, "NetIncome")
            rev = gv(inc, "TotalRevenue")
            gross = gv(inc, "GrossProfit")
            assets = gv(bal, "TotalAssets")
            debt = gv(bal, "TotalDebt")
            cash_bal = gv(bal, "CashCashEquivalentsAndShortTermInvestments")
            equity = gv(bal, "StockholdersEquity")
            fcf = gv(cf, "FreeCashFlow")
            shares = gv(bal, "OrdinarySharesNumber")

            roa = safe_div(ni, assets)
            gpa = safe_div(gross or gv(inc, "OperatingIncome"), assets)
            fcf_m = safe_div(fcf, rev)
            da = safe_div(debt, assets)

            # Value proxy
            mkt_cap = safe_div(close_p, shares) if shares and close_p and np.isfinite(close_p) else None
            # Actually mkt_cap = close_price * shares
            mkt_cap = close_p * shares if shares and np.isfinite(close_p) and shares > 0 else None
            ev = None
            if mkt_cap is not None:
                ev = mkt_cap
                if debt is not None:
                    ev += debt
                if cash_bal is not None:
                    ev -= cash_bal

            fcf_y = safe_div(fcf, ev) if ev else None
            s_ev = safe_div(rev, ev) if ev else None
            bm = safe_div(equity, mkt_cap) if mkt_cap else None

            rows.append({
                "date": sd_ts, "ticker": ticker,
                "A3": A3, "B2": B2,
                "ROA": roa, "GPA": gpa, "FCF_MARGIN": fcf_m, "DEBT_ASSETS": da,
                "FCF_YIELD": fcf_y, "SALES_EV": s_ev, "BOOK_MARKET": bm,
            })

    df = pd.DataFrame(rows)
    # Percentile ranks
    for f in QF + VF:
        df[f"{f}_pct"] = df.groupby("date")[f].transform(lambda x: x.rank(pct=True))
    qfactors_ok = df[QF].notna().sum(axis=1)
    df["Q_composite"] = df[[f"{f}_pct" for f in QF]].mean(axis=1).where(qfactors_ok >= 2)
    vfactors_ok = df[VF].notna().sum(axis=1)
    df["V_composite"] = df[[f"{f}_pct" for f in VF]].mean(axis=1).where(vfactors_ok >= 2)

    coverage = {yr: {} for yr in range(2022, 2027)}
    for yr in coverage:
        sub = df[df.date.dt.year == yr]
        coverage[yr]["tickers"] = sub.ticker.nunique()
        coverage[yr]["q_valid"] = int(sub.Q_composite.notna().sum() / max(1, sub.ticker.nunique()) * 100)
        # percent
    cov_by_yr = {str(yr): v for yr, v in coverage.items()}

    return df, cov_by_yr


# ============================================================
# Part 3+4 — Quarterly-mechanics simulator
# ============================================================

QUARTER_MONTHS = {3, 6, 9, 12}  # Mar, Jun, Sep, Dec last sessions


def quarterly_dates(dates: pd.DatetimeIndex, min_year: int = 2022) -> list[pd.Timestamp]:
    """Return last session of each quarter from min_year onwards."""
    return list(dates[(dates.year >= min_year) & dates.month.isin(QUARTER_MONTHS)].to_series()
                .groupby(dates.to_period("Q")).last().values)


def simulate_quarterly(
    panel: pd.DataFrame,
    dates: pd.DatetimeIndex,
    price_col: str,
    score_fn,
    cost_bps: float = 10.0,
    sector_cap: float = 0.25,
    industry_cap: float = 0.15,
    sectors: np.ndarray | None = None,
    industries: np.ndarray | None = None,
) -> pd.DataFrame:
    """Simulate quarterly-rebuild portfolio.

    Only rebalances on Mar/Jun/Sep/Dec final sessions.
    Between rebalances: survivors drift, only hard-eligibility exits.
    """
    q_dates = quarterly_dates(dates, 2022)
    fill_map = {}
    for qd in q_dates:
        qsi = int(dates.get_loc(qd))
        if qsi + 1 < len(dates):
            fill_map[qsi + 1] = qd

    n = 30
    weights: dict[int, float] = {}
    cash = 1.0
    rows = []
    tickers = panel["ticker"].unique().tolist() if "ticker" in panel.columns else []

    for di in range(len(dates)):
        dr = dates[di]
        # Get returns from panel daily data
        day_return = 0.0

        if di in fill_map:
            sd = fill_map[di]
            # Get scores for this date
            score_sub = panel[panel.date == sd]
            if len(score_sub):
                scores = score_sub.set_index("ticker")[price_col].to_dict()
            else:
                scores = {}

            # Score all tickers
            scored = [(tkr, scores.get(tkr, -1)) for tkr in tickers if tkr in scores]
            scored.sort(key=lambda x: -x[1])

            # Select top 30 with sector/industry caps
            selected: list[str] = []
            sector_cnt: dict[str, int] = {}
            industry_cnt: dict[str, int] = {}
            max_sec = max(1, int(np.floor(n * sector_cap + 1e-12)))
            max_ind = max(1, int(np.floor(n * industry_cap + 1e-12)))

            for tkr, sc in scored:
                sec = ""
                ind = ""
                if sectors is not None and tickers and tkr in tickers:
                    ti = tickers.index(tkr)
                    sec = str(sectors[ti]) if ti < len(sectors) else ""
                    ind = str(industries[ti]) if ti < len(industries) else ""
                if sec and sector_cnt.get(sec, 0) >= max_sec:
                    continue
                if ind and industry_cnt.get(ind, 0) >= max_ind:
                    continue
                selected.append(tkr)
                sector_cnt[sec] = sector_cnt.get(sec, 0) + 1
                industry_cnt[ind] = industry_cnt.get(ind, 0) + 1
                if len(selected) >= n:
                    break

            # Assign equal weights
            target = {tkr: 1.0 / n for tkr in selected}
            cash = 0.0
            weights = {i: target.get(tkr, 0.0) for i, tkr in enumerate(tickers) if tkr in target}
            # (simplified: using integer indices for weights is complex;
            #  for this version we just track the portfolio value)

    # Simplified: return placeholder
    return pd.DataFrame()


def main():
    print("Practical yFinance QV backtest — under construction")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
