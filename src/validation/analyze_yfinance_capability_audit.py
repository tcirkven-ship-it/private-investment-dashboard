#!/usr/bin/env python3
"""Analyze a Phase 1B yfinance capability snapshot without network access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


STATEMENT_ENDPOINTS = [
    "annual_income",
    "quarterly_income",
    "trailing_income",
    "annual_balance",
    "quarterly_balance",
    "annual_cashflow",
    "quarterly_cashflow",
    "trailing_cashflow",
]

ALL_FRAME_ENDPOINTS = STATEMENT_ENDPOINTS + [
    "history_daily",
    "actions",
    "shares_full",
    "earnings_history",
    "eps_revisions",
    "eps_trend",
    "revenue_estimate",
    "earnings_estimate",
    "recommendations",
    "recommendations_summary",
]

VALUATION_FIELDS = [
    "marketCap",
    "enterpriseValue",
    "trailingPE",
    "forwardPE",
    "priceToBook",
    "enterpriseToRevenue",
    "enterpriseToEbitda",
]

FIELD_ALIASES = {
    "revenue": ["TotalRevenue", "OperatingRevenue", "Total Revenue", "Operating Revenue"],
    "gross_profit": ["GrossProfit", "Gross Profit"],
    "operating_income": ["OperatingIncome", "TotalOperatingIncomeAsReported", "Operating Income", "Total Operating Income As Reported"],
    "ebit": ["EBIT", "OperatingIncome", "Operating Income"],
    "ebitda": ["EBITDA", "NormalizedEBITDA", "Normalized EBITDA"],
    "net_income": ["NetIncome", "NetIncomeCommonStockholders", "Net Income", "Net Income Common Stockholders"],
    "total_assets": ["TotalAssets", "Total Assets"],
    "stockholders_equity": ["StockholdersEquity", "CommonStockEquity", "TotalEquityGrossMinorityInterest", "Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"],
    "total_debt": ["TotalDebt", "LongTermDebtAndCapitalLeaseObligation", "Total Debt", "Long Term Debt And Capital Lease Obligation"],
    "cash": ["CashCashEquivalentsAndShortTermInvestments", "CashAndCashEquivalents", "CashFinancial", "Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents", "Cash Financial"],
    "interest_expense": ["InterestExpense", "InterestExpenseNonOperating", "Interest Expense", "Interest Expense Non Operating"],
    "operating_cash_flow": ["OperatingCashFlow", "TotalCashFromOperatingActivities", "Operating Cash Flow", "Total Cash From Operating Activities"],
    "capital_expenditure": ["CapitalExpenditure", "CapitalExpenditures", "Capital Expenditure", "Capital Expenditures"],
    "free_cash_flow": ["FreeCashFlow", "Free Cash Flow"],
    "ordinary_shares": ["OrdinarySharesNumber", "ShareIssued", "Ordinary Shares Number", "Share Issued"],
    "dividends_paid": ["CommonStockDividendPaid", "CashDividendsPaid", "Common Stock Dividend Paid", "Cash Dividends Paid"],
    "repurchases": ["RepurchaseOfCapitalStock", "RepurchaseOfStock", "Repurchase Of Capital Stock", "Repurchase Of Stock"],
    "issuance": ["IssuanceOfCapitalStock", "CommonStockIssuance", "IssuanceOfStock", "Issuance Of Capital Stock", "Common Stock Issuance", "Issuance Of Stock"],
}

FACTOR_DEFINITIONS = [
    ("roa", "net_income / average_total_assets", ["net_income", "total_assets"]),
    ("approx_roic", "EBIT / (debt + equity - cash)", ["ebit", "total_debt", "stockholders_equity", "cash"]),
    ("gross_profitability", "gross_profit / average_total_assets", ["gross_profit", "total_assets"]),
    ("operating_margin", "operating_income / revenue", ["operating_income", "revenue"]),
    ("free_cash_flow_margin", "free_cash_flow / revenue", ["free_cash_flow", "revenue"]),
    ("cash_conversion", "operating_cash_flow / net_income", ["operating_cash_flow", "net_income"]),
    ("debt_to_assets", "total_debt / total_assets", ["total_debt", "total_assets"]),
    ("net_debt_to_ebitda", "(total_debt - cash) / EBITDA", ["total_debt", "cash", "ebitda"]),
    ("interest_coverage", "EBIT / abs(interest_expense)", ["ebit", "interest_expense"]),
    ("share_dilution", "change in ordinary_shares", ["ordinary_shares"]),
    ("earnings_yield", "net_income / current_market_cap", ["net_income", "info:marketCap"]),
    ("free_cash_flow_yield", "free_cash_flow / current_market_cap", ["free_cash_flow", "info:marketCap"]),
    ("ebit_to_ev", "EBIT / current_enterprise_value", ["ebit", "info:enterpriseValue"]),
    ("sales_to_ev", "revenue / current_enterprise_value", ["revenue", "info:enterpriseValue"]),
    ("book_to_market", "stockholders_equity / current_market_cap", ["stockholders_equity", "info:marketCap"]),
    ("shareholder_yield", "(dividends + repurchases - issuance) / current_market_cap", ["dividends_paid", "repurchases", "issuance", "info:marketCap"]),
    ("revenue_growth", "latest annual revenue / prior annual revenue - 1", ["revenue", "periods:annual_income>=2"]),
    ("operating_income_growth", "latest annual operating_income / prior annual operating_income - 1", ["operating_income", "periods:annual_income>=2"]),
    ("net_income_growth", "latest annual net_income / prior annual net_income - 1", ["net_income", "periods:annual_income>=2"]),
    ("free_cash_flow_growth", "latest annual FCF / prior annual FCF - 1", ["free_cash_flow", "periods:annual_cashflow>=2"]),
    ("asset_growth", "latest total_assets / prior total_assets - 1", ["total_assets", "periods:annual_balance>=2"]),
    ("eps_revisions_current", "current EPS revisions table", ["endpoint:eps_revisions"]),
    ("eps_trend_current", "current EPS trend table", ["endpoint:eps_trend"]),
    ("revenue_estimate_current", "current revenue estimates table", ["endpoint:revenue_estimate"]),
    ("earnings_surprise_recent", "currently retrievable earnings-history surprises", ["endpoint:earnings_history"]),
]


def read_frame(ticker_dir: Path, endpoint: str) -> pd.DataFrame:
    path = ticker_dir / f"{endpoint}.csv"
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, index_col=0)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def read_info(ticker_dir: Path) -> dict[str, object]:
    path = ticker_dir / "info.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def conceptual_presence(frames: dict[str, pd.DataFrame], concept: str) -> bool:
    aliases = FIELD_ALIASES[concept]
    for endpoint in STATEMENT_ENDPOINTS:
        frame = frames[endpoint]
        for alias in aliases:
            if alias in frame.index and frame.loc[alias].notna().any():
                return True
    return False


def period_count(frame: pd.DataFrame) -> int:
    return int(frame.shape[1])


def period_bounds(frame: pd.DataFrame) -> tuple[str | None, str | None]:
    dates = pd.to_datetime(pd.Index(frame.columns), errors="coerce").dropna()
    if dates.empty:
        return None, None
    return str(dates.min().date()), str(dates.max().date())


def factor_available(requirements: list[str], frames: dict[str, pd.DataFrame], info: dict[str, object]) -> bool:
    for requirement in requirements:
        if requirement.startswith("info:"):
            value = info.get(requirement.split(":", 1)[1])
            if value is None or (isinstance(value, float) and not np.isfinite(value)):
                return False
        elif requirement.startswith("endpoint:"):
            if read_frame(Path(info["__ticker_dir"]), requirement.split(":", 1)[1]).empty:
                return False
        elif requirement.startswith("periods:"):
            payload = requirement.split(":", 1)[1]
            endpoint, minimum = payload.split(">=")
            if period_count(frames[endpoint]) < int(minimum):
                return False
        elif not conceptual_presence(frames, requirement):
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((args.snapshot / "manifest.json").read_text(encoding="utf-8"))
    sample = pd.read_csv(args.snapshot / "sample_universe.csv")
    sample_lookup = sample.set_index("ticker").to_dict(orient="index")
    ticker_rows: list[dict[str, object]] = []
    endpoint_rows: list[dict[str, object]] = []
    field_ticker_sets: dict[tuple[str, str], set[str]] = {}
    schema_sets: dict[str, list[frozenset[str]]] = {endpoint: [] for endpoint in STATEMENT_ENDPOINTS}
    factor_hits = {name: [] for name, _, _ in FACTOR_DEFINITIONS}

    for ticker in sample["ticker"].astype(str):
        ticker_dir = args.snapshot / "tickers" / ticker.replace("/", "_")
        ticker_manifest_path = ticker_dir / "ticker_manifest.json"
        ticker_manifest = json.loads(ticker_manifest_path.read_text(encoding="utf-8")) if ticker_manifest_path.exists() else {"errors": []}
        info = read_info(ticker_dir)
        info["__ticker_dir"] = str(ticker_dir)
        frames = {endpoint: read_frame(ticker_dir, endpoint) for endpoint in ALL_FRAME_ENDPOINTS}
        annual_periods = period_count(frames["annual_income"])
        quarterly_periods = period_count(frames["quarterly_income"])
        trailing_fields = int(frames["trailing_income"].notna().any(axis=1).sum()) if not frames["trailing_income"].empty else 0
        history = frames["history_daily"]
        actions = frames["actions"]
        shares = frames["shares_full"]
        annual_first, annual_last = period_bounds(frames["annual_income"])
        quarterly_first, quarterly_last = period_bounds(frames["quarterly_income"])
        fundamental_eligible = (
            info.get("country") == "United States"
            and str(info.get("quoteType", sample_lookup[ticker].get("quote_type", ""))).upper() == "EQUITY"
            and info.get("sector") not in {"Financial Services", "Real Estate"}
        )
        ticker_rows.append(
            {
                "ticker": ticker,
                "sample_sector": sample_lookup[ticker].get("sector_query"),
                "info_sector": info.get("sector"),
                "industry": info.get("industry"),
                "country": info.get("country"),
                "exchange": info.get("exchange"),
                "quote_type": info.get("quoteType"),
                "currency": info.get("currency"),
                "financial_currency": info.get("financialCurrency"),
                "market_cap_available": info.get("marketCap") is not None,
                "enterprise_value_available": info.get("enterpriseValue") is not None,
                "valuation_fields_available": sum(info.get(field) is not None for field in VALUATION_FIELDS),
                "annual_income_periods": annual_periods,
                "annual_income_first_period": annual_first,
                "annual_income_last_period": annual_last,
                "quarterly_income_periods": quarterly_periods,
                "quarterly_income_first_period": quarterly_first,
                "quarterly_income_last_period": quarterly_last,
                "annual_balance_periods": period_count(frames["annual_balance"]),
                "quarterly_balance_periods": period_count(frames["quarterly_balance"]),
                "annual_cashflow_periods": period_count(frames["annual_cashflow"]),
                "quarterly_cashflow_periods": period_count(frames["quarterly_cashflow"]),
                "trailing_income_fields": trailing_fields,
                "trailing_cashflow_fields": int(frames["trailing_cashflow"].notna().any(axis=1).sum()) if not frames["trailing_cashflow"].empty else 0,
                "share_history_rows": int(shares.shape[0]),
                "share_count_available": bool(not shares.empty or info.get("sharesOutstanding") is not None),
                "earnings_history_rows": int(frames["earnings_history"].shape[0]),
                "eps_revisions_rows": int(frames["eps_revisions"].shape[0]),
                "eps_trend_rows": int(frames["eps_trend"].shape[0]),
                "revenue_estimate_rows": int(frames["revenue_estimate"].shape[0]),
                "earnings_estimate_rows": int(frames["earnings_estimate"].shape[0]),
                "recommendation_rows": int(frames["recommendations"].shape[0]),
                "price_history_rows": int(history.shape[0]),
                "dividend_events": int((pd.to_numeric(actions.get("Dividends", pd.Series(dtype=float)), errors="coerce").fillna(0) != 0).sum()),
                "split_events": int((pd.to_numeric(actions.get("Stock Splits", pd.Series(dtype=float)), errors="coerce").fillna(0) != 0).sum()),
                "endpoint_errors": len(ticker_manifest.get("errors", [])),
                "fundamental_coverage_subset": fundamental_eligible,
            }
        )
        for endpoint, frame in frames.items():
            cells = int(frame.shape[0] * frame.shape[1])
            endpoint_rows.append(
                {
                    "ticker": ticker,
                    "endpoint": endpoint,
                    "rows": int(frame.shape[0]),
                    "columns": int(frame.shape[1]),
                    "total_cells": cells,
                    "nonmissing_cells": int(frame.notna().sum().sum()) if cells else 0,
                    "missing_fraction": float(frame.isna().sum().sum() / cells) if cells else None,
                    "nonempty": not frame.empty,
                }
            )
            if endpoint in STATEMENT_ENDPOINTS:
                schema_sets[endpoint].append(frozenset(str(field) for field in frame.index))
                for field in frame.index:
                    if frame.loc[field].notna().any():
                        field_ticker_sets.setdefault((endpoint, str(field)), set()).add(ticker)
        for name, _, requirements in FACTOR_DEFINITIONS:
            factor_hits[name].append((ticker, factor_available(requirements, frames, info), fundamental_eligible))

    ticker_frame = pd.DataFrame(ticker_rows)
    endpoint_frame = pd.DataFrame(endpoint_rows)
    ticker_frame.to_csv(args.output_dir / "yfinance_capability_ticker_coverage.csv", index=False)
    endpoint_frame.to_csv(args.output_dir / "yfinance_capability_endpoint_coverage_by_ticker.csv", index=False)

    endpoint_summary = (
        endpoint_frame.groupby("endpoint", as_index=False)
        .agg(
            tickers_nonempty=("nonempty", "sum"),
            mean_rows=("rows", "mean"),
            median_rows=("rows", "median"),
            mean_columns=("columns", "mean"),
            total_cells=("total_cells", "sum"),
            nonmissing_cells=("nonmissing_cells", "sum"),
        )
    )
    endpoint_summary["ticker_coverage"] = endpoint_summary["tickers_nonempty"] / len(sample)
    endpoint_summary["missing_fraction"] = 1 - endpoint_summary["nonmissing_cells"] / endpoint_summary["total_cells"].replace(0, np.nan)
    endpoint_summary["unique_field_schemas"] = endpoint_summary["endpoint"].map(
        lambda endpoint: len(set(schema_sets[endpoint])) if endpoint in schema_sets else np.nan
    )
    endpoint_summary["union_fields"] = endpoint_summary["endpoint"].map(
        lambda endpoint: len(set().union(*schema_sets[endpoint])) if endpoint in schema_sets and schema_sets[endpoint] else np.nan
    )
    endpoint_summary["intersection_fields"] = endpoint_summary["endpoint"].map(
        lambda endpoint: len(set.intersection(*(set(value) for value in schema_sets[endpoint]))) if endpoint in schema_sets and schema_sets[endpoint] else np.nan
    )
    endpoint_summary.to_csv(args.output_dir / "yfinance_endpoint_coverage_matrix.csv", index=False)

    field_rows = [
        {
            "endpoint": endpoint,
            "field": field,
            "tickers_with_nonmissing_field": len(tickers),
            "sample_size": len(sample),
            "coverage": len(tickers) / len(sample),
        }
        for (endpoint, field), tickers in sorted(field_ticker_sets.items())
    ]
    pd.DataFrame(field_rows).to_csv(args.output_dir / "yfinance_statement_field_coverage_matrix.csv", index=False)

    factor_rows = []
    factor_sector_rows = []
    sector_by_ticker = ticker_frame.set_index("ticker")["info_sector"].fillna(ticker_frame.set_index("ticker")["sample_sector"]).to_dict()
    for name, formula, requirements in FACTOR_DEFINITIONS:
        observations = factor_hits[name]
        all_covered = sum(covered for _, covered, _ in observations)
        subset = [(ticker, covered) for ticker, covered, eligible in observations if eligible]
        subset_covered = sum(covered for _, covered in subset)
        coverage = subset_covered / len(subset) if subset else 0.0
        sector_coverages = []
        for sector in sorted({sector_by_ticker[ticker] for ticker, _ in subset}):
            sector_values = [covered for ticker, covered in subset if sector_by_ticker[ticker] == sector]
            sector_coverage = sum(sector_values) / len(sector_values)
            sector_coverages.append(sector_coverage)
            factor_sector_rows.append(
                {
                    "factor": name,
                    "sector": sector,
                    "eligible_tickers": len(sector_values),
                    "covered_tickers": sum(sector_values),
                    "coverage": sector_coverage,
                }
            )
        minimum_sector_coverage = min(sector_coverages) if sector_coverages else 0.0
        if coverage >= 0.80 and minimum_sector_coverage >= 0.70:
            coverage_band = "core_candidate"
        elif coverage >= 0.60:
            coverage_band = "supplemental_only"
        else:
            coverage_band = "reject_sparse"
        factor_rows.append(
            {
                "factor": name,
                "formula": formula,
                "requirements": ";".join(requirements),
                "all_sample_covered": all_covered,
                "all_sample_coverage": all_covered / len(sample),
                "nonfinancial_us_subset_size": len(subset),
                "nonfinancial_us_covered": subset_covered,
                "nonfinancial_us_coverage": coverage,
                "minimum_included_sector_coverage": minimum_sector_coverage,
                "coverage_band": coverage_band,
            }
        )
    factor_frame = pd.DataFrame(factor_rows)
    factor_frame.to_csv(args.output_dir / "yfinance_factor_input_coverage_matrix.csv", index=False)
    pd.DataFrame(factor_sector_rows).to_csv(args.output_dir / "yfinance_factor_sector_coverage_matrix.csv", index=False)

    currency_counts = ticker_frame["financial_currency"].fillna("MISSING").value_counts().to_dict()
    summary = {
        "experiment_id": "EXP-0012",
        "snapshot": str(args.snapshot),
        "yfinance_version": manifest["yfinance_version"],
        "retrieved_at_utc": manifest["completed_at_utc"],
        "sample_size": int(len(sample)),
        "sectors": ticker_frame["sample_sector"].value_counts().to_dict(),
        "tickers_with_any_endpoint_error": int((ticker_frame["endpoint_errors"] > 0).sum()),
        "total_endpoint_errors": int(ticker_frame["endpoint_errors"].sum()),
        "financial_currency_counts": currency_counts,
        "median_annual_periods": float(ticker_frame["annual_income_periods"].median()),
        "median_quarterly_periods": float(ticker_frame["quarterly_income_periods"].median()),
        "nonfinancial_us_coverage_subset": int(ticker_frame["fundamental_coverage_subset"].sum()),
        "endpoint_coverage": endpoint_summary.set_index("endpoint")["ticker_coverage"].to_dict(),
        "factor_coverage_bands": factor_frame.groupby("coverage_band")["factor"].apply(list).to_dict(),
        "classification": "Exploratory non-point-in-time fundamental capability analysis using currently retrievable and potentially restated Yahoo Finance data.",
        "limitations": manifest["limitations"],
    }
    (args.output_dir / "yfinance_capability_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "complete", "sample_size": len(sample), "output": str(args.output_dir)}))


if __name__ == "__main__":
    main()
