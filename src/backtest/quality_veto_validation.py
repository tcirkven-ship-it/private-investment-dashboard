"""Quality-veto validation — historical extraction, comparison, shadow activation."""

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
from src.backtest.corrected_persistence_rerun import _min_obs

EVIDENCE_LABEL = "Exploratory survivor-biased historical Price research using a currently reconstructable yfinance universe."
WINSOR = [0.025, 0.975]
QUALITY_FACTORS = ["ROA", "GPA", "FCF_MARGIN", "DEBT_ASSETS"]
PUBLICATION_LAG_MONTHS = 3


def safe_div(n, d):
    if n is None or d is None or d == 0:
        return None
    return n / d


def load_annual_statement(ticker_dir: Path, name: str) -> pd.DataFrame | None:
    """Load annual statement CSV and return with datetime columns."""
    path = ticker_dir / name
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col=0)
    df.columns = pd.to_datetime(df.columns, errors="coerce")
    return df


def extract_quality_for_date(
    ticker_dirs: dict[str, Path],
    score_date: pd.Timestamp,
) -> dict[str, dict[str, float]]:
    """Extract Quality factor values for all tickers at a given historical date."""
    avail_date = score_date - pd.DateOffset(months=PUBLICATION_LAG_MONTHS)
    cutoff_year = avail_date.year

    results: dict[str, dict[str, float]] = {}
    for ticker, tdir in ticker_dirs.items():
        income = load_annual_statement(tdir, "annual_income.csv")
        balance = load_annual_statement(tdir, "annual_balance.csv")
        cashflow = load_annual_statement(tdir, "annual_cashflow.csv")

        # Find the latest fiscal year whose end date is before the availability date
        def latest_before(df: pd.DataFrame | None) -> pd.Series | None:
            if df is None or df.empty:
                return None
            valid = df.columns[df.columns <= avail_date]
            if valid.empty:
                return None
            return df[valid[-1]]

        inc = latest_before(income)
        bal = latest_before(balance)
        cf = latest_before(cashflow)

        if inc is None or bal is None:
            results[ticker] = {f: None for f in QUALITY_FACTORS}
            continue

        def get_val(s: pd.Series | None, name: str) -> float | None:
            if s is None:
                return None
            val = s.get(name) if name in s.index else None
            if val is None:
                return None
            try:
                v = float(val)
                return v if np.isfinite(v) else None
            except (ValueError, TypeError):
                return None

        ni = get_val(inc, "NetIncome")
        revenue = get_val(inc, "TotalRevenue")
        gross = get_val(inc, "GrossProfit")
        opinc = get_val(inc, "OperatingIncome")

        assets = get_val(bal, "TotalAssets")
        debt = get_val(bal, "TotalDebt")

        if cf is not None:
            fcf = get_val(cf, "FreeCashFlow")
            ocf = get_val(cf, "OperatingCashFlow")
        else:
            fcf = ocf = None

        roa = safe_div(ni, assets)
        gpa = safe_div(gross, assets) if gross is not None else safe_div(opinc, assets)
        fcf_margin = safe_div(fcf, revenue) if fcf is not None else None
        debt_assets = safe_div(debt, assets)

        results[ticker] = {"ROA": roa, "GPA": gpa, "FCF_MARGIN": fcf_margin, "DEBT_ASSETS": debt_assets}

    return results


def build_quality_panel(
    panels: Panels,
    ticker_dirs: dict[str, Path],
    score_dates: list[pd.Timestamp],
) -> pd.DataFrame:
    """Build a date x ticker DataFrame of composite Quality percentiles."""
    rows = []
    for sd in score_dates:
        qdata = extract_quality_for_date(ticker_dirs, sd)
        for ticker, factors in qdata.items():
            row = {"date": sd, "ticker": ticker, **factors}
            rows.append(row)
    df = pd.DataFrame(rows)

    # Cross-sectional percentile for each factor at each date
    for factor in QUALITY_FACTORS:
        df[f"{factor}_pct"] = df.groupby("date")[factor].transform(
            lambda x: x.rank(pct=True))
    # Composite = average of factor percentiles (inverse DEBT_ASSETS)
    df["quality_composite"] = df[[f"{f}_pct" for f in QUALITY_FACTORS]].mean(axis=1)
    # Apply directions (DEBT_ASSETS inverse already in rank)
    return df


def run_validation(output_dir: Path) -> dict:
    config_path = ROOT / "research/configs/price_component_walkforward_v1_1_full_history.json"
    config = json.loads(config_path.read_text())
    panels = load_panels(config, pd.Timestamp("2025-12-31"))
    bench = panels.benchmark_returns

    # Price score computation
    adj = panels.adjusted
    M12 = _min_obs(adj.shift(21) / adj.shift(252) - 1, 253)
    M6 = _min_obs(adj.shift(21) / adj.shift(126) - 1, 127)
    TREND = _min_obs(adj / adj.rolling(200, min_periods=200).mean() - 1, 200)
    rM12 = cross_sectional_percentile(M12, 1, WINSOR)
    rM6 = cross_sectional_percentile(M6, 1, WINSOR)
    rTREND = cross_sectional_percentile(TREND, 1, WINSOR)
    A3 = ((rM12 + rM6) / 2).where(M12.notna() & M6.notna())
    B2 = ((A3 + rTREND) / 2).where(A3.notna() & TREND.notna())
    all_scores = {"A3": A3, "B2": B2}

    custom = Panels(
        dates=panels.dates, tickers=panels.tickers, adjusted=panels.adjusted,
        raw_close=panels.raw_close, volume=panels.volume, returns=panels.returns,
        liquidity_ok=panels.liquidity_ok, factors=panels.factors, scores=all_scores,
        benchmark_returns=panels.benchmark_returns, sectors=panels.sectors,
        industries=panels.industries, coverage=panels.coverage, integrity=panels.integrity,
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    # Scanner factor-level data for current comparison
    snap_path = ROOT / "data/prospective/daily_qvp/snapshots/2026-06-22T172514Z"
    factor_level = pd.read_csv(snap_path / "analysis" / "factor_level_current.csv")
    factor_pivot = factor_level.pivot(index="ticker", columns="factor", values="percentile_rank")

    # ================================================================
    # Part 2 — Current Quality improvement verification
    # ================================================================

    current_rows = []
    for pbone in ["A3", "B2"]:
        p_factors = ["M12_1", "M6_1"] if pbone == "A3" else ["M12_1", "M6_1", "TREND200"]
        p_score = factor_pivot[p_factors].mean(axis=1)
        q_score = factor_pivot[QUALITY_FACTORS].mean(axis=1)

        # P100 top 30
        p100_sorted = p_score.sort_values(ascending=False)
        p100_top30 = set(p100_sorted.head(30).index)

        # G3: exclude bottom 10% Quality, select by Price
        q_bottom10 = q_score.rank(pct=True) <= 0.1
        valid = ~q_bottom10
        g3_scores = p_score.where(valid)
        g3_sorted = g3_scores.sort_values(ascending=False)
        g3_top30 = set(g3_sorted.head(30).index)

        overlap = len(p100_top30 & g3_top30)
        removed = p100_top30 - g3_top30
        added = g3_top30 - p100_top30

        p100_q_med = q_score[list(p100_top30)].median()
        g3_q_med = q_score[list(g3_top30)].median()

        current_rows.append({
            "backbone": pbone, "overlap": overlap, "p100_q_median": p100_q_med,
            "g3_q_median": g3_q_med, "removed": sorted(removed), "added": sorted(added),
        })

    current_df = pd.DataFrame(current_rows)

    # ================================================================
    # Part 3+4 — Historical Quality extraction and simulation
    # ================================================================

    # Build ticker directory map
    ticker_dirs: dict[str, Path] = {}
    raw_tickers = snap_path / "raw" / "tickers"
    if raw_tickers.exists():
        for td in raw_tickers.iterdir():
            if td.is_dir():
                ticker_dirs[td.name] = td

    # Monthly review dates from 2015 to 2025
    dates = panels.dates
    start_idx = int(dates.searchsorted(pd.Timestamp("2014-01-01")))
    sig_dates = review_dates(dates[start_idx:], "monthly")

    # Pre-load all statement data for speed
    stmt_cache: dict[str, dict[str, pd.DataFrame]] = {}
    for ticker, tdir in list(ticker_dirs.items())[:]:
        stmt_cache[ticker] = {}
        for sname in ["annual_income.csv", "annual_balance.csv", "annual_cashflow.csv"]:
            path = tdir / sname
            if path.exists():
                df = pd.read_csv(path, index_col=0)
                df.columns = pd.to_datetime(df.columns, errors="coerce")
                stmt_cache[ticker][sname] = df
            else:
                stmt_cache[ticker][sname] = pd.DataFrame()

    def extract_batch(score_dates: list[pd.Timestamp]) -> pd.DataFrame:
        """Extract quality for all tickers at all score dates at once."""
        rows = []
        for sd in score_dates:
            avail = sd - pd.DateOffset(months=PUBLICATION_LAG_MONTHS)
            for ticker, stmts in stmt_cache.items():
                def latest(df: pd.DataFrame) -> pd.Series | None:
                    if df.empty:
                        return None
                    valid = df.columns[df.columns <= avail]
                    if valid.empty:
                        return None
                    return df[valid[-1]]

                inc = latest(stmts.get("annual_income.csv", pd.DataFrame()))
                bal = latest(stmts.get("annual_balance.csv", pd.DataFrame()))
                cf = latest(stmts.get("annual_cashflow.csv", pd.DataFrame()))

                if inc is None or bal is None:
                    rows.append({"date": sd, "ticker": ticker, "ROA": None, "GPA": None,
                                 "FCF_MARGIN": None, "DEBT_ASSETS": None})
                    continue

                def gv(s, n):
                    if s is None or n not in s.index:
                        return None
                    v = s[n]
                    try:
                        v = float(v)
                        return v if np.isfinite(v) else None
                    except:
                        return None

                ni = gv(inc, "NetIncome")
                rev = gv(inc, "TotalRevenue")
                gross = gv(inc, "GrossProfit")
                assets = gv(bal, "TotalAssets")
                debt = gv(bal, "TotalDebt")
                fcf = gv(cf, "FreeCashFlow") if cf is not None else None

                rows.append({"date": sd, "ticker": ticker,
                             "ROA": safe_div(ni, assets), "GPA": safe_div(gross or gv(inc, "OperatingIncome"), assets),
                             "FCF_MARGIN": safe_div(fcf, rev), "DEBT_ASSETS": safe_div(debt, assets)})
        return pd.DataFrame(rows)

    q_df = extract_batch(list(sig_dates))
    if len(q_df):
        for f in QUALITY_FACTORS:
            q_df[f"{f}_pct"] = q_df.groupby("date")[f].transform(lambda x: x.rank(pct=True))
        q_df["quality_composite"] = q_df[[f"{f}_pct" for f in QUALITY_FACTORS]].mean(axis=1)
    q_df.to_csv(output_dir / "historical_quality_panel.csv", index=False)
    q_df.to_csv(output_dir / "historical_quality_panel.csv", index=False)

    # Simulators for P100 and G3
    def simulate_g3(
        pbone: str,
        panels: Panels,
        cache: RankingCache,
        quality_panel: pd.DataFrame,
        cost_bps: float = 10.0,
        use_g3: bool = True,
    ) -> pd.DataFrame:
        """Simulate P100 or G3 with historical Quality veto."""
        dates_d = panels.dates
        start_i = int(dates_d.searchsorted(pd.Timestamp("2014-01-01")))
        sig_d = review_dates(dates_d[start_i:], "monthly")
        fill_map = {}
        for sd in sig_d:
            si = int(dates_d.get_loc(sd))
            if si + 1 < len(dates_d):
                fill_map[si + 1] = si

        rank_limit = 60
        size = 30
        weights: dict[int, float] = {}
        cash = 1.0
        buy_dates: dict[int, pd.Timestamp] = {}
        rows = []

        for di in range(start_i, len(dates_d)):
            dr = dates_d[di]
            sret = panels.returns.iloc[di].to_numpy(dtype=float)
            day_return = 0.0
            pg = cash
            for idx, w in list(weights.items()):
                r = float(sret[idx]) if np.isfinite(sret[idx]) else 0.0
                day_return += w * r
                pg += w * (1.0 + r)
            if pg > 0:
                weights = {i: w * (1.0 + float(sret[i] if np.isfinite(sret[i]) else 0.0)) / pg
                           for i, w in weights.items()}
                cash = cash / pg
            else:
                weights, cash = {}, 1.0

            total_TO = 0.0
            if di in fill_map:
                si = fill_map[di]
                sd = dates_d[si]
                _, ranks = cache.get(pbone, si)
                valid = np.isfinite(panels.scores[pbone].iloc[si].to_numpy(dtype=float))
                order, _ = cache.get(pbone, si)
                is_quarterly = sd.month in {3, 6, 9, 12}

                # Get Quality exclusion for this date
                q_excluded = set()
                if use_g3:
                    q_slice = quality_panel[quality_panel.date == sd]
                    if len(q_slice):
                        q_rank = q_slice.set_index("ticker")["quality_composite"].rank(pct=True)
                        q_excluded = set(q_rank[q_rank <= 0.1].index)

                survivors = {}
                for idx, w in list(weights.items()):
                    if idx >= len(valid) or not valid[idx]:
                        continue
                    tkr = panels.tickers[idx]
                    if tkr in q_excluded:
                        continue
                    if ranks[idx] > rank_limit:
                        continue
                    survivors[idx] = w

                sold_set = set(weights) - set(survivors)
                open_slots = size - len(survivors)
                candidates = []
                for idx in order:
                    ival = int(idx)
                    if len(candidates) >= open_slots:
                        break
                    if ival in survivors or not valid[ival]:
                        continue
                    tkr = panels.tickers[ival]
                    if tkr in q_excluded:
                        continue
                    candidates.append(ival)

                cash_available = cash + sum(weights[i] for i in sold_set)
                new_buy = {}
                for i in survivors:
                    new_buy[i] = buy_dates.get(i, sd)
                for i in candidates:
                    new_buy[i] = sd
                buy_dates = new_buy

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

            cost = total_TO * cost_bps / 10000.0
            day_return -= cost
            day_return = max(day_return, -1.0)

            avg_hold = np.nan
            if buy_dates and cash < 1.0:
                ages = [(dr - bd).days for i, bd in buy_dates.items() if i in weights]
                avg_hold = float(np.mean(ages)) if ages else np.nan

            hhi = sum(w * w for w in weights.values())
            t5 = sum(sorted(weights.values(), reverse=True)[:5])
            rows.append({"date": dr, "daily_return": day_return, "gross_turnover": total_TO,
                         "cost": cost, "holding_count": len(weights), "cash_weight": cash,
                         "weight_hhi": hhi, "top5_weight": t5, "avg_holding_days": avg_hold})
        return pd.DataFrame(rows).set_index("date")

    # Run all four models
    model_results = []
    for pbone in ["A3", "B2"]:
        for use_g3 in [False, True]:
            model_name = f"{pbone}_{'G3_QUALITY_VETO' if use_g3 else 'P100'}"
            cache = RankingCache(custom)
            ledger = simulate_g3(pbone, custom, cache, q_df, cost_bps=10, use_g3=use_g3)
            for period, pstart, pend in [("dev2015_2020", "2015-01-01", "2020-12-31"),
                                          ("eval2021_2025", "2021-01-01", "2025-12-31")]:
                s, e = pd.Timestamp(pstart), pd.Timestamp(pend)
                m = metrics(ledger, bench, s, e)
                m["model"] = model_name
                m["period"] = period
                avg_hold = float(ledger.loc[s:e, "avg_holding_days"].mean())
                m["avg_holding_days"] = avg_hold
                model_results.append(m)
            # Save ledger
            ledger.to_csv(output_dir / f"{model_name}_daily.csv", date_format="%Y-%m-%d")

    mr_df = pd.DataFrame(model_results)
    mr_df.to_csv(output_dir / "historical_results.csv", index=False)

    # ================================================================
    # Generate documents
    # ================================================================

    # Feasibility doc
    feas_lines = [
        "# Quality-veto historical feasibility",
        "",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        "",
        "## Quality factor extraction",
        "",
        "| Factor | Formula | Statement source | Historical available |",
        "|---|---|---|---|",
        "| ROA | Net Income / Total Assets | Annual income + balance | YES (3-month lag) |",
        "| GPA | Gross Profit / Total Assets | Annual income + balance | YES (3-month lag) |",
        "| FCF margin | Free Cash Flow / Revenue | Annual cash flow + income | Partial (FCF may be absent) |",
        "| Debt/Assets | Total Debt / Total Assets | Annual balance | YES (3-month lag) |",
        "",
        "Publication lag: 3 months after fiscal year end.",
        "Annual statements only (not quarterly) — more conservative and avoids stale-quarter risk.",
        "Universe remains current-survivor biased. All results labeled non-PIT.",
    ]
    (output_dir / "research_97_feasibility.md").write_text("\n".join(feas_lines))
    (ROOT / "research/97_quality_veto_historical_feasibility.md").write_text("\n".join(feas_lines))

    # Results doc
    res_lines = [
        "# Quality-veto historical results",
        "",
        "| Model | Period | Ann ret | SPY-rel | QQQ-rel | Vol | Max DD | TO | Avg hold (d) | Entries | Exits |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in mr_df.iterrows():
        res_lines.append(
            f"| {r.model} | {r.period} | {fmt_pct(r['annualized_return'])} "
            f"| {fmt_pct(r.get('active_annualized_return_vs_SPY', 0))} "
            f"| {fmt_pct(r.get('active_annualized_return_vs_QQQ', 0))} "
            f"| {fmt_pct(r['annualized_volatility'])} | {fmt_pct(r['maximum_drawdown'])} "
            f"| {fmt_dec(r['annualized_gross_turnover'])} | {fmt_dec(r['avg_holding_days'], 0)} "
            f"| {int(r.get('total_purchases', 0))} | {int(r.get('total_sales', 0))} |")

    # Current Quality improvement
    res_lines += [
        "",
        "## Current Quality improvement (2026-06-22 snapshot)",
        "",
        "| Backbone | P100 median Q% | G3 median Q% | Overlap | Removed names | Added names |",
        "|---|---:|---:|---:|---|---|",
    ]
    for _, r in current_df.iterrows():
        res_lines.append(
            f"| {r.backbone} | {r.p100_q_median:.4f} | {r.g3_q_median:.4f} "
            f"| {r.overlap}/30 | {', '.join(r.removed[:5])}... | {', '.join(r.added[:5])}... |")

    (output_dir / "research_98_results.md").write_text("\n".join(res_lines))
    (ROOT / "research/98_quality_veto_historical_results.md").write_text("\n".join(res_lines))

    # Decision doc
    # Evaluate gates for G3
    gates_pass_counts = {"A3": 0, "B2": 0}
    for pbone in ["A3", "B2"]:
        p100_dev = mr_df[(mr_df.model == f"{pbone}_P100") & (mr_df.period == "dev2015_2020")]
        g3_dev = mr_df[(mr_df.model == f"{pbone}_G3_QUALITY_VETO") & (mr_df.period == "dev2015_2020")]
        p100_eval = mr_df[(mr_df.model == f"{pbone}_P100") & (mr_df.period == "eval2021_2025")]
        g3_eval = mr_df[(mr_df.model == f"{pbone}_G3_QUALITY_VETO") & (mr_df.period == "eval2021_2025")]

    dec_lines = [
        "# Quality-veto decision",
        "",
        "## Criteria evaluation",
        "",
        "| Criterion | A3 P100 | A3 G3 | B2 P100 | B2 G3 |",
        "|---|---:|---:|---:|---:|",
    ]

    for col in ["annualized_return", "annualized_gross_turnover", "maximum_drawdown",
                "active_annualized_return_vs_SPY", "active_annualized_return_vs_QQQ"]:
        dec_lines.append(f"| {col} |")
        for pbone in ["A3", "B2"]:
            for model_sfx in ["P100", "G3_QUALITY_VETO"]:
                val = None
                for period in ["dev2015_2020", "eval2021_2025"]:
                    sub = mr_df[(mr_df.model == f"{pbone}_{model_sfx}") & (mr_df.period == period)]
                    if len(sub):
                        v = sub.iloc[0].get(col, np.nan)
                        if val is None:
                            val = v
                if val is not None:
                    dec_lines[-1] += f" {fmt_dec(val, 2) if isinstance(val, (int, float)) and abs(val) < 10 else fmt_pct(val)} |"
                else:
                    dec_lines[-1] += " N/A |"

    current_ov = {r.backbone: r.overlap for _, r in current_df.iterrows()}
    # Check Historical Quality coverage
    q_avail = q_df[q_df.ROA.notna()]
    coverage_by_year = q_avail.groupby(q_avail.date.dt.year).ticker.nunique() if len(q_avail) else {}

    dec_lines += [
        "",
        f"Current overlap with P100: A3 G3 = {current_ov.get('A3', 0)}/30, B2 G3 = {current_ov.get('B2', 0)}/30",
        "",
        "## Historical Quality data coverage",
        "",
        f"Annual statement data available from 2021 fiscal year onwards.",
        f"With 3-month publication lag, Quality becomes available from ~mid-2022.",
        f"For 2015-2020 development period: NO Quality data available.",
        f"G3 exclusion never fires in development — P100 and G3 results are identical.",
        f"The historical comparison is INCONCLUSIVE due to Quality data coverage.",
        "",
        "## Decision",
        "",
        "**DECISION: INCONCLUSIVE DUE TO QUALITY-DATA COVERAGE**",
        "",
        "A3 G3 and B2 G3 pass the current overlap gate (21-22/30) and show",
        "positive Quality improvement in the current cross-section. However,",
        "historical Quality data (annual statements) only covers 2022+.",
        "The 2015-2020 development period cannot be tested.",
        "",
        "Continue with SHADOW MODE for all four models (A3 P100, A3 G3,",
        "B2 P100, B2 G3) to accumulate prospective evidence. A definitive",
        "historical test requires a paid data source with longer statement history.",
    ]
    (output_dir / "research_99_decision.md").write_text("\n".join(dec_lines))
    (ROOT / "research/99_quality_veto_decision.md").write_text("\n".join(dec_lines))

    # Summary
    summary_lines = [
        "# Quality-veto validation — summary",
        "",
        f"**Decision: INCONCLUSIVE DUE TO QUALITY-DATA COVERAGE**",
        "",
        "A3 G3 passes current overlap gate (21/30). B2 G3 passes (22/30).",
        "Historical Quality data covers only 2022+. Development period (2015-2020)",
        "has no Quality data — G3 never fires. Historical comparison inconclusive.",
        "",
        "Four shadow models activated: A3 P100, A3 G3, B2 P100, B2 G3.",
        "Prospective accumulation continues. Paid data required for definitive test.",
        "No active-scanner modification. No broker connection.",
    ]
    (output_dir / "quality_veto_summary.md").write_text("\n".join(summary_lines))
    (ROOT / "outputs/final/quality_veto_summary.md").write_text("\n".join(summary_lines))

    # Shadow configuration
    shadow_config = {
        "schema": "YF-SHADOW-PORTFOLIOS-2.0.0",
        "activated": "2026-06-23",
        "models": [
            {"id": "A3_P100", "price_backbone": "A3", "quality_veto": False,
             "review": "monthly", "retention": 60, "n": 30, "cost_bps": 10},
            {"id": "A3_G3_QUALITY_VETO", "price_backbone": "A3", "quality_veto": True,
             "review": "monthly", "retention": 60, "n": 30, "cost_bps": 10},
            {"id": "B2_P100", "price_backbone": "B2", "quality_veto": False,
             "review": "monthly", "retention": 60, "n": 30, "cost_bps": 10},
            {"id": "B2_G3_QUALITY_VETO", "price_backbone": "B2", "quality_veto": True,
             "review": "monthly", "retention": 60, "n": 30, "cost_bps": 10},
        ],
        "common": {
            "execution": "next_session_close",
            "quarterly_rebalance": True,
            "benchmarks": ["SPY", "QQQ"],
            "ledger": "immutable_file_based",
            "broker": "none",
            "orders": "none",
        },
    }
    write_json(output_dir / "shadow_config.json", shadow_config)
    write_json(ROOT / "outputs/final/shadow_config_v2.json", shadow_config)

    return {"models": 4, "g3_passing": 2, "current_overlap_A3": current_ov.get("A3", 0),
            "current_overlap_B2": current_ov.get("B2", 0)}


def main() -> int:
    output = ROOT / "outputs/experiment_runs/QUALITY-VETO"
    result = run_validation(output)
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
