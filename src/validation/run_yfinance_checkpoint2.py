#!/usr/bin/env python3
"""Offline semantic, factor, coverage, and current-score analysis for Checkpoint 2."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


FORMULA_VERSION = "YF-FACTOR-1.0.0"
PRICE_FACTORS = ["M12_1", "M6_1", "RS63_MKT", "RS252_SEC", "TREND200", "VOL252", "DOWNVOL252", "DD252", "LIQ63"]
QUALITY_FACTORS = ["ROA", "APPROX_ROIC", "GPA", "OP_MARGIN", "FCF_MARGIN", "CASH_CONVERSION", "DEBT_ASSETS", "NET_DEBT_EBITDA", "INTEREST_COVER", "EARN_STABILITY", "DILUTION"]
VALUE_FACTORS = ["EARN_YIELD", "FCF_YIELD", "EBIT_EV", "SALES_EV", "BOOK_MARKET", "SHAREHOLDER_YIELD"]
GROWTH_FACTORS = ["REV_GROWTH", "OP_INC_GROWTH", "NI_GROWTH", "FCF_GROWTH", "MARGIN_CHANGE", "ASSET_GROWTH"]
EXPECTATION_FACTORS = ["EPS_REV_BREADTH", "EPS_TREND", "REV_EST_GROWTH", "SURPRISE4", "REC_CHANGE"]
DIRECTIONS = {factor: 1 for factor in PRICE_FACTORS + QUALITY_FACTORS + VALUE_FACTORS + GROWTH_FACTORS + EXPECTATION_FACTORS}
DIRECTIONS.update({"VOL252": -1, "DOWNVOL252": -1, "DEBT_ASSETS": -1, "NET_DEBT_EBITDA": -1, "ASSET_GROWTH": -1})
CATEGORIES = {**{x: "Price" for x in PRICE_FACTORS}, **{x: "Quality" for x in QUALITY_FACTORS}, **{x: "Value" for x in VALUE_FACTORS}, **{x: "Growth" for x in GROWTH_FACTORS}, **{x: "Expectations" for x in EXPECTATION_FACTORS}}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def read_frame(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, index_col=0) if path.exists() and path.stat().st_size else pd.DataFrame()
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def finite(value: object) -> float | None:
    try:
        number = float(value)
        return number if np.isfinite(number) else None
    except (TypeError, ValueError):
        return None


class Statements:
    def __init__(self, ticker_dir: Path, alias_config: dict):
        self.dir = ticker_dir
        self.config = alias_config["fields"]
        self.frames = {name: read_frame(ticker_dir / f"{name}.csv") for name in [
            "trailing_income", "quarterly_income", "annual_income", "quarterly_balance", "annual_balance",
            "trailing_cashflow", "quarterly_cashflow", "annual_cashflow"]}

    def values(self, concept: str, endpoint: str) -> tuple[list[float], str | None]:
        mode = "sum4" if endpoint.endswith(":sum4") else "latest"
        endpoint = endpoint.split(":", 1)[0]
        frame = self.frames[endpoint]
        if frame.empty:
            return [], None
        for alias in self.config[concept]["aliases"]:
            if alias in frame.index:
                vals = pd.to_numeric(frame.loc[alias], errors="coerce").dropna().tolist()
                if vals:
                    if mode == "sum4":
                        return ([float(sum(vals[:4]))] if len(vals) >= 4 else []), alias
                    return [float(x) for x in vals], alias
        return [], None

    def current(self, concept: str) -> tuple[float | None, dict]:
        for endpoint in self.config[concept]["preferred"]:
            vals, alias = self.values(concept, endpoint)
            if vals:
                return vals[0], {"concept": concept, "endpoint": endpoint, "alias": alias}
        return None, {"concept": concept, "reason": "no_accepted_alias_value"}

    def annual(self, concept: str) -> tuple[list[float], str | None]:
        endpoints = [x for x in self.config[concept]["preferred"] if x.startswith("annual_")]
        for endpoint in endpoints:
            vals, alias = self.values(concept, endpoint)
            if vals:
                return vals, alias
        return [], None

    def aligned_annual_quarterly(self, concept: str) -> tuple[float | None, float | None, str]:
        annual_endpoint = next((x for x in self.config[concept]["preferred"] if x.startswith("annual_")), None)
        if annual_endpoint is None:
            return None, None, "no_annual_endpoint"
        quarterly_endpoint = annual_endpoint.replace("annual_", "quarterly_")
        annual_frame, quarterly_frame = self.frames[annual_endpoint], self.frames.get(quarterly_endpoint, pd.DataFrame())
        if annual_frame.empty or quarterly_frame.empty:
            return None, None, "endpoint_missing"
        for annual_alias in self.config[concept]["aliases"]:
            if annual_alias not in annual_frame.index:
                continue
            annual_series = pd.to_numeric(annual_frame.loc[annual_alias], errors="coerce")
            annual_series.index = pd.to_datetime(annual_series.index, errors="coerce")
            annual_series = annual_series.dropna().sort_index(ascending=False)
            for annual_date, annual_value in annual_series.items():
                for quarterly_alias in self.config[concept]["aliases"]:
                    if quarterly_alias not in quarterly_frame.index:
                        continue
                    q = pd.to_numeric(quarterly_frame.loc[quarterly_alias], errors="coerce")
                    q.index = pd.to_datetime(q.index, errors="coerce")
                    q = q.dropna().sort_index()
                    aligned = q[(q.index <= annual_date) & (q.index > annual_date - pd.Timedelta(days=370))].tail(4)
                    if len(aligned) == 4:
                        return float(annual_value), float(aligned.sum()), f"annual={annual_alias};quarterly={quarterly_alias};end={annual_date.date()}"
        return None, None, "no_four_date_aligned_quarters"

    def dated_quarterly(self, concept: str) -> pd.Series:
        endpoint = next((x for x in self.config[concept]["preferred"] if x.startswith("quarterly_")), None)
        if endpoint is None:
            return pd.Series(dtype=float)
        frame = self.frames[endpoint.split(":", 1)[0]]
        for alias in self.config[concept]["aliases"]:
            if alias in frame.index:
                series = pd.to_numeric(frame.loc[alias], errors="coerce")
                series.index = pd.to_datetime(series.index, errors="coerce")
                return series.dropna().sort_index()
        return pd.Series(dtype=float)


def safe_div(n: float | None, d: float | None, positive_denominator: bool = True) -> float | None:
    if n is None or d is None or not np.isfinite(n) or not np.isfinite(d):
        return None
    if (positive_denominator and d <= 0) or (not positive_denominator and d == 0):
        return None
    return n / d


def growth(vals: list[float], require_positive_both: bool = True) -> float | None:
    if len(vals) < 2 or vals[1] == 0 or (require_positive_both and (vals[0] <= 0 or vals[1] <= 0)):
        return None
    return vals[0] / vals[1] - 1


def rel_diff(actual: float | None, expected: float | None) -> float | None:
    if actual is None or expected is None:
        return None
    return abs(actual - expected) / max(abs(actual), abs(expected), 1.0)


def semantic_row(test: str, ticker: str, actual: float | None, expected: float | None, tolerance: float, note: str = "") -> dict:
    diff = rel_diff(actual, expected)
    return {"test": test, "ticker": ticker, "actual": actual, "expected": expected, "relative_difference": diff,
            "tolerance": tolerance, "pass": bool(diff is not None and diff <= tolerance), "note": note}


def pct_return(series: pd.Series, recent: int, old: int) -> float | None:
    series = pd.to_numeric(series, errors="coerce").dropna()
    return float(series.iloc[-recent] / series.iloc[-old] - 1) if len(series) >= old else None


def through_session(frame: pd.DataFrame, as_of_session: pd.Timestamp | None) -> pd.DataFrame:
    if as_of_session is None or frame.empty:
        return frame
    dates = pd.to_datetime(frame.index, utc=True, errors="coerce").tz_convert(None).normalize()
    return frame.loc[np.asarray(dates <= as_of_session)].copy()


def factor_values(ticker: str, ticker_dir: Path, info: dict, st: Statements, spy: pd.Series,
                  as_of_session: pd.Timestamp | None = None) -> tuple[dict, dict, list[dict]]:
    inputs: dict[str, object] = {}
    for concept in st.config:
        value, provenance = st.current(concept)
        inputs[concept] = value
        inputs[f"{concept}__source"] = provenance
    market_cap, ev = finite(info.get("marketCap")), finite(info.get("enterpriseValue"))
    inputs.update({"market_cap": market_cap, "enterprise_value": ev, "shares_outstanding": finite(info.get("sharesOutstanding")),
                   "operating_margins_info": finite(info.get("operatingMargins"))})
    history = through_session(read_frame(ticker_dir / "history_daily.csv"), as_of_session)
    adjusted = pd.to_numeric(history.get("Adj Close", pd.Series(dtype=float)), errors="coerce").dropna()
    close = pd.to_numeric(history.get("Close", pd.Series(dtype=float)), errors="coerce")
    volume = pd.to_numeric(history.get("Volume", pd.Series(dtype=float)), errors="coerce")
    returns = np.log(adjusted / adjusted.shift(1)).dropna()
    stock63 = pct_return(adjusted, 1, 64)
    spy63 = pct_return(spy, 1, 64)

    ni, assets = inputs["net_income"], inputs["total_assets"]
    stock_series = {}
    for concept in ["total_assets", "total_debt", "cash", "stockholders_equity"]:
        vals, _ = st.values(concept, "quarterly_balance")
        if not vals:
            vals, _ = st.values(concept, "annual_balance")
        stock_series[concept] = vals
    average_assets = float(np.mean(stock_series["total_assets"][:2])) if len(stock_series["total_assets"]) >= 2 else assets
    invested_capital_observations = []
    for i in range(2):
        if all(len(stock_series[x]) > i for x in ["total_debt", "stockholders_equity", "cash"]):
            invested_capital_observations.append(stock_series["total_debt"][i] + stock_series["stockholders_equity"][i] - stock_series["cash"][i])
    average_invested_capital = float(np.mean(invested_capital_observations)) if invested_capital_observations else None
    inputs["average_total_assets"] = average_assets
    inputs["average_invested_capital"] = average_invested_capital
    debt, cash, equity = inputs["total_debt"], inputs["cash"], inputs["stockholders_equity"]
    revenue, opinc, fcf = inputs["revenue"], inputs["operating_income"], inputs["free_cash_flow"]
    ebit, ebitda, interest = inputs["ebit"], inputs["ebitda"], inputs["interest_expense"]
    gross, ocf = inputs["gross_profit"], inputs["operating_cash_flow"]
    ordinary = inputs["ordinary_shares"]
    quarterly_ni = st.dated_quarterly("net_income")
    quarterly_assets = st.dated_quarterly("total_assets")
    aligned_profitability = pd.concat([quarterly_ni.rename("ni"), quarterly_assets.rename("assets")], axis=1, sort=True).dropna().tail(5)
    if len(aligned_profitability) == 5 and (aligned_profitability.assets > 0).all():
        earnings_stability = -float((aligned_profitability.ni / aligned_profitability.assets).std(ddof=1))
    else:
        earnings_stability = None
    annual = {c: st.annual(c)[0] for c in ["revenue", "operating_income", "net_income", "free_cash_flow", "total_assets", "ordinary_shares"]}
    values = {
        "M12_1": pct_return(adjusted, 22, 253), "M6_1": pct_return(adjusted, 22, 127),
        "RS63_MKT": (stock63 - spy63) if stock63 is not None and spy63 is not None else None,
        "TREND200": (float(adjusted.iloc[-1] / adjusted.tail(200).mean() - 1) if len(adjusted) >= 200 else None),
        "VOL252": (float(returns.tail(252).std(ddof=1) * np.sqrt(252)) if len(returns.tail(252)) >= 200 else None),
        "DOWNVOL252": (float(np.sqrt(np.mean(np.square(returns.tail(252)[returns.tail(252) < 0]))) * np.sqrt(252)) if (returns.tail(252) < 0).sum() else None),
        "DD252": (float(adjusted.iloc[-1] / adjusted.tail(252).max() - 1) if len(adjusted) >= 252 else None),
        "LIQ63": (float((close * volume).tail(63).median()) if (close * volume).tail(63).notna().sum() >= 55 else None),
        "ROA": safe_div(ni, average_assets), "APPROX_ROIC": safe_div(ebit, average_invested_capital),
        "GPA": safe_div(gross, average_assets), "OP_MARGIN": safe_div(opinc, revenue), "FCF_MARGIN": safe_div(fcf, revenue),
        "CASH_CONVERSION": safe_div(ocf, ni), "DEBT_ASSETS": safe_div(debt, assets),
        "NET_DEBT_EBITDA": safe_div((debt - cash) if debt is not None and cash is not None else None, ebitda),
        "INTEREST_COVER": safe_div(ebit, abs(interest) if interest is not None else None), "EARN_STABILITY": earnings_stability,
        "DILUTION": (-growth(annual["ordinary_shares"], False) if growth(annual["ordinary_shares"], False) is not None else None),
        "EARN_YIELD": safe_div(ni, market_cap), "FCF_YIELD": safe_div(fcf, market_cap), "EBIT_EV": safe_div(ebit, ev),
        "SALES_EV": safe_div(revenue, ev), "BOOK_MARKET": safe_div(equity, market_cap),
        "REV_GROWTH": growth(annual["revenue"]), "OP_INC_GROWTH": growth(annual["operating_income"]),
        "NI_GROWTH": growth(annual["net_income"]), "FCF_GROWTH": growth(annual["free_cash_flow"]),
        "ASSET_GROWTH": growth(annual["total_assets"]),
    }
    if len(annual["operating_income"]) >= 2 and len(annual["revenue"]) >= 2 and annual["revenue"][0] > 0 and annual["revenue"][1] > 0:
        values["MARGIN_CHANGE"] = annual["operating_income"][0] / annual["revenue"][0] - annual["operating_income"][1] / annual["revenue"][1]
    else:
        values["MARGIN_CHANGE"] = None
    components = [inputs["dividends_paid"], inputs["repurchases"], inputs["issuance"]]
    values["SHAREHOLDER_YIELD"] = safe_div(-sum(components), market_cap) if all(x is not None for x in components) else None
    values["RS252_SEC"] = values["M12_1"]  # converted to sector-relative after the cross-section is assembled

    eps_revisions = read_frame(ticker_dir / "eps_revisions.csv")
    eps_trend = read_frame(ticker_dir / "eps_trend.csv")
    revenue_estimate = read_frame(ticker_dir / "revenue_estimate.csv")
    earnings_history = read_frame(ticker_dir / "earnings_history.csv")
    inputs["expectations_endpoint_rows"] = {"eps_revisions": len(eps_revisions), "eps_trend": len(eps_trend),
        "revenue_estimate": len(revenue_estimate), "earnings_history": len(earnings_history)}
    breadth = []
    breadth_components = {}
    for period in ["0q", "+1q"]:
        if period in eps_revisions.index:
            up = finite(eps_revisions.loc[period].get("upLast30days"))
            down = finite(eps_revisions.loc[period].get("downLast30days"))
            if up is not None and down is not None:
                breadth.append((up - down) / max(1.0, up + down))
                breadth_components[period] = {"upLast30days": up, "downLast30days": down}
    inputs["eps_revision_breadth_components"] = breadth_components
    values["EPS_REV_BREADTH"] = float(np.mean(breadth)) if len(breadth) == 2 else None
    trend = []
    trend_components = {}
    for period in ["0y", "+1y"]:
        if period in eps_trend.index:
            current = finite(eps_trend.loc[period].get("current"))
            prior = finite(eps_trend.loc[period].get("30daysAgo"))
            if current is not None and prior is not None and prior > 0:
                trend.append(current / prior - 1)
                trend_components[period] = {"current": current, "30daysAgo": prior}
    inputs["eps_trend_components"] = trend_components
    values["EPS_TREND"] = float(np.mean(trend)) if len(trend) == 2 else None
    if "0y" in revenue_estimate.index:
        estimate = finite(revenue_estimate.loc["0y"].get("avg"))
        year_ago = finite(revenue_estimate.loc["0y"].get("yearAgoRevenue"))
        inputs["revenue_estimate_growth_components"] = {"avg": estimate, "yearAgoRevenue": year_ago}
        values["REV_EST_GROWTH"] = safe_div(estimate, year_ago)
        if values["REV_EST_GROWTH"] is not None:
            values["REV_EST_GROWTH"] -= 1
    else:
        values["REV_EST_GROWTH"] = None
    surprises = pd.to_numeric(earnings_history.get("surprisePercent", pd.Series(dtype=float)), errors="coerce").dropna().tail(4)
    inputs["surprise4_components"] = surprises.tolist()
    values["SURPRISE4"] = float(surprises.mean()) if len(surprises) == 4 else None
    values["REC_CHANGE"] = None
    inputs["REC_CHANGE_reason"] = "get_recommendations returned period-level consensus counts, not upgrade/downgrade events required by the frozen formula"

    semantic = []
    capex, da = inputs["capital_expenditure"], inputs["depreciation_amortization"]
    semantic.append(semantic_row("FCF_vs_OCF_minus_capex", ticker, fcf, (ocf - abs(capex)) if ocf is not None and capex is not None else None, 0.02))
    semantic.append(semantic_row("EBITDA_vs_EBIT_plus_DA", ticker, ebitda, (ebit + da) if ebit is not None and da is not None else None, 0.05))
    pref, minority = inputs["preferred_stock"], inputs["minority_interest"]
    expected_ev = market_cap + debt + pref + minority - cash if None not in (market_cap, debt, pref, minority, cash) else None
    semantic.append(semantic_row("EV_bridge", ticker, ev, expected_ev, 0.10, "Compared only when preferred stock and minority interest are explicitly reported; unknown is not zero."))
    semantic.append(semantic_row("ordinary_vs_info_shares", ticker, ordinary, inputs["shares_outstanding"], 0.05))
    semantic.append(semantic_row("gross_profit_bridge", ticker, gross, (revenue - inputs["cost_revenue"]) if revenue is not None and inputs["cost_revenue"] is not None else None, 0.02))
    semantic.append(semantic_row("operating_margin_info", ticker, values["OP_MARGIN"], inputs["operating_margins_info"], 0.02))

    actions = read_frame(ticker_dir / "actions.csv")
    shares = read_frame(ticker_dir / "shares_full.csv")
    if not actions.empty and "Stock Splits" in actions and not shares.empty:
        share_values = pd.to_numeric(shares.iloc[:, 0], errors="coerce")
        share_dates = pd.to_datetime(shares.index, utc=True, errors="coerce")
        share_series = pd.Series(share_values.values, index=share_dates).dropna().groupby(level=0).median().sort_index()
        split_values = pd.to_numeric(actions["Stock Splits"], errors="coerce").fillna(0)
        split_dates = pd.to_datetime(actions.index, utc=True, errors="coerce")
        for split_date, ratio in zip(split_dates, split_values):
            if pd.isna(split_date) or ratio <= 0:
                continue
            before = share_series[share_series.index < split_date].tail(1)
            after = share_series[share_series.index >= split_date].head(1)
            observed = float(after.iloc[0] / before.iloc[0]) if len(before) and len(after) and before.iloc[0] > 0 else None
            semantic.append(semantic_row("split_vs_share_change", ticker, observed, float(ratio), 0.15,
                                         f"split_date={split_date.date()}"))

    for concept, endpoint in [("revenue", "quarterly_income"), ("operating_income", "quarterly_income"), ("net_income", "quarterly_income"), ("operating_cash_flow", "quarterly_cashflow"), ("free_cash_flow", "quarterly_cashflow")]:
        annual_value, summed_quarters, alignment_note = st.aligned_annual_quarterly(concept)
        semantic.append(semantic_row(f"annual_vs_sum4q_{concept}", ticker, annual_value, summed_quarters, 0.15, alignment_note))
    return values, inputs, semantic


def winsor_rank(long: pd.DataFrame, universe: pd.DataFrame) -> pd.DataFrame:
    out = long.merge(universe[["ticker", "info_sector"]], on="ticker", how="left")
    out["comparison_group"] = ""
    out["winsorized_value"] = np.nan
    out["percentile_rank"] = np.nan
    for factor, indices in out.groupby("factor").groups.items():
        factor_valid = out.loc[indices][out.loc[indices, "raw_value"].notna()]
        if CATEGORIES[factor] == "Price":
            if len(factor_valid):
                lo, hi = factor_valid["raw_value"].quantile([0.025, 0.975])
                clipped = factor_valid["raw_value"].clip(lo, hi)
                out.loc[factor_valid.index, "winsorized_value"] = clipped
                out.loc[factor_valid.index, "comparison_group"] = "market_price_cross_section"
                out.loc[factor_valid.index, "percentile_rank"] = (clipped * DIRECTIONS[factor]).rank(pct=True, method="average")
            continue
        for sector, sector_idx in out.loc[indices].groupby("info_sector").groups.items():
            local = out.loc[sector_idx]
            local_valid = local[local["raw_value"].notna()]
            if len(local_valid) >= 20:
                target, label = local_valid.index, f"sector:{sector}"
            else:
                target = out.loc[indices][out.loc[indices, "raw_value"].notna()].index
                label = "market_fallback_sector_lt20"
            if len(target) == 0:
                continue
            lo, hi = out.loc[target, "raw_value"].quantile([0.025, 0.975])
            assign = local_valid.index
            out.loc[assign, "winsorized_value"] = out.loc[assign, "raw_value"].clip(lo, hi)
            out.loc[assign, "comparison_group"] = label
            direction = DIRECTIONS[factor]
            ranks = (out.loc[target, "raw_value"].clip(lo, hi) * direction).rank(pct=True, method="average")
            out.loc[assign, "percentile_rank"] = ranks.reindex(assign)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--aliases", type=Path, default=Path("research/configs/yfinance_statement_aliases_v1.json"))
    parser.add_argument("--as-of-session", type=pd.Timestamp,
                        help="Ignore daily bars after this fully completed session (YYYY-MM-DD)")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    aliases = json.loads(args.aliases.read_text())
    universe = pd.read_csv(args.snapshot / "base_eligible_universe.csv")
    snapshot_time = json.loads((args.snapshot / "manifest.json").read_text()).get("completed_at_utc")
    spy_frame = read_frame(args.snapshot / "benchmarks" / "SPY_history_daily.csv")
    spy_frame = through_session(spy_frame, args.as_of_session)
    spy = pd.to_numeric(spy_frame.get("Adj Close", pd.Series(dtype=float)), errors="coerce").dropna()
    factor_rows, semantics, alias_usage = [], [], []
    universe_lookup = universe.set_index("ticker").to_dict(orient="index")
    for ticker in universe["ticker"].astype(str):
        ticker_dir = args.snapshot / "tickers" / ticker.replace("/", "_")
        info = json.loads((ticker_dir / "info.json").read_text()) or {}
        fallback = universe_lookup[ticker]
        for key, column in {"marketCap": "info_market_cap", "enterpriseValue": "info_enterprise_value",
                            "sharesOutstanding": "info_shares_outstanding", "sector": "info_sector", "industry": "info_industry"}.items():
            if info.get(key) is None and pd.notna(fallback.get(column)):
                info[key] = fallback.get(column)
        st = Statements(ticker_dir, aliases)
        values, inputs, tests = factor_values(ticker, ticker_dir, info, st, spy, args.as_of_session)
        semantics.extend(tests)
        for concept in aliases["fields"]:
            _, source = st.current(concept)
            alias_usage.append({"ticker": ticker, "concept": concept, "alias": source.get("alias"), "endpoint": source.get("endpoint"), "resolved": "alias" in source})
        checksums = {name: sha(ticker_dir / f"{name}.csv") for name in ["history_daily", "trailing_income", "quarterly_income", "annual_income", "quarterly_balance", "annual_balance", "trailing_cashflow", "quarterly_cashflow", "annual_cashflow", "earnings_history", "eps_revisions", "eps_trend", "revenue_estimate", "recommendations"]}
        checksums["info"] = sha(ticker_dir / "info.json")
        for factor in CATEGORIES:
            value = finite(values.get(factor))
            factor_rows.append({"ticker": ticker, "snapshot_timestamp": snapshot_time, "factor": factor, "category": CATEGORIES[factor],
                                "raw_inputs": json.dumps(inputs, sort_keys=True, default=str), "raw_value": value,
                                "missing_reason": None if value is not None else (inputs.get("REC_CHANGE_reason") if factor == "REC_CHANGE" else "required_input_missing_or_invalid_denominator"),
                                "formula_version": FORMULA_VERSION, "input_file_checksums": json.dumps(checksums, sort_keys=True)})
    long = pd.DataFrame(factor_rows)
    # Current sector-relative strength is a residual from the current sector median.
    sectors = universe.set_index("ticker")["info_sector"]
    m12 = long[long.factor.eq("M12_1")].set_index("ticker")["raw_value"]
    sector_median = m12.groupby(sectors).transform("median")
    mask = long.factor.eq("RS252_SEC")
    long.loc[mask, "raw_value"] = long.loc[mask, "ticker"].map(m12 - sector_median)
    long = winsor_rank(long, universe)
    long.to_csv(args.output / "factor_level_current.csv", index=False)

    sem = pd.DataFrame(semantics)
    sem.to_csv(args.output / "semantic_reconciliation_observations.csv", index=False)
    summary = sem.groupby("test", dropna=False).agg(eligible=("ticker", "size"), comparable=("relative_difference", "count"), pass_count=("pass", "sum"), median_relative_difference=("relative_difference", "median"), p90_relative_difference=("relative_difference", lambda x: x.quantile(.9)), max_relative_difference=("relative_difference", "max")).reset_index()
    summary["pass_rate_comparable"] = summary["pass_count"] / summary["comparable"].replace(0, np.nan)
    summary.to_csv(args.output / "semantic_reconciliation_summary.csv", index=False)
    usage = pd.DataFrame(alias_usage)
    usage.to_csv(args.output / "statement_alias_usage_ticker.csv", index=False)
    usage.groupby(["concept", "alias", "endpoint"], dropna=False).size().rename("companies").reset_index().to_csv(args.output / "statement_alias_usage_summary.csv", index=False)
    required_fundamental = ["revenue", "net_income", "total_assets", "operating_cash_flow", "free_cash_flow"]
    resolved = usage.pivot(index="ticker", columns="concept", values="resolved")
    fundamental = universe[["ticker"]].copy().set_index("ticker")
    for concept in required_fundamental:
        fundamental[f"has_{concept}"] = resolved.get(concept, False)
    fundamental["fundamental_coverage_pass"] = fundamental[[f"has_{x}" for x in required_fundamental]].all(axis=1)
    fundamental.reset_index().to_csv(args.output / "fundamental_coverage_eligibility.csv", index=False)

    coverage = long.assign(available=long.raw_value.notna()).groupby(["factor", "category"]).agg(companies=("ticker", "size"), available=("available", "sum")).reset_index()
    coverage["coverage"] = coverage.available / coverage.companies
    coverage.to_csv(args.output / "factor_coverage_overall.csv", index=False)
    expanded = long.merge(universe[["ticker", "info_industry", "info_market_cap"]], on="ticker")
    expanded["market_cap_bucket"] = pd.cut(expanded.info_market_cap, [2e9, 5e9, 10e9, np.inf], labels=["2B-5B", "5B-10B", ">10B"], right=False)
    for group, filename in [("info_sector", "factor_coverage_by_sector.csv"), ("info_industry", "factor_coverage_by_industry.csv"), ("market_cap_bucket", "factor_coverage_by_market_cap.csv")]:
        x = expanded.assign(available=expanded.raw_value.notna()).groupby(["factor", group], observed=True).agg(companies=("ticker", "size"), available=("available", "sum")).reset_index()
        x["coverage"] = x.available / x.companies
        x.to_csv(args.output / filename, index=False)

    corr = long.pivot(index="ticker", columns="factor", values="percentile_rank").corr(method="spearman")
    corr.to_csv(args.output / "factor_spearman_current.csv")
    proposed = {"Price": ["M12_1", "M6_1", "TREND200", "VOL252"], "Quality": ["ROA", "GPA", "OP_MARGIN", "FCF_MARGIN", "DEBT_ASSETS", "DILUTION"], "Value": ["FCF_YIELD", "EBIT_EV", "SALES_EV", "BOOK_MARKET"], "Growth": ["REV_GROWTH", "MARGIN_CHANGE"]}
    sector_cov = pd.read_csv(args.output / "factor_coverage_by_sector.csv")
    semantic_gate = {"FCF_MARGIN": "FCF_vs_OCF_minus_capex", "FCF_YIELD": "FCF_vs_OCF_minus_capex", "FCF_GROWTH": "FCF_vs_OCF_minus_capex", "OP_MARGIN": "operating_margin_info", "GPA": "gross_profit_bridge", "EBIT_EV": "EV_bridge", "DILUTION": "split_vs_share_change", "REV_GROWTH": "annual_vs_sum4q_revenue", "MARGIN_CHANGE": "annual_vs_sum4q_operating_income"}
    admitted, admission_rows = {}, []
    for category, factors in proposed.items():
        candidates = []
        for factor in factors:
            overall = float(coverage.set_index("factor").loc[factor, "coverage"])
            min_sector = float(sector_cov[sector_cov.factor.eq(factor)].coverage.min())
            test = semantic_gate.get(factor)
            sem_rate = float(summary.set_index("test").loc[test, "pass_rate_comparable"]) if test and test in summary.test.values else 1.0
            sem_comparable = int(summary.set_index("test").loc[test, "comparable"]) if test and test in summary.test.values else len(universe)
            status = "primary_candidate" if overall >= .8 and min_sector >= .7 and sem_rate >= .8 and sem_comparable >= max(20, int(.5 * len(universe))) else ("diagnostic" if overall >= .6 else "rejected_sparse")
            admission_rows.append({"factor": factor, "category": category, "overall_coverage": overall, "minimum_sector_coverage": min_sector, "semantic_test": test, "semantic_comparable": sem_comparable, "semantic_pass_rate": sem_rate, "pre_redundancy_status": status})
            if status == "primary_candidate": candidates.append(factor)
        retained = []
        for factor in candidates:
            redundant_with = next((x for x in retained if abs(corr.loc[factor, x]) > .85), None)
            if redundant_with:
                next(row for row in admission_rows if row["factor"] == factor)["pre_redundancy_status"] = f"diagnostic_redundant_with_{redundant_with}"
            else:
                retained.append(factor)
        admitted[category] = retained
    admission = pd.DataFrame(admission_rows)
    admission.to_csv(args.output / "factor_admission.csv", index=False)
    (args.output / "primary_factor_sets.json").write_text(json.dumps({"formula_version": FORMULA_VERSION, "primary": admitted,
        "diagnostic": [x for x in CATEGORIES if x not in sum(admitted.values(), []) and x not in ["SHAREHOLDER_YIELD", "REC_CHANGE"]], "rejected": ["SHAREHOLDER_YIELD", "REC_CHANGE"],
        "rule": "Common complete factor set per category; companies missing any primary factor receive no primary category score."}, indent=2) + "\n")

    ranks = long.pivot(index="ticker", columns="factor", values="percentile_rank")
    category_scores = pd.DataFrame(index=ranks.index)
    for category, factors in admitted.items():
        category_scores[category] = ranks[factors].mean(axis=1) if factors else np.nan
        if factors:
            category_scores.loc[ranks[factors].isna().any(axis=1), category] = np.nan
    category_scores.reset_index().to_csv(args.output / "category_scores_current.csv", index=False)
    composites = pd.DataFrame(index=ranks.index)
    families = {"YF-P": ["Price"], "YF-QP": ["Quality", "Price"], "YF-QVP": ["Quality", "Value", "Price"], "YF-QVGP": ["Quality", "Value", "Growth", "Price"]}
    for name, cats in families.items():
        composites[name] = category_scores[cats].mean(axis=1)
        composites.loc[category_scores[cats].isna().any(axis=1), name] = np.nan
        composites[f"{name}_percentile"] = composites[name].rank(pct=True)
    composites = composites.reset_index().merge(universe[["ticker", "info_long_name", "info_sector", "info_industry", "info_market_cap"]], on="ticker")
    composites.to_csv(args.output / "candidate_composites_current.csv", index=False)
    cat_corr = category_scores.corr(method="spearman")
    cat_corr.to_csv(args.output / "category_spearman_current.csv")
    eig = np.linalg.eigvalsh(corr.fillna(0).values)
    effective = float((eig.sum() ** 2) / np.square(eig).sum()) if np.square(eig).sum() else np.nan
    diagnostics = {"eligible_companies": len(universe), "primary_factor_sets": admitted, "effective_independent_signals_all_factors": effective,
                   "fundamental_coverage_companies": int(fundamental.fundamental_coverage_pass.sum()),
                   "snapshot_bytes": sum(p.stat().st_size for p in args.snapshot.rglob("*") if p.is_file()), "formula_version": FORMULA_VERSION,
                   "snapshot_manifest_sha256": sha(args.snapshot / "manifest.json"), "alias_mapping_sha256": sha(args.aliases)}
    distributions = long.groupby("factor")["raw_value"].agg(["count", "mean", "std", "min", "median", "max", "skew"]).reset_index()
    quantiles = long.groupby("factor")["raw_value"].quantile([.01, .05, .25, .75, .95, .99]).unstack().reset_index()
    quantiles.columns = ["factor", "p01", "p05", "p25", "p75", "p95", "p99"]
    distributions.merge(quantiles, on="factor").to_csv(args.output / "factor_distributions_current.csv", index=False)
    top_bottom = []
    exposure_rows = []
    for family in families:
        available = composites.dropna(subset=[family]).sort_values(family, ascending=False)
        for side, sample in [("top", available.head(20)), ("bottom", available.tail(20).sort_values(family))]:
            for _, row in sample.iterrows():
                top_bottom.append({"candidate": family, "side": side, "ticker": row.ticker, "name": row.info_long_name,
                                   "sector": row.info_sector, "market_cap": row.info_market_cap, "score": row[family]})
        top30 = available.head(30).copy()
        top30["market_cap_bucket"] = pd.cut(top30.info_market_cap, [2e9, 5e9, 10e9, 50e9, np.inf], labels=["2B-5B", "5B-10B", "10B-50B", ">50B"], right=False)
        for dimension in ["info_sector", "market_cap_bucket"]:
            for label, count in top30.groupby(dimension, observed=True).size().items():
                exposure_rows.append({"candidate": family, "research_cut": "top30_not_portfolio", "dimension": dimension,
                                      "label": label, "count": int(count), "fraction": count / len(top30) if len(top30) else np.nan})
    pd.DataFrame(top_bottom).to_csv(args.output / "top_bottom_current.csv", index=False)
    pd.DataFrame(exposure_rows).to_csv(args.output / "top30_exposure_diagnostics.csv", index=False)
    pct_columns = [f"{x}_percentile" for x in families]
    disagreements = composites.dropna(subset=pct_columns).copy()
    disagreements["rank_spread"] = disagreements[pct_columns].max(axis=1) - disagreements[pct_columns].min(axis=1)
    disagreements.sort_values("rank_spread", ascending=False).head(100).to_csv(args.output / "largest_candidate_disagreements.csv", index=False)
    ranking_concentration = []
    for family in families:
        top = composites.dropna(subset=[family]).nlargest(max(1, int(composites[family].notna().sum() * .1)), family)
        shares = top.groupby("info_sector").size() / len(top) if len(top) else pd.Series(dtype=float)
        ranking_concentration.append({"candidate": family, "scored": int(composites[family].notna().sum()), "top_decile_names": len(top),
                                      "top_decile_sector_hhi": float(np.square(shares).sum()) if len(shares) else None,
                                      "largest_sector_fraction": float(shares.max()) if len(shares) else None})
    pd.DataFrame(ranking_concentration).to_csv(args.output / "ranking_concentration.csv", index=False)
    (args.output / "checkpoint2_metrics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    output_files = []
    for path in sorted(p for p in args.output.iterdir() if p.is_file() and p.name != "analysis_manifest.json"):
        output_files.append({"path": path.name, "bytes": path.stat().st_size, "sha256": sha(path)})
    (args.output / "analysis_manifest.json").write_text(json.dumps({"snapshot": str(args.snapshot), "files": output_files}, indent=2) + "\n")
    print(json.dumps(diagnostics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
