# Project operating rules

## Purpose

This repository contains a research-first investigation and a minimal local decision-support implementation for a recurring-contribution, long-only US stock-selection strategy. It does not place orders or connect to a broker.

## Current direction

- Current YF-QVP scores and constrained model portfolios are available on demand after the latest fully completed daily market session.
- Score timing, user review timing, and user transaction timing are independent clocks.
- Month-end is a historical/rebalance research schedule, not a gate on current rankings.
- The local scanner may retrieve current yfinance data, preserve immutable snapshots, accept optional holdings and contribution inputs, and create Markdown/CSV/HTML reports.
- Scanner output is decision-support research, not prospective performance evidence, a live-trading instruction, or a claim of validated outperformance.
- The formal paper-performance ledger records only explicitly chosen paper decisions; generating a score never creates a transaction.
- Preserve the superseded month-end-only activation and all earlier failures as audit history.

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
- Never convert a scanner signal into a paper or live transaction without an explicit separately recorded user decision.
- Do not build or materially expand a production application without explicit approval. The private dashboard under web/ has received explicit approval; all other production expansion still requires approval.

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

## Private dashboard authorization and engineering rules

The owner has explicitly authorized development of the private investment dashboard under `web/`.

The dashboard is:

* private and single-owner;
* browser-based and responsive;
* built with Next.js, TypeScript, Supabase Auth, PostgreSQL and Row Level Security;
* manual-entry only;
* not connected to a broker;
* not permitted to place orders automatically;
* not a public service;
* not a substitute for the research evidence process.

The research scanner, the official quarterly model, the personal portfolio ledger and any daily research model must remain clearly separated.

### Mandatory engineering reliability rules

Before substantial work under `web/`, read and follow:

`docs/engineering-reliability.md`

Its rules are mandatory, especially those concerning:

* evidence-first completion;
* no silent scope reduction;
* stop-on-failure behavior;
* database migration safety;
* Supabase and RLS testing;
* append-only financial-ledger integrity;
* real database integration;
* test-script honesty;
* requirement traceability;
* contradiction detection;
* Impeccable UI verification;
* commit and handoff integrity.

### No false completion claims

Do not describe work as verified, complete, production-ready or safe to deploy unless the relevant checks were actually executed successfully.

Clearly distinguish:

* implemented;
* statically inspected;
* compiled;
* unit-tested;
* integration-tested;
* end-to-end tested;
* manually verified;
* not tested;
* blocked.

Creating a test script is not equivalent to running the test.

A successful build is not proof of runtime, database, RLS, accounting or UI correctness.

### No permanent mock or empty production data

Production routes must not use:

* mock financial records;
* hard-coded balances or returns;
* permanent `useState([])` data;
* permanent `loading = false`;
* disabled controls as substitutes for required functionality;
* text claiming database connectivity without a real successful query.

A truthful empty state must result from a real database query that completed successfully and returned no records.

### Database release gate

Database work is not deployable until all of the following execute successfully against a disposable Supabase-compatible environment:

1. clean migration;
2. exact schema verification;
3. deliberate-failure rollback verification;
4. reset and reapply;
5. Auth profile creation;
6. anonymous denial;
7. owner access;
8. second-user denial;
9. append-only transaction enforcement;
10. published-model immutability;
11. database-backed financial integration tests.

Missing infrastructure is a blocker, not a passing result.

### Financial integrity

Transactions are the source of truth for portfolio activity.

Holdings, cash, cost basis, realised gains and valuations must be reproducible from the ledger and related price observations.

Financial history must not be silently updated, deleted or destroyed through cascade deletion.

Corrections must use explicit linked correction or reversal events.

Every transaction event type must have documented and tested:

* required fields;
* prohibited fields;
* sign convention;
* cash effect;
* quantity effect;
* cost-basis effect;
* realised-gain effect.

### Impeccable requirement

When an implementation task requires Impeccable:

* configure and actually use the applicable workflow;
* preserve audit evidence;
* identify issues found;
* implement the fixes;
* provide desktop and mobile evidence;
* report accessibility and responsive-layout checks.

If no evidence exists, state plainly:

`IMPECCABLE WAS NOT USED`

Do not infer Impeccable usage from general visual polish.

### Final task status

Every substantial application task must end with exactly one status:

* `COMPLETE — EXECUTED AND VERIFIED`
* `PARTIAL — IMPLEMENTED BUT NOT FULLY VERIFIED`
* `BLOCKED`
* `FAILED`

The report must separately list:

* requirements and status;
* files changed;
* commands executed;
* exit codes;
* tests not executed;
* known limitations;
* deployment status;
* final commit hash;
* working-tree status.

Deployment status must be exactly one of:

* `SAFE TO DEPLOY`
* `NOT SAFE TO DEPLOY`
* `DEPLOYMENT NOT ASSESSED`

