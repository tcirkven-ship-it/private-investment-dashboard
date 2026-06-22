# Score, review and transaction clocks

| Clock | Controller | Frequency | Effect |
|---|---|---|---|
| Score | Scanner/user request | On demand after latest completed daily session | Refreshes universe, current inputs, factors, ranks and immutable reports |
| Review | User | Daily, weekly, biweekly, monthly or irregular | Interprets current model output and holdings; does not change formulas |
| Transaction | User | Any user-chosen time or never | A separately chosen action; scanner never places an order |

Generating a score does not rebalance a portfolio. Reviewing a score does not imply trading. Contribution input changes only the cash-allocation illustration, never the ranking.

The formal paper-performance ledger is a fourth recordkeeping concept, not a clock imposed on the scanner. It records only decisions explicitly designated for paper observation. Daily decision-support runs remain outside performance evidence unless separately promoted before outcomes are known.
