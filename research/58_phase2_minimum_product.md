# Phase Two minimum product

## Implemented minimum

The first local minimum product is the one-command scanner in `src/daily_screen.py`, configured by `research/configs/daily_qvp_v1.json`.

It retrieves fresh data, enforces a completed-session cutoff, calculates frozen scores, selects a constrained top 30, compares with the prior run, accepts optional holdings and contribution amounts, and emits immutable CSV/Markdown/HTML reports with checksums. It has no broker connection and no order API.

## Exact next development step

Validate the command on several consecutive completed sessions and add a small local “Run scanner” launcher that collects the holdings path and contribution amount, then invokes the same tested command. Do not create a separate scoring implementation or large web application. The CLI remains the source of truth.

Only after consecutive-run change reports and holdings imports are verified should a lightweight local dashboard read the immutable outputs. Brokerage integration remains out of scope.
