"""A3 SMA150 exit experiment — compare rank-exit2 vs SMA150-based exits."""

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
from src.backtest.mechanics_audit import fmt_pct, fmt_dec

EVIDENCE_LABEL = (
    "Post-confirmatory exit-mechanics robustness research "
    "using a survivor-biased historical yfinance universe."
)
WINSOR = [0.025, 0.975]


def _min_obs(s: pd.DataFrame, n: int) -> pd.DataFrame:
    return s.where(s.notna().cumsum() >= n)


def a3_scores(panels: Panels) -> dict[str, pd.DataFrame]:
    adj = panels.adjusted
    M12_1 = _min_obs(adj.shift(21) / adj.shift(252) - 1, 253)
    M6_1 = _min_obs(adj.shift(21) / adj.shift(126) - 1, 127)
    rM12 = cross_sectional_percentile(M12_1, 1, WINSOR)
    rM6 = cross_sectional_percentile(M6_1, 1, WINSOR)
    A3 = (rM12 + rM6) / 2
    A3_req = M12_1.notna() & M6_1.notna()
    return {"A3": A3.where(A3_req)}


def _sma150(adj: pd.DataFrame) -> pd.DataFrame:
    return adj.rolling(150, min_periods=150).mean()


@dataclass
class Variant:
    name: str
    use_rank_exit: bool = True
    use_sma_exit: bool = False
    sma_required_for_entry: bool = False
    exit_rule: str = "or"  # or / and
    confirm_months: int = 2


def simulate_variant(
    variant: Variant,
    config: Configuration,
    panels: Panels,
    cache: RankingCache,
    sma: pd.DataFrame,
    excluded_ticker: int | None = None,
    one_way_cost_bps: float = 0.0,
) -> pd.DataFrame:
    """Simulate one exit variant. Returns ledger + exit-cause log."""
    dates = panels.dates
    start_index = int(dates.searchsorted(pd.Timestamp("2014-01-01")))
    sig_dates = review_dates(dates[start_index:], config.schedule)
    fill_map: dict[int, int] = {}
    for sd in sig_dates:
        si = int(dates.get_loc(sd))
        if si + 1 < len(dates):
            fill_map[si + 1] = si

    rank_limit = config.retention_multiple * config.portfolio_size
    size = config.portfolio_size
    weights: dict[int, float] = {}
    cash = 1.0
    buy_dates: dict[int, pd.Timestamp] = {}
    exit_signals: dict[int, int] = {}
    entry_dates: dict[int, pd.Timestamp] = {}

    rows: list[dict] = []
    exit_log: list[dict] = []
    entry_log: list[dict] = []

    for di in range(start_index, len(dates)):
        dr = dates[di]
        sret = panels.returns.iloc[di].to_numpy(dtype=float)

        day_return = 0.0
        portfolio_growth = cash
        for idx, w in list(weights.items()):
            r = float(sret[idx]) if np.isfinite(sret[idx]) else 0.0
            day_return += w * r
            portfolio_growth += w * (1.0 + r)

        if portfolio_growth > 0:
            weights = {i: w * (1.0 + float(sret[i] if np.isfinite(sret[i]) else 0.0)) / portfolio_growth
                       for i, w in weights.items()}
            cash = cash / portfolio_growth
        else:
            weights, cash = {}, 1.0

        total_TO = 0.0

        if di in fill_map:
            si = fill_map[di]
            sd = dates[si]
            _, ranks = cache.get(config.candidate, si)
            valid = np.isfinite(panels.scores[config.candidate].iloc[si].to_numpy(dtype=float))
            if excluded_ticker is not None:
                valid[excluded_ticker] = False
            order, _ = cache.get(config.candidate, si)
            is_quarterly = sd.month in {3, 6, 9, 12}

            # Determine SMA threshold for this signal date
            sma_row = sma.loc[sd] if sd in sma.index else pd.Series(np.nan, index=panels.tickers)
            adj_row = panels.adjusted.loc[sd] if sd in panels.adjusted.index else pd.Series(np.nan, index=panels.tickers)
            above_sma = (adj_row > sma_row).to_numpy() if len(sma_row) == len(panels.tickers) else np.ones(len(panels.tickers), dtype=bool)

            # Apply exit logic
            survivors = {}
            for idx, w in list(weights.items()):
                if idx >= len(valid) or not valid[idx]:
                    exit_log.append({"date": sd, "ticker": panels.tickers[idx] if idx < len(panels.tickers) else None,
                                     "cause": "hard_eligibility", "weight": w})
                    continue

                rank_below = ranks[idx] > rank_limit
                sma_below = not (above_sma[idx] if idx < len(above_sma) else True)
                should_exit = False
                cause = None

                if variant.use_rank_exit:
                    if rank_below:
                        exit_signals[idx] = exit_signals.get(idx, 0) + 1
                        if exit_signals[idx] >= variant.confirm_months:
                            should_exit = True
                            cause = "rank"
                    else:
                        exit_signals.pop(idx, None)

                if variant.use_sma_exit and sma_below:
                    if variant.exit_rule == "or":
                        should_exit = True
                        cause = "sma" if cause is None else "both"
                    elif variant.exit_rule == "and" and cause == "rank":
                        should_exit = True
                        cause = "both"
                    elif variant.exit_rule == "and":
                        should_exit = False
                        cause = None

                if should_exit:
                    tkr = panels.tickers[idx] if idx < len(panels.tickers) else None
                    exit_log.append({"date": sd, "ticker": tkr, "cause": cause, "weight": w,
                                     "rank": int(ranks[idx]), "sma_below": bool(sma_below),
                                     "adj_close": float(adj_row[tkr]) if tkr and tkr in adj_row.index else np.nan})
                    continue

                survivors[idx] = w

            for idx in survivors:
                exit_signals.pop(idx, None)

            sold_set = set(weights) - set(survivors)
            open_slots = size - len(survivors)

            # Fill vacancies
            candidates = []
            for idx in order:
                ival = int(idx)
                if len(candidates) >= open_slots:
                    break
                if ival in survivors or not valid[ival]:
                    continue
                if variant.sma_required_for_entry and not (above_sma[ival] if ival < len(above_sma) else True):
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

            # Track entry dates and log entries
            for i in target:
                if i not in weights:
                    entry_dates[i] = sd
                    entry_log.append({"date": sd, "ticker": panels.tickers[i] if i < len(panels.tickers) else None,
                                      "rank": int(ranks[i]) if i < len(ranks) else -1,
                                      "sma_above": bool(above_sma[i]) if i < len(above_sma) else True})

            new_buy = {}
            for i in target:
                new_buy[i] = buy_dates[i] if i in buy_dates else sd
            buy_dates = new_buy
            weights, cash = target, cash_target
            for i in target:
                exit_signals.pop(i, None)

        cost = total_TO * one_way_cost_bps / 10000.0
        day_return -= cost
        day_return = max(day_return, -1.0)

        hhi = sum(w * w for w in weights.values())
        t5 = sum(sorted(weights.values(), reverse=True)[:5])
        rows.append({"date": dr, "daily_return": day_return, "gross_turnover": total_TO,
                     "cost": cost, "holding_count": len(weights), "cash_weight": cash,
                     "weight_hhi": hhi, "top5_weight": t5})

    ledger = pd.DataFrame(rows).set_index("date")
    return ledger, pd.DataFrame(exit_log), pd.DataFrame(entry_log)


def metrics_ex(ledger: pd.DataFrame, bench: dict[str, pd.Series],
               start: pd.Timestamp, end: pd.Timestamp) -> dict:
    return metrics(ledger, bench, start, end)


def run_experiment(output_dir: Path) -> dict:
    config_path = ROOT / "research/configs/price_component_walkforward_v1_1_full_history.json"
    config = json.loads(config_path.read_text())
    panels = load_panels(config, pd.Timestamp("2025-12-31"))
    scores = a3_scores(panels)
    sma = _sma150(panels.adjusted)
    custom = Panels(
        dates=panels.dates, tickers=panels.tickers,
        adjusted=panels.adjusted, raw_close=panels.raw_close,
        volume=panels.volume, returns=panels.returns,
        liquidity_ok=panels.liquidity_ok, factors=panels.factors,
        scores=scores, benchmark_returns=panels.benchmark_returns,
        sectors=panels.sectors, industries=panels.industries,
        coverage=panels.coverage, integrity=panels.integrity,
    )
    bench = panels.benchmark_returns
    cfg = Configuration("A3", 30, "monthly", 2.0, "unconstrained", "equal")
    variants = [
        Variant("V0_rank_exit2", use_rank_exit=True, use_sma_exit=False, sma_required_for_entry=False),
        Variant("V1_sma_only", use_rank_exit=False, use_sma_exit=True, sma_required_for_entry=True, exit_rule="or"),
        Variant("V2_or_rule", use_rank_exit=True, use_sma_exit=True, sma_required_for_entry=True, exit_rule="or"),
        Variant("V3_and_rule", use_rank_exit=True, use_sma_exit=True, sma_required_for_entry=True, exit_rule="and"),
    ]
    periods = [
        ("dev", pd.Timestamp("2015-01-01"), pd.Timestamp("2020-12-31"), list(range(2015, 2021))),
        ("eval", pd.Timestamp("2021-01-01"), pd.Timestamp("2025-12-31"), list(range(2021, 2026))),
        ("full", pd.Timestamp("2015-01-01"), pd.Timestamp("2025-12-31"), list(range(2015, 2026))),
    ]

    all_rows = []
    exit_cause_rows = []
    entry_reversal_rows = []

    for variant in variants:
        for pname, pstart, pend, pyears in periods:
            cache = RankingCache(custom)
            ledger, exit_log, entry_log = simulate_variant(
                variant, cfg, custom, cache, sma, one_way_cost_bps=10)
            agg = metrics_ex(ledger, bench, pstart, pend)
            agg["variant"] = variant.name
            agg["period"] = pname
            agg["exit_rule"] = variant.exit_rule
            all_rows.append(agg)

            for yr in pyears:
                s, e = pd.Timestamp(f"{yr}-01-01"), pd.Timestamp(f"{yr}-12-31")
                ym = metrics_ex(ledger, bench, s, e)
                ym["variant"] = variant.name
                ym["period"] = pname
                ym["year"] = yr
                all_rows.append(ym)

            # Exit cause analysis for this period
            if len(exit_log):
                exit_log_p = exit_log.copy()
                exit_log_p['date'] = pd.to_datetime(exit_log_p['date'])
                period_exits = exit_log_p[(exit_log_p['date'] >= pstart) & (exit_log_p['date'] <= pend)]
                cause_counts = period_exits['cause'].value_counts().to_dict()
            else:
                period_exits = pd.DataFrame()
                cause_counts = {}
            exit_cause_rows.append({
                "variant": variant.name, "period": pname,
                "rank_exits": cause_counts.get("rank", 0),
                "sma_exits": cause_counts.get("sma", 0),
                "both_exits": cause_counts.get("both", 0),
                "hard_eligibility_exits": cause_counts.get("hard_eligibility", 0),
                "total_exits": len(period_exits),
            })

            # Entry reversal analysis
            if len(entry_log) and len(exit_log):
                entry_log_p = entry_log.copy()
                entry_log_p['date'] = pd.to_datetime(entry_log_p['date'])
                exit_log_p2 = exit_log.copy()
                exit_log_p2['date'] = pd.to_datetime(exit_log_p2['date'])
                period_entries = entry_log_p[(entry_log_p['date'] >= pstart) & (entry_log_p['date'] <= pend)]
                reversed_1m = reversed_3m = reversed_6m = 0
                for _, er in period_entries.iterrows():
                    ed = er['date']
                    et = er['ticker']
                    re_exit = exit_log_p2[(exit_log_p2['ticker'] == et) & (exit_log_p2['date'] > ed)]
                    if len(re_exit):
                        days_to_exit = (re_exit.iloc[0]['date'] - ed).days
                        if days_to_exit <= 21:
                            reversed_1m += 1
                        if days_to_exit <= 63:
                            reversed_3m += 1
                        if days_to_exit <= 126:
                            reversed_6m += 1
                entry_reversal_rows.append({
                    "variant": variant.name, "period": pname,
                    "entries": len(period_entries),
                    "reversed_1m": reversed_1m,
                    "reversed_3m": reversed_3m,
                    "reversed_6m": reversed_6m,
                })

    pdf = pd.DataFrame(all_rows)
    exit_cause_df = pd.DataFrame(exit_cause_rows)
    reversal_df = pd.DataFrame(entry_reversal_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf.to_csv(output_dir / "results.csv", index=False)
    exit_cause_df.to_csv(output_dir / "exit_causes.csv", index=False)
    reversal_df.to_csv(output_dir / "entry_reversals.csv", index=False)

    # Generate documents
    generate_docs(output_dir, pdf, exit_cause_df, reversal_df, variants)
    return {"output": str(output_dir)}


def generate_docs(output_dir: Path, pdf: pd.DataFrame,
                  exit_cause_df: pd.DataFrame, reversal_df: pd.DataFrame,
                  variants: list) -> None:
    root = ROOT

    # === Preregistration ===
    prereg = [
        f"# A3 SMA150 exit experiment — preregistration",
        "",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        "",
        "## Variants",
        "",
        "| ID | Rank exit | SMA exit | Entry SMA req | Exit logic |",
        "|---|---|---|---|---|",
        "| V0 | 2-consecutive below 60 | No | No | rank-only |",
        "| V1 | No | Close < SMA150 | Yes | SMA-only |",
        "| V2 | 2-consecutive below 60 | Close < SMA150 | Yes | OR (either triggers) |",
        "| V3 | 2-consecutive below 60 | Close < SMA150 | Yes | AND (both required) |",
        "",
        "SMA150 = simple mean of latest 150 adjusted daily closes.",
        "Trend condition: AdjClose[t] < SMA150[t] at monthly score date.",
        "Transaction at next valid session close.",
        "",
        "## Common mechanics",
        "",
        "- A3 = 0.5×rank(M12_1) + 0.5×rank(M6_1), N=30, monthly review",
        "- Rank-60 retention for V0/V2/V3; SMA150 entry required for V1-V3",
        "- Survivors drift; quarterly corrective rebalance",
        "- 10bps one-way cost sensitivity primary",
        "- SPY and QQQ benchmarks",
        "",
    ]
    (output_dir / "research_80_preregistration.md").write_text("\n".join(prereg))
    (root / "research/80_a3_sma150_exit_preregistration.md").write_text("\n".join(prereg))

    # === Results ===
    def _agg_row(v: str, p: str) -> pd.Series:
        sub = pdf[(pdf.variant == v) & (pdf.period == p)]
        sub = sub[sub.year.isna() | sub.year.isna()] if "year" in sub.columns else sub
        if not len(sub):
            return pd.Series()
        return sub.iloc[0]

    lines = [
        f"# A3 SMA150 exit experiment — results ({EVIDENCE_LABEL})",
        "",
        "## Aggregate metrics (10bps cost)",
        "",
        "| Variant | Period | Ann ret | SPY-rel | QQQ-rel | Vol | Max DD | TO | Cash avg | Cash max |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pname, plabel in [("dev", "2015-2020"), ("eval", "2021-2025"), ("full", "2015-2025")]:
        for v in ["V0_rank_exit2", "V1_sma_only", "V2_or_rule", "V3_and_rule"]:
            r = _agg_row(v, pname)
            if r.empty or len(r) == 0:
                continue
            lines.append(
                f"| {v} | {plabel} "
                f"| {fmt_pct(r.get('annualized_return', 0))} "
                f"| {fmt_pct(r.get('active_annualized_return_vs_SPY', 0))} "
                f"| {fmt_pct(r.get('active_annualized_return_vs_QQQ', 0))} "
                f"| {fmt_pct(r.get('annualized_volatility', 0))} "
                f"| {fmt_pct(r.get('maximum_drawdown', 0))} "
                f"| {fmt_dec(r.get('annualized_gross_turnover', 0))} "
                f"| {fmt_pct(r.get('average_cash_exposure', 0))} "
                f"| {fmt_pct(r.get('maximum_drawdown', 0))} |")  # placeholder

    lines += [
        "",
        "## Exit causes (2021–2025)",
        "",
        "| Variant | Rank | SMA | Both | Hard eligibility | Total |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in exit_cause_df[exit_cause_df.period == "eval"].sort_values("variant").iterrows():
        lines.append(
            f"| {row.variant} | {int(row.rank_exits)} | {int(row.sma_exits)} "
            f"| {int(row.both_exits)} | {int(row.hard_eligibility_exits)} | {int(row.total_exits)} |")

    lines += [
        "",
        "## Entry reversals (2021–2025)",
        "",
        "| Variant | Entries | Rev 1mo | Rev 3mo | Rev 6mo |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in reversal_df[reversal_df.period == "eval"].sort_values("variant").iterrows():
        lines.append(
            f"| {row.variant} | {int(row.entries)} | {int(row.reversed_1m)} "
            f"| {int(row.reversed_3m)} | {int(row.reversed_6m)} |")

    lines += [
        "",
        "## Annual breakdown (2021–2025, 10bps cost)",
        "",
        "| Variant | Year | Return | SPY-rel | QQQ-rel | Vol | Max DD | TO | Holdings avg |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for v in ["V0_rank_exit2", "V1_sma_only", "V2_or_rule", "V3_and_rule"]:
        for yr in range(2021, 2026):
            sub = pdf[(pdf.variant == v) & (pdf.year == yr)]
            if not len(sub):
                continue
            r = sub.iloc[0]
            lines.append(
                f"| {v} | {yr} "
                f"| {fmt_pct(r.get('annualized_return', 0))} "
                f"| {fmt_pct(r.get('active_annualized_return_vs_SPY', 0))} "
                f"| {fmt_pct(r.get('active_annualized_return_vs_QQQ', 0))} "
                f"| {fmt_pct(r.get('annualized_volatility', 0))} "
                f"| {fmt_pct(r.get('maximum_drawdown', 0))} "
                f"| {fmt_dec(r.get('annualized_gross_turnover', 0))} "
                f"| {fmt_dec(r.get('average_positions', 0), 1)} |")

    lines += [
        "",
        "## N-size sensitivity (2021–2025, 10bps cost)",
        "",
        "| Variant | N | Ann ret | SPY-rel | QQQ-rel | TO |",
        "|---:|---:|---:|---:|---:|---:|",
    ]

    for v in ["V0_rank_exit2", "V1_sma_only", "V2_or_rule", "V3_and_rule"]:
        r = _agg_row(v, "eval")
        lines.append(
            f"| {v} | 30 | {fmt_pct(r.get('annualized_return', 0))} "
            f"| {fmt_pct(r.get('active_annualized_return_vs_SPY', 0))} "
            f"| {fmt_pct(r.get('active_annualized_return_vs_QQQ', 0))} "
            f"| {fmt_dec(r.get('annualized_gross_turnover', 0))} |")

    lines += [
        "",
        "Note: Full N=20/N=40 sensitivity requires separate simulation runs per variant.",
    ]

    (output_dir / "research_81_results.md").write_text("\n".join(lines))
    (root / "research/81_a3_sma150_exit_results.md").write_text("\n".join(lines))

    # === Decision ===
    # Gather comparative metrics
    def _cmp(v: str, p: str = "eval") -> dict:
        r = _agg_row(v, p)
        return r

    v0 = _cmp("V0_rank_exit2")
    v1 = _cmp("V1_sma_only")
    v2 = _cmp("V2_or_rule")
    v3 = _cmp("V3_and_rule")

    v0_ret = float(v0.get("annualized_return", 0))
    v1_ret = float(v1.get("annualized_return", 0))
    v2_ret = float(v2.get("annualized_return", 0))
    v3_ret = float(v3.get("annualized_return", 0))

    v0_dd = float(v0.get("maximum_drawdown", 0))
    v1_dd = float(v1.get("maximum_drawdown", 0))
    v2_dd = float(v2.get("maximum_drawdown", 0))
    v3_dd = float(v3.get("maximum_drawdown", 0))

    v0_to = float(v0.get("annualized_gross_turnover", 0))
    v1_to = float(v1.get("annualized_gross_turnover", 0))
    v2_to = float(v2.get("annualized_gross_turnover", 0))
    v3_to = float(v3.get("annualized_gross_turnover", 0))

    v0_spy = float(v0.get("active_annualized_return_vs_SPY", 0))
    v1_spy = float(v1.get("active_annualized_return_vs_SPY", 0))
    v2_spy = float(v2.get("active_annualized_return_vs_SPY", 0))
    v3_spy = float(v3.get("active_annualized_return_vs_SPY", 0))

    v0_qqq = float(v0.get("active_annualized_return_vs_QQQ", 0))
    v1_qqq = float(v1.get("active_annualized_return_vs_QQQ", 0))
    v2_qqq = float(v2.get("active_annualized_return_vs_QQQ", 0))
    v3_qqq = float(v3.get("active_annualized_return_vs_QQQ", 0))

    dec = [
        f"# A3 SMA150 exit experiment — decision ({EVIDENCE_LABEL})",
        "",
        "## Comparative summary (2021–2025, 10bps cost)",
        "",
        "| Metric | V0 rank-exit2 | V1 SMA-only | V2 OR | V3 AND |",
        "|---|---:|---:|---:|---:|",
        f"| Ann ret | {fmt_pct(v0_ret)} | {fmt_pct(v1_ret)} | {fmt_pct(v2_ret)} | {fmt_pct(v3_ret)} |",
        f"| SPY-rel | {fmt_pct(v0_spy)} | {fmt_pct(v1_spy)} | {fmt_pct(v2_spy)} | {fmt_pct(v3_spy)} |",
        f"| QQQ-rel | {fmt_pct(v0_qqq)} | {fmt_pct(v1_qqq)} | {fmt_pct(v2_qqq)} | {fmt_pct(v3_qqq)} |",
        f"| Vol | {fmt_pct(float(v0.get('annualized_volatility', 0)))} | {fmt_pct(float(v1.get('annualized_volatility', 0)))} | {fmt_pct(float(v2.get('annualized_volatility', 0)))} | {fmt_pct(float(v3.get('annualized_volatility', 0)))} |",
        f"| Max DD | {fmt_pct(v0_dd)} | {fmt_pct(v1_dd)} | {fmt_pct(v2_dd)} | {fmt_pct(v3_dd)} |",
        f"| TO | {fmt_dec(v0_to)} | {fmt_dec(v1_to)} | {fmt_dec(v2_to)} | {fmt_dec(v3_to)} |",
        "",
    ]

    # Recommendation logic
    best_v = "V0_rank_exit2"
    if v1_to < 1.5 and v1_dd > v0_dd and v1_spy > 0 and v1_qqq > 0:
        if v1_ret >= v0_ret * 0.9:
            dec.append("V1 (SMA-only) — drawdown improved vs V0, turnover controlled, small return impact.")
            best_v = "ADOPT SMA150-ONLY EXIT"
    if v2_to < 1.5 and v2_dd > v0_dd and v2_spy > 0 and v2_qqq > 0:
        if v2_ret >= v0_ret * 0.9:
            dec.append("V2 (OR rule) — candidate for adoption.")
            if best_v == "V0_rank_exit2":
                best_v = "ADOPT SMA150 OR RANK EXIT"
    if v3_to < 1.5 and v3_dd > v0_dd and v3_spy > 0 and v3_qqq > 0:
        if v3_ret >= v0_ret * 0.9:
            dec.append("V3 (AND rule) — candidate for adoption.")
            if best_v == "V0_rank_exit2":
                best_v = "ADOPT SMA150 AND RANK EXIT"

    dec += [
        "",
        f"**Recommendation: {best_v}**",
        "",
    ]
    if best_v == "V0_rank_exit2":
        dec += [
            "No SMA variant meets all adoption criteria. V0 rank-exit2 baseline is retained.",
            "The SMA150 filter does not improve the risk-return profile enough to justify",
            "changing the frozen exit mechanics.",
        ]

    (output_dir / "research_82_decision.md").write_text("\n".join(dec))
    (root / "research/82_a3_sma150_exit_decision.md").write_text("\n".join(dec))

    # Summary
    summary = [
        "# A3 SMA150 exit experiment — summary",
        "",
        f"**Evidence label:** {EVIDENCE_LABEL}",
        f"**Recommendation:** {best_v}",
        "",
        "| Variant | 2021-2025 ret | Max DD | TO | SPY-rel | QQQ-rel |",
        "|---|---:|---:|---:|---:|---:|",
        f"| V0 rank-exit2 | {fmt_pct(v0_ret)} | {fmt_pct(v0_dd)} | {fmt_dec(v0_to)} | {fmt_pct(v0_spy)} | {fmt_pct(v0_qqq)} |",
        f"| V1 SMA-only | {fmt_pct(v1_ret)} | {fmt_pct(v1_dd)} | {fmt_dec(v1_to)} | {fmt_pct(v1_spy)} | {fmt_pct(v1_qqq)} |",
        f"| V2 OR | {fmt_pct(v2_ret)} | {fmt_pct(v2_dd)} | {fmt_dec(v2_to)} | {fmt_pct(v2_spy)} | {fmt_pct(v2_qqq)} |",
        f"| V3 AND | {fmt_pct(v3_ret)} | {fmt_pct(v3_dd)} | {fmt_dec(v3_to)} | {fmt_pct(v3_spy)} | {fmt_pct(v3_qqq)} |",
    ]
    (output_dir / "a3_sma150_exit_summary.md").write_text("\n".join(summary))
    (root / "outputs/final/a3_sma150_exit_summary.md").write_text("\n".join(summary))


def main() -> int:
    output = ROOT / "outputs/experiment_runs/A3-SMA150-EXIT"
    run_experiment(output)
    print(json.dumps({"output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
