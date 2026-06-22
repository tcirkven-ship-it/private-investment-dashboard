# Final recommendation

## Decision: FAIL

No tested strategy is approved. The result is not a conditional pass because structural survivorship, delisting and point-in-time fundamental defects violate critical gates that cannot be waived.

| Critical gate | Result |
|---|---|
| Data integrity | **FAIL** — current universe, missing inactive/delisted outcomes, no historical PIT fundamentals |
| Benchmark/accounting | PASS — deterministic tests and contribution equality passed |
| Full-sample TWR/XIRR hurdle | Point estimate passed, but biased |
| Final-holdout performance vs SPY | PASS |
| Final-holdout performance vs QQQ | **FAIL** |
| Stressed-cost holdout vs QQQ | **FAIL** |
| Uncertainty vs QQQ | **FAIL** — 95% interval includes zero |
| Rolling/period consistency | **FAIL** |
| Drawdown and volatility | PASS |
| Turnover | **FAIL** — approximately 172–184% |
| Parameter stability | **FAIL** — 20% stable-positive fraction |
| Investability/operational burden | **FAIL** |
| Adversarial review | **FAIL** — unresolved critical findings |

## Recommended policy from this research

1. Do not deploy C03-M or any observed high-return size variant as a validated live strategy.
2. Use contribution-matched passive ETFs as the decision baseline. A diversified passive policy requires a separate investor suitability choice; this report does not prescribe the SPY/QQQ allocation.
3. If direct-stock research remains desirable, paper-track C03-M unchanged and begin a genuinely forward, as-filed fundamental dataset. Do not reuse the completed holdout for certification.
4. Reconsider active deployment only after new evidence passes turnover, QQQ, data-integrity, uncertainty and operational gates.

## What would change the conclusion

- An effective-dated universe with inactive securities and delisting outcomes.
- Point-in-time as-filed fundamentals mapped to permanent security identifiers.
- A new unused chronological holdout.
- Turnover below 100% without holdout-led redesign.
- Positive, statistically credible performance against both SPY and QQQ under stressed costs.
- A practical fractional-share execution convention and resolved tax/FX context.

Historical performance does not guarantee future returns. This is research, not personalized investment, tax or legal advice.

