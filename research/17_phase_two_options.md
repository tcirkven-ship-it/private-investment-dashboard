# Phase Two options — not authorized or implemented

Phase One ends with a fail decision for the active strategy. The following are optional development paths only if the user explicitly authorizes Phase Two.

## Option A — forward research ledger

Recommended if the zero-cost constraint remains:

- local yfinance price/action snapshots;
- current Nasdaq/iShares universe snapshots;
- SEC as-filed facts using an owner-provided compliant `SEC_USER_AGENT` contact;
- frozen monthly score files;
- paper holdings, contributions, costs and exception logs;
- no broker connection or orders.

This can create unbiased evidence prospectively, but several years are needed.

## Option B — spreadsheet workflow

A manually reviewed workbook containing data freshness checks, ranks, holdings, target weights, contribution routing, proposed paper orders and an audit log. It should remain paper-only until a strategy passes a new research generation.

## Option C — local command-line scanner

A reproducible local command that updates approved data, validates it, emits ranks and creates a paper-order worksheet. No credentials or order transmission.

## Option D — scheduled research report

A weekly local report generator that archives manifests, coverage, scores, constraint breaches and paper performance.

## Option E — data-quality upgrade

If the no-cost constraint changes, acquire effective-dated security identifiers, inactive listings, delisting returns and point-in-time fundamental vintages, then create a new preregistration and unused holdout.

Dashboard, IBKR-assisted order generation and broker integration should remain deferred until a strategy actually passes Phase One under an adequate dataset.

