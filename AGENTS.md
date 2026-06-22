# Project operating rules

## Purpose

This repository contains a research-first investigation of a recurring-contribution, long-only US stock-selection strategy for an individual investor using Interactive Brokers. Phase One is research and validation, not production application development.

## Required startup procedure

Before doing any work:

1. Read this file and `handoff.md`.
2. Read the current research protocol and decision log.
3. Inspect existing files before creating or modifying artifacts.
4. Review available Codex skills and use the relevant ones.
5. Use an explicit plan for substantial tasks.

## Primary rules

- Preserve raw data. Never modify files in `data/raw/`.
- Use point-in-time information whenever possible.
- Prevent survivorship bias, look-ahead bias, and benchmark mismatch.
- Use filing or conservative availability dates for fundamental information.
- Include dividends, delistings, corporate actions, commissions, spreads, and slippage.
- Apply identical contribution schedules to strategies and benchmarks.
- Keep final holdout data untouched until rules and success criteria are frozen.
- Record every material experiment, including failures.
- Prefer simple, explainable rules and stable parameter regions.
- Cite substantive research claims.
- Separate facts, assumptions, interpretations, and recommendations.
- Never guarantee future returns.
- Never place live orders or request brokerage credentials.
- Do not build a production application without explicit approval.

## Research code

Research code and notebooks are permitted when needed for reproducibility. They must be deterministic where practical, use clear configuration, preserve data lineage, include tests for critical calculations, save machine-readable results, and avoid unnecessary production architecture.

## Required documentation

Maintain:

- `handoff.md`;
- `research/decision_log.md`;
- `research/experiment_registry.csv`;
- `research/references.md`;
- `research/contradictions.md`.

Update `handoff.md` after every major checkpoint, when an assumption changes, when a blocker is discovered, before ending a session, and before delegating work.

## Subagents

When the user has authorized delegation, use independent workstreams for literature, data integrity, strategy design, statistics, portfolio construction, execution practicality, and adversarial review. Each return must identify sources, methods, findings, uncertainties, contradictions, and recommended next actions. The coordinating agent must reconcile disagreements rather than concatenate outputs.

## Phase One definition of done

Phase One is complete only when data limitations are documented; benchmark calculations are validated; candidate strategies have genuine out-of-sample and walk-forward results; costs are included; robustness and parameter stability are reported; an adversarial review is complete; the strategy receives a pass, conditional pass, or fail determination; and a manual weekly playbook exists. Phase Two remains unimplemented unless separately authorized.
