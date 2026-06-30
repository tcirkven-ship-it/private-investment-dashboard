/**
 * Holdings derivation engine.
 * Transactions are the source of truth. Holdings and cash are derived.
 * Average-cost method. No silent mutation of historical transactions.
 */

export type TransactionEventType =
  | "DEPOSIT" | "WITHDRAWAL" | "BUY" | "SELL" | "DIVIDEND"
  | "FEE" | "TAX" | "INTEREST" | "SPLIT" | "SYMBOL_CHANGE"
  | "MERGER" | "SPINOFF" | "CORRECTION" | "TRANSFER"
  | "OPENING_POSITION";

export interface Transaction {
  id?: string;
  portfolio_id?: string;
  security_id?: string;
  ticker?: string;
  event_type: TransactionEventType;
  event_date: string;
  quantity: number;
  price: number;
  gross_amount: number;
  commission: number;
  tax: number;
  notes?: string;
  corrected_by?: string;
}

export interface Holding {
  ticker: string;
  security_id?: string;
  quantity: number;
  total_cost: number;
  average_cost: number;
  market_value?: number;
  current_price?: number;
  unrealized_pl?: number;
  realized_pl: number;
  dividends: number;
  fees: number;
  taxes: number;
  portfolio_weight?: number;
}

export interface PortfolioState {
  cash: number;
  holdings: Map<string, Holding>;
  total_deposits: number;
  total_withdrawals: number;
  total_dividends: number;
  total_fees: number;
  total_taxes: number;
  total_realized_pl: number;
}

export function deriveHoldings(transactions: Transaction[], prices?: Map<string, number>): PortfolioState {
  const state: PortfolioState = {
    cash: 0,
    holdings: new Map(),
    total_deposits: 0,
    total_withdrawals: 0,
    total_dividends: 0,
    total_fees: 0,
    total_taxes: 0,
    total_realized_pl: 0,
  };

  const sorted = [...transactions].sort((a, b) =>
    new Date(a.event_date).getTime() - new Date(b.event_date).getTime()
  );

  for (const tx of sorted) {
    // Skip corrected transactions
    if (tx.corrected_by) continue;

    const ticker = tx.ticker || "";
    const qty = tx.quantity || 0;
    const price = tx.price || 0;
    const gross = tx.gross_amount || 0;
    const comm = tx.commission || 0;
    const tax = tx.tax || 0;

    switch (tx.event_type) {
      case "DEPOSIT":
      case "TRANSFER":
        state.cash += gross;
        state.total_deposits += gross;
        break;

      case "WITHDRAWAL":
        state.cash -= gross;
        state.total_withdrawals += gross;
        break;

      case "BUY": {
        const cost = gross + comm;
        if (cost > state.cash) {
          console.warn(`Insufficient cash for BUY ${ticker} on ${tx.event_date}`);
        }
        state.cash -= cost;

        let h = state.holdings.get(ticker);
        if (!h) {
          h = { ticker, quantity: 0, total_cost: 0, average_cost: 0, realized_pl: 0, dividends: 0, fees: 0, taxes: 0 };
          state.holdings.set(ticker, h);
        }
        // Average cost
        const newQty = h.quantity + qty;
        h.total_cost += cost;
        h.average_cost = newQty > 0 ? h.total_cost / newQty : 0;
        h.quantity = newQty;
        h.fees += comm;
        h.taxes += tax;
        break;
      }

      case "SELL": {
        const proceeds = gross - comm;
        state.cash += proceeds;

        const h = state.holdings.get(ticker);
        if (!h || h.quantity < qty) {
          console.warn(`Cannot sell ${qty} of ${ticker}, only ${h?.quantity || 0} held`);
          break;
        }
        const costOfSold = h.average_cost * qty;
        const realized = proceeds - costOfSold;
        h.realized_pl += realized;
        state.total_realized_pl += realized;
        h.quantity -= qty;
        h.total_cost -= costOfSold;
        h.fees += comm;
        h.taxes += tax;

        if (h.quantity <= 0) {
          state.holdings.delete(ticker);
        }
        break;
      }

      case "DIVIDEND":
        state.cash += gross;
        state.total_dividends += gross;
        {
          const h = state.holdings.get(ticker);
          if (h) h.dividends += gross;
        }
        break;

      case "FEE":
        state.cash -= gross;
        state.total_fees += gross;
        {
          const h = state.holdings.get(ticker);
          if (h) h.fees += gross;
        }
        break;

      case "TAX":
        state.cash -= gross;
        state.total_taxes += gross;
        break;

      case "INTEREST":
        state.cash += gross;
        break;

      case "SPLIT": {
        const h = state.holdings.get(ticker);
        if (h && qty !== 0) {
          const ratio = qty; // e.g., 2 for 2:1 split, 0.2 for 1:5 reverse
          h.quantity *= ratio;
          h.average_cost = h.quantity > 0 ? h.total_cost / h.quantity : 0;
        }
        break;
      }

      case "SYMBOL_CHANGE": {
        const h = state.holdings.get(ticker);
        if (h) {
          state.holdings.delete(ticker);
          const newHolding = { ...h, ticker: tx.notes || ticker };
          state.holdings.set(newHolding.ticker, newHolding);
        }
        break;
      }

      case "CORRECTION": {
        // Manual correction — adjust cash and holdings directly
        state.cash += gross;
        if (ticker && qty !== 0) {
          let h = state.holdings.get(ticker);
          if (!h && qty > 0) {
            h = { ticker, quantity: 0, total_cost: 0, average_cost: 0, realized_pl: 0, dividends: 0, fees: 0, taxes: 0 };
            state.holdings.set(ticker, h);
          }
          if (h) {
            h.quantity += qty;
            if (price > 0) {
              h.total_cost += qty * price;
              h.average_cost = h.quantity > 0 ? h.total_cost / h.quantity : 0;
            }
            if (h.quantity <= 0) state.holdings.delete(ticker);
          }
        }
        break;
      }

      case "OPENING_POSITION": {
        // Set initial holding without affecting cash
        if (ticker && qty > 0) {
          const totalCost = qty * price;
          state.holdings.set(ticker, {
            ticker, quantity: qty, total_cost: totalCost,
            average_cost: price, realized_pl: 0, dividends: 0, fees: 0, taxes: 0,
          });
        }
        break;
      }

      default:
        break;
    }
  }

  // Apply current prices
  if (prices) {
    for (const [ticker, h] of state.holdings) {
      const p = prices.get(ticker);
      if (p) {
        h.current_price = p;
        h.market_value = h.quantity * p;
        h.unrealized_pl = h.market_value - h.total_cost;
      }
    }
  }

  return state;
}

export function totalNav(state: PortfolioState): number {
  let holdingsValue = 0;
  for (const h of state.holdings.values()) {
    holdingsValue += h.market_value || 0;
  }
  return state.cash + holdingsValue;
}

export function calculateXIRR(transactions: Transaction[], currentValue: number): number {
  const flows: Array<[Date, number]> = [];
  for (const tx of transactions) {
    if (tx.corrected_by) continue;
    let amount = 0;
    if (tx.event_type === "DEPOSIT") amount = -tx.gross_amount;
    else if (tx.event_type === "WITHDRAWAL") amount = tx.gross_amount;
    else if (tx.event_type === "BUY") amount = -(tx.gross_amount + (tx.commission || 0));
    else if (tx.event_type === "SELL") amount = tx.gross_amount - (tx.commission || 0);
    else if (tx.event_type === "DIVIDEND") amount = tx.gross_amount;
    else if (tx.event_type === "FEE") amount = -tx.gross_amount;
    if (amount !== 0) {
      flows.push([new Date(tx.event_date), amount]);
    }
  }
  // Sort by date
  flows.sort((a, b) => a[0].getTime() - b[0].getTime());
  // Add final value
  if (flows.length > 0) {
    const lastDate = flows[flows.length - 1][0];
    flows.push([new Date(lastDate.getTime() + 86400000), currentValue]);
  }
  if (flows.length < 2) return 0;

  // Newton's method for XIRR
  let rate = 0.1;
  for (let iter = 0; iter < 100; iter++) {
    let npv = 0;
    let dnpv = 0;
    const days0 = flows[0][0].getTime();
    for (const [date, amount] of flows) {
      const years = (date.getTime() - days0) / (365.2425 * 86400000);
      npv += amount / Math.pow(1 + rate, years);
      dnpv -= years * amount / Math.pow(1 + rate, years + 1);
    }
    if (Math.abs(npv) < 1e-8) break;
    if (Math.abs(dnpv) < 1e-12) break;
    rate = rate - npv / dnpv;
  }
  return rate;
}
