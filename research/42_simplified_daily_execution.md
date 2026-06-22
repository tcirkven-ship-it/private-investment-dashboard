# Simplified daily paper execution

1. Complete and archive the final regular-session month-end snapshot.
2. Calculate ranks after completion.
3. Create decisions with a dated manifest.
4. Fill each paper trade at the first positive raw official Close on a trading date strictly after the decision date.
5. If missing, keep deferring until a valid raw Close exists.
6. Never use same-day Close after consuming that day's completed data; never execute or value with Adjusted Close.

This daily convention is fixed without day/time optimization. It is a research standard, not an expected real fill.

Intraday windows, limit offsets, bar crossing, partial fills, expiration, retries, volume participation and intraday archives are superseded and absent from the active code.

> The paper results exclude commissions, spreads, slippage, taxes, currency conversion, and broker-specific charges.

