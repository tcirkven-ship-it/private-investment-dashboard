"""One-command current YF-QVP ranking and decision-support scanner."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import shutil
import subprocess
import sys
from datetime import datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "research/configs/daily_qvp_v1.json"
DEFAULT_DATA_ROOT = ROOT / "data/prospective/daily_qvp/snapshots"
DEFAULT_OUTPUT_ROOT = ROOT / "outputs/daily_qvp_runs"
FINAL = ROOT / "outputs/final"
OLD_698_TICKERS = ROOT / "outputs/experiment_runs/EXP-0014/candidate_composites_current.csv"
NY = ZoneInfo("America/New_York")
FORBIDDEN_PUBLISH_RUN_TOKENS = ("smoke", "mechanics", "rehearsal", "fixture", "test")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def run_id_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def git_commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                          text=True, capture_output=True).stdout.strip()


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("UTC timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def publication_run_id_valid(run_id: str) -> bool:
    lowered = run_id.lower()
    return bool(run_id) and not any(token in lowered for token in FORBIDDEN_PUBLISH_RUN_TOKENS)


def validate_publication(run_id: str, invoked_at: datetime, raw_manifest: dict,
                         snapshot: Path, analysis: Path, base: pd.DataFrame,
                         ranking: pd.DataFrame, internal_retrieval: bool) -> None:
    if not internal_retrieval:
        raise RuntimeError("External/cached snapshots cannot publish compact current outputs")
    if not publication_run_id_valid(run_id):
        raise RuntimeError(f"Rehearsal/smoke run ID cannot publish: {run_id}")
    retrieval_started = parse_utc(str(raw_manifest["started_at_utc"]))
    if retrieval_started < invoked_at.astimezone(timezone.utc):
        raise RuntimeError("Source snapshot predates scanner invocation")
    eligible_tickers, ranking_tickers = set(base.ticker.astype(str)), set(ranking.ticker.astype(str))
    if len(ranking) != len(base) or ranking_tickers != eligible_tickers:
        raise RuntimeError("Published ranking must contain exactly one row per current eligible ticker")
    unscored = ranking[ranking.qvp_score.isna()]
    if len(unscored) and (~unscored.data_quality_flags.str.contains("missing_", na=False)).any():
        raise RuntimeError("Every unscored eligible row requires a documented missing-score reason")
    analysis_manifest = json.loads((analysis / "analysis_manifest.json").read_text())
    recorded = Path(str(analysis_manifest["snapshot"])).resolve()
    if recorded != snapshot.resolve():
        raise RuntimeError("Analysis manifest does not point to the current source snapshot")


def completed_session_cutoff(now: datetime | None = None) -> pd.Timestamp:
    current = (now or datetime.now(timezone.utc)).astimezone(NY)
    local_date = pd.Timestamp(current.date())
    if current.weekday() >= 5 or current.time() < time(16, 15):
        return local_date - pd.Timedelta(days=1)
    return local_date


def latest_completed_session(benchmark_csv: Path, now: datetime | None = None) -> pd.Timestamp:
    frame = pd.read_csv(benchmark_csv, index_col=0)
    dates = pd.to_datetime(frame.index, utc=True, errors="coerce").tz_convert(None).normalize()
    close = pd.to_numeric(frame.get("Close"), errors="coerce")
    valid = pd.Series(close.to_numpy(), index=dates).dropna()
    valid = valid[valid > 0]
    cutoff = completed_session_cutoff(now)
    eligible = valid[valid.index <= cutoff]
    if eligible.empty:
        raise RuntimeError("No completed benchmark session available")
    return pd.Timestamp(eligible.index.max()).normalize()


def select_constrained(ranking: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    spec = config["strategy"]
    size = int(spec["portfolio_size"])
    sector_cap, industry_cap = float(spec["sector_cap"]), float(spec["industry_cap"])
    selected_rows, exclusions = [], []
    sector_counts: dict[str, int] = {}
    industry_counts: dict[str, int] = {}
    scoreable = ranking.dropna(subset=["qvp_score"]).sort_values(
        ["qvp_score", "ticker"], ascending=[False, True]
    )
    for _, row in scoreable.iterrows():
        sector = str(row["sector"])
        industry = str(row["industry"])
        sector_block = (sector_counts.get(sector, 0) + 1) / size > sector_cap + 1e-12
        industry_block = (industry_counts.get(industry, 0) + 1) / size > industry_cap + 1e-12
        if sector_block or industry_block:
            exclusions.append({
                "ticker": row.ticker,
                "unconstrained_rank": int(row.unconstrained_rank),
                "reason": "sector_cap" if sector_block else "industry_cap",
                "sector": sector,
                "industry": industry,
                "would_be_unconstrained_top30": bool(row.unconstrained_rank <= size),
            })
            continue
        selected_rows.append(row)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        industry_counts[industry] = industry_counts.get(industry, 0) + 1
        if len(selected_rows) == size:
            break
    if len(selected_rows) != size:
        raise RuntimeError(f"Only {len(selected_rows)} stocks satisfy the frozen caps")
    portfolio = pd.DataFrame(selected_rows).reset_index(drop=True)
    portfolio["portfolio_rank"] = np.arange(1, len(portfolio) + 1)
    portfolio["target_weight"] = 1 / size
    portfolio["selection_reason"] = np.where(
        portfolio["unconstrained_rank"] <= size,
        "unconstrained_top_30",
        "constraint_replacement",
    )
    return portfolio, pd.DataFrame(exclusions)


def frozen_current_scores(analysis: Path, universe: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Rebuild category/model scores from the explicitly frozen factor lists."""
    factors = pd.read_csv(analysis / "factor_level_current.csv", usecols=["ticker", "factor", "percentile_rank"])
    ranks = factors.pivot(index="ticker", columns="factor", values="percentile_rank")
    spec = config["strategy"]
    category_factors = {
        "Quality": spec["quality_factors"],
        "Value": spec["value_factors"],
        "Price": spec["price_factors"],
        "Growth": spec["growth_factors"],
    }
    categories = pd.DataFrame(index=ranks.index)
    for category, names in category_factors.items():
        missing_columns = [name for name in names if name not in ranks.columns]
        if missing_columns:
            raise RuntimeError(f"Frozen factors absent from calculation: {missing_columns}")
        categories[category] = ranks[names].mean(axis=1)
        categories.loc[ranks[names].isna().any(axis=1), category] = np.nan
    models = {"YF-P": ["Price"], "YF-QP": ["Quality", "Price"],
              "YF-QVP": ["Quality", "Value", "Price"],
              "YF-QVGP": ["Quality", "Value", "Growth", "Price"]}
    result = pd.DataFrame(index=ranks.index)
    for model, names in models.items():
        result[model] = categories[names].mean(axis=1)
        result.loc[categories[names].isna().any(axis=1), model] = np.nan
        result[f"{model}_percentile"] = result[model].rank(pct=True)
    result = result.join(categories).reset_index()
    return result.merge(universe[["ticker", "info_long_name", "info_sector", "info_industry",
                                  "info_market_cap", "latest_close"]], on="ticker", how="right")


def previous_ranking(output_root: Path, current_run_id: str) -> tuple[pd.DataFrame | None, str | None]:
    candidates = []
    if output_root.exists():
        for path in output_root.glob("*/ranking.csv"):
            manifest_path = path.parent / "manifest.json"
            if path.parent.name == current_run_id or not manifest_path.exists() or not publication_run_id_valid(path.parent.name):
                continue
            try:
                manifest = json.loads(manifest_path.read_text())
            except json.JSONDecodeError:
                continue
            if manifest.get("classification") == "current_decision_support_integrity_passed":
                candidates.append(path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=lambda p: p.parent.name)[-1]
    return pd.read_csv(path), path.parent.name


def build_changes(current: pd.DataFrame, previous: pd.DataFrame | None) -> tuple[pd.DataFrame, dict]:
    frame = current.copy()
    if previous is None:
        frame["previous_rank"] = np.nan
        frame["rank_change"] = np.nan
        return frame, {
            "previous_run": None,
            "new_top30": [], "left_top30": [], "crossed_below_60": [],
            "largest_improvements": [], "largest_deteriorations": [],
            "largest_qvp_score_changes": [], "factor_score_changes": [], "sector_exposure_changes": [],
            "newly_missing": [], "newly_eligible": [], "newly_ineligible": [],
            "note": "First daily-scanner run; no prior daily snapshot was substituted.",
        }
    prior = previous.set_index("ticker")
    frame["previous_rank"] = frame.ticker.map(prior.get("unconstrained_rank", pd.Series(dtype=float)))
    frame["rank_change"] = frame["previous_rank"] - frame["unconstrained_rank"]
    current_ranks = frame.set_index("ticker")["unconstrained_rank"]
    prior_ranks = prior["unconstrained_rank"]
    common = current_ranks.index.intersection(prior_ranks.index)
    moves = frame.dropna(subset=["rank_change"]).sort_values("rank_change", ascending=False)
    newly_missing = frame.loc[
        frame.qvp_score.isna() & frame.ticker.map(prior.get("qvp_score", pd.Series(dtype=float))).notna(), "ticker"
    ].tolist()
    frame["qvp_score_change"] = frame.qvp_score - frame.ticker.map(prior.get("qvp_score", pd.Series(dtype=float)))
    score_moves = frame.dropna(subset=["qvp_score_change"]).assign(
        absolute_change=lambda x: x.qvp_score_change.abs()
    ).nlargest(10, "absolute_change")
    factor_columns = ["quality_score", "value_score", "price_score", "qvp_score"]
    for column in factor_columns:
        frame[f"{column}_change"] = frame[column] - frame.ticker.map(prior.get(column, pd.Series(dtype=float)))
    factor_moves = frame.assign(
        maximum_factor_change=frame[[f"{column}_change" for column in factor_columns]].abs().max(axis=1)
    ).nlargest(10, "maximum_factor_change")
    current_exposure = frame[frame.constrained_portfolio_status.eq("SELECTED")].groupby("sector").size() / 30
    prior_exposure = previous[previous.constrained_portfolio_status.eq("SELECTED")].groupby("sector").size() / 30
    sector_changes = (current_exposure.subtract(prior_exposure, fill_value=0)).sort_values(key=abs, ascending=False)
    return frame, {
        "new_top30": sorted([t for t in current_ranks[current_ranks <= 30].index if t not in prior_ranks.index or prior_ranks.get(t, np.inf) > 30]),
        "left_top30": sorted([t for t in prior_ranks[prior_ranks <= 30].index if t not in current_ranks.index or current_ranks.get(t, np.inf) > 30]),
        "crossed_below_60": sorted([t for t in common if prior_ranks[t] <= 60 < current_ranks[t]]),
        "largest_improvements": moves.head(10)[["ticker", "rank_change"]].to_dict(orient="records"),
        "largest_deteriorations": moves.tail(10).sort_values("rank_change")[["ticker", "rank_change"]].to_dict(orient="records"),
        "largest_qvp_score_changes": score_moves[["ticker", "qvp_score_change"]].to_dict(orient="records"),
        "factor_score_changes": factor_moves[["ticker"] + [f"{column}_change" for column in factor_columns]].to_dict(orient="records"),
        "sector_exposure_changes": [{"sector": sector, "target_weight_change": value}
                                    for sector, value in sector_changes.items() if abs(value) > 1e-12],
        "newly_missing": newly_missing,
        "newly_eligible": sorted(set(current_ranks.index) - set(prior_ranks.index)),
        "newly_ineligible": sorted(set(prior_ranks.index) - set(current_ranks.index)),
    }


def load_holdings(path: Path | None) -> tuple[pd.DataFrame, float]:
    columns = ["ticker", "shares", "average_cost", "last_update_date"]
    if path is None:
        return pd.DataFrame(columns=columns), 0.0
    frame = pd.read_csv(path)
    if not {"ticker", "shares"}.issubset(frame.columns):
        raise ValueError("Holdings CSV requires ticker and shares columns")
    frame["ticker"] = frame.ticker.astype(str).str.upper().str.strip()
    frame["shares"] = pd.to_numeric(frame.shares, errors="raise")
    if (frame.shares < 0).any():
        raise ValueError("Holdings shares cannot be negative")
    cash = float(pd.to_numeric(frame.get("cash", pd.Series(dtype=float)), errors="coerce").dropna().iloc[0]) if "cash" in frame and frame.cash.notna().any() else 0.0
    cash_rows = frame.ticker.eq("CASH")
    if cash_rows.any():
        cash += float(frame.loc[cash_rows, "shares"].sum())
        frame = frame.loc[~cash_rows].copy()
    return frame, cash


def holdings_analysis(holdings: pd.DataFrame, ranking: pd.DataFrame, portfolio: pd.DataFrame,
                      universe_report: pd.DataFrame) -> pd.DataFrame:
    rank_lookup = ranking.set_index("ticker")
    selected = set(portfolio.ticker)
    eligible = set(ranking.ticker)
    rows = []
    held = set(holdings.ticker)
    for _, holding in holdings.iterrows():
        ticker = holding.ticker
        rank = rank_lookup.loc[ticker, "unconstrained_rank"] if ticker in rank_lookup.index else np.nan
        qvp = rank_lookup.loc[ticker, "qvp_score"] if ticker in rank_lookup.index else np.nan
        if ticker not in eligible:
            classification, reason = "REVIEW", "not_in_current_eligible_universe"
        elif pd.isna(qvp):
            classification, reason = "DATA OR CORPORATE-ACTION REVIEW", "required_score_input_missing"
        elif rank <= 30:
            classification, reason = "HOLD", "ranked_within_top_30"
        elif rank <= 60:
            classification, reason = "HOLD", "eligible_within_rank_60_buffer"
        else:
            classification, reason = "MODEL EXIT", "rank_below_60"
        rows.append({**holding.to_dict(), "unconstrained_rank": rank, "qvp_score": qvp,
                     "in_constrained_model": ticker in selected, "classification": classification, "reason": reason})
    for _, row in portfolio[~portfolio.ticker.isin(held)].iterrows():
        rows.append({"ticker": row.ticker, "shares": 0.0, "average_cost": np.nan,
                     "last_update_date": None, "unconstrained_rank": row.unconstrained_rank,
                     "qvp_score": row.qvp_score, "in_constrained_model": True,
                     "classification": "BUY/ADD CANDIDATE", "reason": "new_constrained_top_30_model_name"})
    return pd.DataFrame(rows)


def contribution_allocation(amount: float, portfolio: pd.DataFrame, holdings: pd.DataFrame,
                            cash: float, max_names: int = 3) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    if amount < 0 or not math.isfinite(amount):
        raise ValueError("Contribution must be finite and nonnegative")
    shares = holdings.set_index("ticker")["shares"].to_dict() if len(holdings) else {}
    work = portfolio.copy()
    work["current_shares"] = work.ticker.map(shares).fillna(0.0)
    work["current_value"] = work.current_shares * work.latest_close
    nav_after = float(work.current_value.sum() + cash + amount)
    target_value = nav_after / len(work) if len(work) else 0.0
    work["target_value_after_contribution"] = target_value
    work["underweight"] = (target_value - work.current_value).clip(lower=0)
    candidates = work[work.latest_close.gt(0) & work.underweight.gt(0)].sort_values(
        ["underweight", "portfolio_rank"], ascending=[False, True]
    ).head(max_names).copy()
    if amount == 0 or candidates.empty:
        candidates["allocation"] = 0.0
    else:
        candidates["allocation"] = amount * candidates.underweight / candidates.underweight.sum()
    candidates["illustrative_fractional_shares"] = candidates.allocation / candidates.latest_close
    candidates["method"] = "up_to_three_largest_underweights"
    residual = max(0.0, amount - float(candidates.allocation.sum()))
    one = work[work.latest_close.gt(0) & work.underweight.gt(0)].sort_values(
        ["underweight", "portfolio_rank"], ascending=[False, True]
    ).head(1).copy()
    one["allocation"] = amount if len(one) else 0.0
    one["illustrative_fractional_shares"] = one.allocation / one.latest_close if len(one) else np.nan
    one["method"] = "single_largest_underweight_alternative"
    columns = ["ticker", "portfolio_rank", "latest_close", "current_value", "target_value_after_contribution",
               "underweight", "allocation", "illustrative_fractional_shares", "method"]
    return candidates[columns], one[columns], residual


def universe_table(snapshot: Path, score_session: pd.Timestamp) -> pd.DataFrame:
    screened = pd.read_csv(snapshot / "screened_universe.csv")
    eligibility = pd.read_csv(snapshot / "eligibility_and_exclusions.csv")
    merged = screened.merge(eligibility, on="ticker", how="left", suffixes=("_screen", ""))
    merged["eligible"] = merged.ticker.isin(set(pd.read_csv(snapshot / "base_eligible_universe.csv").ticker))
    fallback = pd.Series(
        np.where(merged["eligible"], "", "below_2b_preliminary_threshold_or_not_enriched"),
        index=merged.index,
    )
    merged["exclusion_reason"] = merged["first_exclusion_reason"].fillna(fallback)
    merged["score_session"] = str(score_session.date())
    return merged


def build_reconciliation(snapshot: Path, ranking: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Compare only after current scoring; the old set is never a score input."""
    old = set(pd.read_csv(OLD_698_TICKERS, usecols=["ticker"]).ticker.astype(str))
    current = set(ranking.ticker.astype(str))
    eligibility = pd.read_csv(snapshot / "eligibility_and_exclusions.csv").set_index("ticker")
    rows = []
    for ticker in sorted(old | current):
        if ticker in old and ticker in current:
            classification, reason = "overlap", "eligible_in_both_retrievals"
        elif ticker in current:
            classification = "new_addition"
            reason = "recovered_by_essential_field_and_504_observation_retries_after_old_silent_enrichment_failure"
        else:
            classification = "removed"
            reason = (str(eligibility.loc[ticker, "first_exclusion_reason"])
                      if ticker in eligibility.index else "not_returned_by_current_screen")
        qvp = ranking.loc[ranking.ticker.eq(ticker), "qvp_score"]
        rows.append({"ticker": ticker, "old_698_eligible": ticker in old,
                     "current_eligible": ticker in current, "classification": classification,
                     "discrepancy_reason": reason,
                     "current_qvp_scored": bool(len(qvp) and qvp.notna().iloc[0])})
    frame = pd.DataFrame(rows)
    waterfall = pd.read_csv(snapshot / "eligibility_waterfall.csv").to_dict(orient="records")
    summary = {"old_eligible_count": len(old), "corrected_retrieval_eligible_count": len(current),
               "fully_qvp_scored_count": int(ranking.qvp_score.notna().sum()),
               "overlap_with_old_698": len(old & current), "new_additions": len(current - old),
               "removed_names": len(old - current), "stage_by_stage_counts": waterfall}
    return frame, summary


def latest_history_dates(snapshot: Path, tickers: list[str], score_session: pd.Timestamp) -> dict[str, str | None]:
    result = {}
    for ticker in tickers:
        path = snapshot / "tickers" / ticker.replace("/", "_") / "history_daily.csv"
        if not path.exists():
            result[ticker] = None
            continue
        frame = pd.read_csv(path, index_col=0, usecols=[0, 4])
        dates = pd.to_datetime(frame.index, utc=True, errors="coerce").tz_convert(None).normalize()
        close = pd.to_numeric(frame.iloc[:, 0], errors="coerce")
        valid = dates[(close.notna().to_numpy()) & (dates <= score_session)]
        result[ticker] = str(valid.max().date()) if len(valid) else None
    return result


def markdown_table(frame: pd.DataFrame, decimals: int = 4) -> str:
    if frame.empty:
        return "No rows."
    columns = [str(column) for column in frame.columns]
    rows = []
    for values in frame.itertuples(index=False, name=None):
        rendered = []
        for value in values:
            if pd.isna(value):
                rendered.append("")
            elif isinstance(value, (float, np.floating)):
                rendered.append(f"{float(value):.{decimals}f}")
            else:
                rendered.append(str(value).replace("|", "\\|"))
        rows.append(rendered)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    return "\n".join([header, separator] + ["| " + " | ".join(row) + " |" for row in rows])


def attach_metadata(frame: pd.DataFrame, metadata: dict) -> pd.DataFrame:
    result = frame.copy()
    for key, value in reversed(list(metadata.items())):
        if key in result.columns:
            result[key] = value
        else:
            result.insert(0, key, value)
    return result


def markdown_report(run_id: str, manifest: dict, ranking: pd.DataFrame, portfolio: pd.DataFrame,
                    exposures: pd.DataFrame, changes: dict, allocations: dict[float, pd.DataFrame],
                    warnings: list[str], holdings: pd.DataFrame,
                    constraint_exclusions: pd.DataFrame) -> str:
    qvp_count = int(ranking.qvp_score.notna().sum())
    p_top = set(ranking.dropna(subset=["price_score"]).nsmallest(30, "price_rank").ticker)
    overlap = len(set(portfolio.ticker) & p_top)
    if changes.get("note"):
        change_text = changes["note"]
    else:
        improvements = ", ".join(f"{x['ticker']} +{x['rank_change']:.0f}" for x in changes["largest_improvements"][:5]) or "none"
        deteriorations = ", ".join(f"{x['ticker']} {x['rank_change']:.0f}" for x in changes["largest_deteriorations"][:5]) or "none"
        score_moves = ", ".join(f"{x['ticker']} {x['qvp_score_change']:+.4f}" for x in changes["largest_qvp_score_changes"][:5]) or "none"
        change_text = (f"Entrants to top 30: {', '.join(changes['new_top30']) or 'none'}. Departures: {', '.join(changes['left_top30']) or 'none'}. "
                       f"Rank-60 downward crosses: {', '.join(changes['crossed_below_60']) or 'none'}. "
                       f"Largest improvements: {improvements}. Largest deteriorations: {deteriorations}. "
                       f"Largest QVP score changes: {score_moves}. Newly missing: {', '.join(changes['newly_missing']) or 'none'}.")
    lines = [
        "# Current daily YF-QVP decision-support report", "",
        f"**Run:** `{run_id}`  ",
        f"**Retrieval start:** {manifest.get('started_at_utc')}  ",
        f"**Retrieval finish:** {manifest.get('completed_at_utc')}  ",
        f"**Latest completed score session:** {manifest.get('score_session')}  ",
        f"**Source snapshot:** `{manifest.get('source_snapshot_path')}`  ",
        f"**Universe:** {manifest.get('screened_unique_tickers')} screened; {manifest.get('base_eligible_tickers')} eligible; {qvp_count} fully scored for YF-QVP.  ",
        f"**Code commit:** `{manifest.get('code_commit')}`  ",
        f"**Configuration SHA-256:** `{manifest.get('configuration_sha256')}`  ",
        f"**Output manifest identity SHA-256:** `{manifest.get('output_manifest_sha256')}`  ",
        "**Classification:** current decision-support research; not prospective performance evidence and not a trade instruction.", "",
        "## Universe reconciliation", "",
        (f"Old eligible: {manifest['reconciliation']['old_eligible_count']}; corrected current eligible: {manifest['reconciliation']['corrected_retrieval_eligible_count']}; "
         f"fully QVP-scored: {manifest['reconciliation']['fully_qvp_scored_count']}; overlap: {manifest['reconciliation']['overlap_with_old_698']}; "
         f"additions: {manifest['reconciliation']['new_additions']}; removed: {manifest['reconciliation']['removed_names']}.") , "",
        markdown_table(pd.DataFrame(manifest["reconciliation"]["stage_by_stage_counts"])), "",
        "## Model", "",
        "YF-QVP averages frozen Quality, Value and Price category percentiles. The model portfolio contains 30 equal-target names subject to 25% sector and 15% industry caps. Scores can run on demand; review and transaction timing remain user choices.", "",
        "## Constrained top 30", "",
        markdown_table(portfolio[["portfolio_rank", "ticker", "company_name", "sector", "industry", "unconstrained_rank", "qvp_score", "target_weight", "selection_reason"]]), "",
        "## Portfolio-constraint effects", "",
        markdown_table(constraint_exclusions[constraint_exclusions.would_be_unconstrained_top30].head(20)) if len(constraint_exclusions) else "No score-leading name was excluded by a portfolio cap.", "",
        "## Exposure", "", markdown_table(exposures), "",
        "## Comparison with YF-P", "",
        f"The constrained YF-QVP portfolio overlaps the unconstrained YF-P top 30 in {overlap} names. This is a current cross-sectional comparison, not a return result.", "",
        "## Change from previous daily run", "",
        change_text, "",
        "## Contribution illustrations", "",
    ]
    for amount, frame in allocations.items():
        names = ", ".join(f"{r.ticker} ${r.allocation:,.2f} ({r.illustrative_fractional_shares:.4f} shares)" for r in frame.itertuples())
        residual = amount - float(frame.allocation.sum()) if len(frame) else amount
        lines.append(f"- USD {amount:,.0f}: {names or 'no allocation; contribution is zero'}; residual cash ${residual:,.2f}")
    lines += ["", "## Holdings analysis", ""]
    lines.append(markdown_table(holdings) if len(holdings) else "No holdings file was supplied; no personal holdings classification was generated.")
    lines += ["", "## Data-quality warnings", ""] + [f"- {warning}" for warning in warnings]
    lines += ["", "## Limitations", "",
              "The complete QVP model cannot receive a reliable long historical backtest from yfinance alone because point-in-time market capitalization, enterprise value and valuation vintages are unavailable. Current fundamentals may be restated; the current universe is not a historical universe and excludes inactive/delisted names.", "",
              "This model portfolio is not proven to outperform SPY or QQQ and is not personalized investment advice. The user decides whether and when to trade.", ""]
    return "\n".join(lines)


def simple_html(markdown: str, portfolio: pd.DataFrame, exposures: pd.DataFrame) -> str:
    paragraphs = "\n".join(f"<p>{html.escape(line)}</p>" for line in markdown.splitlines() if line and not line.startswith("#") and not line.startswith("|"))
    return ("<!doctype html><html><head><meta charset='utf-8'><title>Daily YF-QVP</title>"
            "<style>body{font-family:system-ui;max-width:1200px;margin:2rem auto;padding:0 1rem}"
            "table{border-collapse:collapse;width:100%;font-size:13px}th,td{border:1px solid #ddd;padding:6px;text-align:left}th{background:#eee}</style>"
            "</head><body><h1>Current daily YF-QVP decision-support report</h1>" + paragraphs +
            "<h2>Constrained top 30</h2>" + portfolio.to_html(index=False, float_format=lambda x: f"{x:.4f}") +
            "<h2>Exposure</h2>" + exposures.to_html(index=False, float_format=lambda x: f"{x:.4f}") + "</body></html>")


def run(args: argparse.Namespace) -> dict:
    invoked_at = datetime.now(timezone.utc)
    config = json.loads(args.config.read_text())
    run_id = args.run_id or (args.snapshot.parent.name if args.snapshot else run_id_now())
    snapshot = args.snapshot or (args.data_root / run_id / "raw")
    analysis = snapshot.parent / "analysis"
    output = args.output_root / run_id
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"Refusing to overwrite immutable run {output}")
    output.mkdir(parents=True, exist_ok=True)
    if args.snapshot is None:
        command = [sys.executable, str(ROOT / "src/data/pull_yfinance_full_universe.py"),
                   "--output", str(snapshot), "--attempts", str(args.attempts),
                   "--workers", str(args.workers), "--delay-seconds", str(args.delay_seconds),
                   "--endpoint-delay-seconds", str(args.endpoint_delay_seconds),
                   "--scoring-core-only",
                   "--maximum-scoring-core-incomplete", str(args.maximum_scoring_core_incomplete)]
        if args.resume_retrieval:
            command.append("--resume")
        subprocess.run(command, cwd=ROOT, check=True)
    score_session = latest_completed_session(snapshot / "benchmarks/SPY_history_daily.csv")
    if analysis.exists() and any(analysis.iterdir()) and not args.reuse_analysis:
        raise RuntimeError(f"Refusing to overwrite analysis {analysis}")
    if not analysis.exists() or not any(analysis.iterdir()):
        subprocess.run([sys.executable, str(ROOT / "src/validation/run_yfinance_checkpoint2.py"),
                        "--snapshot", str(snapshot), "--output", str(analysis),
                        "--as-of-session", str(score_session.date())], cwd=ROOT, check=True)

    base = pd.read_csv(snapshot / "base_eligible_universe.csv")
    frozen = frozen_current_scores(analysis, base, config)
    ranking = frozen.rename(columns={"info_long_name": "company_name", "info_sector": "sector", "info_industry": "industry",
                      "Quality": "quality_score", "Value": "value_score", "Price": "price_score",
                      "YF-QVP": "qvp_score", "YF-P": "yf_p_score"})
    ranking = ranking.sort_values(["qvp_score", "ticker"], ascending=[False, True], na_position="last").reset_index(drop=True)
    ranking["unconstrained_rank"] = ranking.qvp_score.rank(method="first", ascending=False)
    ranking["price_rank"] = ranking.price_score.rank(method="first", ascending=False)
    dates = latest_history_dates(snapshot, ranking.ticker.tolist(), score_session)
    ranking["latest_price_session"] = ranking.ticker.map(dates)
    ranking["data_quality_flags"] = ranking.apply(
        lambda r: ";".join(x for x in [
            "missing_quality" if pd.isna(r.quality_score) else "",
            "missing_value" if pd.isna(r.value_score) else "",
            "missing_price" if pd.isna(r.price_score) else "",
            "stale_price" if r.latest_price_session != str(score_session.date()) else "",
        ] if x) or "none", axis=1)
    portfolio, constraint_exclusions = select_constrained(ranking, config)
    selected = set(portfolio.ticker)
    excluded_sector = set(constraint_exclusions.loc[constraint_exclusions.reason.eq("sector_cap"), "ticker"]) if len(constraint_exclusions) else set()
    excluded_industry = set(constraint_exclusions.loc[constraint_exclusions.reason.eq("industry_cap"), "ticker"]) if len(constraint_exclusions) else set()
    ranking["constrained_portfolio_status"] = ranking.ticker.map(
        lambda t: "SELECTED" if t in selected else ("SKIPPED_SECTOR_CAP" if t in excluded_sector else ("SKIPPED_INDUSTRY_CAP" if t in excluded_industry else "NOT_SELECTED"))
    )
    ranking.loc[ranking.qvp_score.isna(), "constrained_portfolio_status"] = "UNSCORED"
    previous, previous_id = previous_ranking(args.output_root, run_id)
    ranking, changes = build_changes(ranking, previous)
    changes["previous_run"] = previous_id
    universe = universe_table(snapshot, score_session)
    holdings, cash = load_holdings(args.holdings)
    holdings_report = holdings_analysis(holdings, ranking, portfolio, universe) if args.holdings else pd.DataFrame()

    allocations: dict[float, pd.DataFrame] = {}
    allocation_rows = []
    for amount in sorted(set([0.0, 250.0, 500.0, 1000.0, 5000.0, float(args.contribution)])):
        multi, one, residual = contribution_allocation(amount, portfolio, holdings, cash, int(config["strategy"]["contribution_max_names"]))
        allocations[amount] = multi
        for frame in [multi, one]:
            if len(frame):
                temp = frame.copy(); temp.insert(0, "contribution_amount", amount); temp["residual_cash"] = residual
                allocation_rows.append(temp)
    allocations_all = pd.concat(allocation_rows, ignore_index=True) if allocation_rows else pd.DataFrame()
    exposure_rows = []
    for dimension in ["sector", "industry"]:
        for label, group in portfolio.groupby(dimension):
            exposure_rows.append({"dimension": dimension, "label": label, "names": len(group),
                                  "target_weight": float(group.target_weight.sum())})
    exposures = pd.DataFrame(exposure_rows)
    warnings = [
        f"{int((ranking.data_quality_flags != 'none').sum())} eligible stocks have at least one score or price-freshness flag.",
        f"{int(ranking.qvp_score.isna().sum())} eligible stocks lack a complete YF-QVP score and are not ranked for selection.",
        "Fundamental and valuation fields are current retrieval-time observations, not historical point-in-time vintages.",
        "Yahoo classifications and active security coverage can change and do not include a reliable delisting history.",
    ]
    raw_manifest = json.loads((snapshot / "manifest.json").read_text())
    raw_manifest["score_session"] = str(score_session.date())
    raw_manifest["daily_scanner_run_id"] = run_id
    raw_manifest["source_snapshot_path"] = display_path(snapshot)
    raw_manifest["code_commit"] = git_commit()
    raw_manifest["configuration_sha256"] = sha256(args.config)
    raw_manifest["eligible_count"] = len(ranking)
    raw_manifest["scored_count"] = int(ranking.qvp_score.notna().sum())
    validate_publication(run_id, invoked_at, raw_manifest, snapshot, analysis, base, ranking,
                         internal_retrieval=args.snapshot is None)
    reconciliation, reconciliation_summary = build_reconciliation(snapshot, ranking)
    raw_manifest["reconciliation"] = reconciliation_summary
    identity = {"schema": "YF-DAILY-QVP-OUTPUT-IDENTITY-1.0.0", "run_id": run_id,
                "scanner_invoked_at_utc": invoked_at.isoformat(),
                "retrieval_started_at_utc": raw_manifest["started_at_utc"],
                "retrieval_completed_at_utc": raw_manifest["completed_at_utc"],
                "score_session": str(score_session.date()), "source_snapshot": display_path(snapshot),
                "eligible_count": len(ranking), "scored_count": int(ranking.qvp_score.notna().sum()),
                "code_commit": raw_manifest["code_commit"], "configuration_sha256": raw_manifest["configuration_sha256"],
                "snapshot_manifest_sha256": sha256(snapshot / "manifest.json")}
    write_json(output / "output_manifest_identity.json", identity)
    identity_hash = sha256(output / "output_manifest_identity.json")
    raw_manifest["output_manifest_sha256"] = identity_hash
    metadata = {"run_id": run_id, "retrieval_started_at_utc": raw_manifest["started_at_utc"],
                "retrieval_completed_at_utc": raw_manifest["completed_at_utc"],
                "score_session": str(score_session.date()), "source_snapshot": display_path(snapshot),
                "eligible_count": len(ranking), "scored_count": int(ranking.qvp_score.notna().sum()),
                "code_commit": raw_manifest["code_commit"], "configuration_sha256": raw_manifest["configuration_sha256"],
                "output_manifest_sha256": identity_hash}
    report = markdown_report(run_id, raw_manifest, ranking, portfolio, exposures, changes, allocations,
                             warnings, holdings_report, constraint_exclusions)

    attach_metadata(ranking, metadata).to_csv(output / "ranking.csv", index=False)
    attach_metadata(portfolio, metadata).to_csv(output / "portfolio.csv", index=False)
    attach_metadata(universe, metadata).to_csv(output / "universe_report.csv", index=False)
    attach_metadata(constraint_exclusions, metadata).to_csv(output / "constraint_exclusions.csv", index=False)
    attach_metadata(holdings_report, metadata).to_csv(output / "holdings_analysis.csv", index=False)
    attach_metadata(allocations_all, metadata).to_csv(output / "contribution_allocations.csv", index=False)
    attach_metadata(exposures, metadata).to_csv(output / "exposures.csv", index=False)
    attach_metadata(reconciliation, metadata).to_csv(output / "reconciliation.csv", index=False)
    write_json(output / "reconciliation_summary.json", {"metadata": metadata,
                                                          "reconciliation": reconciliation_summary})
    write_json(output / "changes.json", {"metadata": metadata, "changes": changes})
    write_json(output / "data_quality_warnings.json", {"metadata": metadata, "warnings": warnings})
    (output / "report.md").write_text(report, encoding="utf-8")
    (output / "report.html").write_text(simple_html(report, portfolio, exposures), encoding="utf-8")
    files = [{"path": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(output.iterdir()) if p.is_file() and p.name != "manifest.json"]
    run_manifest = {"schema": "YF-DAILY-QVP-RUN-1.0.0", "run_id": run_id,
                    "created_at_utc": datetime.now(timezone.utc).isoformat(), "score_session": str(score_session.date()),
                    "snapshot": display_path(snapshot), "snapshot_manifest_sha256": sha256(snapshot / "manifest.json"),
                    "configuration": display_path(args.config), "configuration_sha256": sha256(args.config),
                    "previous_run": previous_id, "requested_contribution": float(args.contribution),
                    "holdings_file": str(args.holdings) if args.holdings else None,
                    "eligible_count": len(ranking), "scored_count": int(ranking.qvp_score.notna().sum()),
                    "code_commit": raw_manifest["code_commit"], "output_manifest_identity_sha256": identity_hash,
                    "classification": "current_decision_support_integrity_passed",
                    "files": files}
    write_json(output / "manifest.json", run_manifest)
    FINAL.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output / "report.md", FINAL / "current_daily_qvp_report.md")
    shutil.copy2(output / "report.html", FINAL / "current_daily_qvp_report.html")
    shutil.copy2(output / "portfolio.csv", FINAL / "current_daily_qvp_portfolio.csv")
    shutil.copy2(output / "ranking.csv", FINAL / "current_daily_qvp_ranking.csv")
    summary = {"run_id": run_id, "score_session": str(score_session.date()), "eligible": len(ranking),
               "qvp_scored": int(ranking.qvp_score.notna().sum()), "portfolio": portfolio.ticker.tolist(),
               "requested_contribution": float(args.contribution), "previous_run": previous_id,
               "output": str(output), "manifest_sha256": sha256(output / "manifest.json")}
    print(json.dumps(summary, sort_keys=True))
    return summary


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--holdings", type=Path)
    value.add_argument("--contribution", type=float, default=0.0)
    value.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    value.add_argument("--snapshot", type=Path)
    value.add_argument("--run-id")
    value.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    value.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    value.add_argument("--attempts", type=int, default=4)
    value.add_argument("--workers", type=int, default=2)
    value.add_argument("--delay-seconds", type=float, default=0.3)
    value.add_argument("--endpoint-delay-seconds", type=float, default=0.3)
    value.add_argument("--reuse-analysis", action="store_true")
    value.add_argument("--resume-retrieval", action="store_true",
                       help="Pass --resume to the raw pull so an existing snapshot can be completed")
    value.add_argument("--maximum-scoring-core-incomplete", type=int, default=0,
                       help="Tolerated count of eligible tickers with missing scoring-core files (default 0)")
    return value


def main() -> int:
    args = parser().parse_args()
    for attribute in ["config", "snapshot", "data_root", "output_root", "holdings"]:
        path = getattr(args, attribute)
        if path is not None and not path.is_absolute():
            setattr(args, attribute, ROOT / path)
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
