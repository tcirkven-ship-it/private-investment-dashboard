# Risks and failure modes

## Critical evidence risks

- **Survivorship and membership bias:** the historical universe is the current OEF portfolio.
- **Delisting omission:** inactive names and terminal returns are absent.
- **Fundamental look-ahead:** free historical statement vintages were insufficient; latest statements cannot be projected backward.
- **Identifier risk:** Yahoo tickers are not permanent effective-dated security identifiers.
- **Upstream revision:** yfinance/Yahoo history can change; immutable local snapshots reduce but do not remove that risk.

## Strategy risks

- Momentum crashes and reversals.
- Concentration in technology and current mega-cap winners.
- QQQ-like exposure without reliably beating QQQ.
- High turnover, many small orders and tax inefficiency.
- Parameter instability: shorter lookbacks and portfolio sizes behaved differently across stages.
- Large relative underperformance in individual years, including 2023.
- Crowding and factor decay.

## Implementation risks

- Fractional shares may become ineligible and do not support MOC in the reviewed IBKR workflow.
- Limit orders may not fill; marketable orders may incur more slippage than modeled.
- USD 0.35 minimum commissions are material for small multi-order contributions.
- Historical bid/ask spreads and market impact were not available.
- Corporate actions can be delayed or revised upstream.
- Exact account permissions, pricing plan and residence eligibility can differ.

## Investor-context risks

- Tax jurisdiction and account type are unresolved.
- Contributions may originate in EUR, introducing conversion timing and FX costs.
- Maximum tolerable drawdown is unresolved; the prototype experienced about -32%.
- The active workflow may be too burdensome to follow consistently.

## Governance risks

- Choosing N=10 or N=20 after seeing their high return would be post-selection overfitting.
- Reusing the 2023–2026 holdout would invalidate it as an independent test.
- A favorable forward period cannot repair the original survivor-biased history; it creates new forward evidence only.
- Production automation could make an unapproved strategy easier to trade without making it more valid.

