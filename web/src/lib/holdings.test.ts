import { describe, it, expect } from "vitest";
import { deriveHoldings, totalNav, calculateXIRR } from "./holdings";

function tx(overrides: Partial<import("./holdings").Transaction> = {}): import("./holdings").Transaction {
  return {
    event_type: "DEPOSIT",
    event_date: "2026-01-01",
    quantity: 0,
    price: 0,
    gross_amount: 0,
    commission: 0,
    tax: 0,
    ...overrides,
  };
}

describe("holdings engine", () => {
  it("deposit increases cash", () => {
    const s = deriveHoldings([tx({ event_type: "DEPOSIT", gross_amount: 100000 })]);
    expect(s.cash).toBe(100000);
  });

  it("buy decreases cash and creates holding", () => {
    const s = deriveHoldings([
      tx({ event_type: "DEPOSIT", gross_amount: 100000 }),
      tx({ event_type: "BUY", ticker: "AAPL", quantity: 10, price: 150, gross_amount: 1500, commission: 5 }),
    ]);
    expect(s.cash).toBeCloseTo(98495);
    expect(s.holdings.get("AAPL")?.quantity).toBe(10);
    expect(s.holdings.get("AAPL")?.average_cost).toBeCloseTo(150.5);
  });

  it("sell reduces holding and records realized gain", () => {
    const s = deriveHoldings([
      tx({ event_type: "DEPOSIT", gross_amount: 100000 }),
      tx({ event_type: "BUY", ticker: "AAPL", quantity: 10, price: 100, gross_amount: 1000, commission: 5 }),
      tx({ event_type: "SELL", ticker: "AAPL", quantity: 5, price: 150, gross_amount: 750, commission: 5 }),
    ]);
    expect(s.holdings.get("AAPL")?.quantity).toBe(5);
    expect(s.holdings.get("AAPL")?.realized_pl).toBeCloseTo(242.5);
    expect(s.total_realized_pl).toBeCloseTo(242.5);
  });

  it("dividend increases cash", () => {
    const s = deriveHoldings([
      tx({ event_type: "DEPOSIT", gross_amount: 100000 }),
      tx({ event_type: "BUY", ticker: "AAPL", quantity: 10, price: 150, gross_amount: 1500 }),
      tx({ event_type: "DIVIDEND", ticker: "AAPL", gross_amount: 50 }),
    ]);
    expect(s.cash).toBeCloseTo(98550);
    expect(s.total_dividends).toBe(50);
    expect(s.holdings.get("AAPL")?.dividends).toBe(50);
  });

  it("2:1 split doubles quantity", () => {
    const s = deriveHoldings([
      tx({ event_type: "DEPOSIT", gross_amount: 100000 }),
      tx({ event_type: "BUY", ticker: "AAPL", quantity: 10, price: 200, gross_amount: 2000 }),
      tx({ event_type: "SPLIT", ticker: "AAPL", quantity: 2 }),
    ]);
    expect(s.holdings.get("AAPL")?.quantity).toBe(20);
    expect(s.holdings.get("AAPL")?.average_cost).toBeCloseTo(100);
  });

  it("full liquidation zeroes holding", () => {
    const s = deriveHoldings([
      tx({ event_type: "DEPOSIT", gross_amount: 100000 }),
      tx({ event_type: "BUY", ticker: "AAPL", quantity: 10, price: 100, gross_amount: 1000 }),
      tx({ event_type: "SELL", ticker: "AAPL", quantity: 10, price: 110, gross_amount: 1100 }),
    ]);
    expect(s.holdings.has("AAPL")).toBe(false);
  });

  it("fee reduces cash", () => {
    const s = deriveHoldings([
      tx({ event_type: "DEPOSIT", gross_amount: 100000 }),
      tx({ event_type: "FEE", gross_amount: 10 }),
    ]);
    expect(s.cash).toBe(99990);
    expect(s.total_fees).toBe(10);
  });

  it("corrected_by skips corrected transactions", () => {
    const s = deriveHoldings([
      tx({ event_type: "DEPOSIT", gross_amount: 100000, id: "1" }),
      tx({ event_type: "BUY", ticker: "AAPL", quantity: 10, price: 100, gross_amount: 1000, id: "2" }),
      tx({ event_type: "SELL", ticker: "AAPL", quantity: 10, price: 110, gross_amount: 1100, id: "3" }),
      tx({ event_type: "BUY", ticker: "AAPL", quantity: 10, price: 100, gross_amount: 1000, id: "4", corrected_by: "2" }),
    ]);
    // The corrected transaction should be ignored
    expect(s.holdings.get("AAPL")).toBeUndefined();
    expect(s.cash).toBeCloseTo(100100);
  });

  it("prices produce market values", () => {
    const prices = new Map([["AAPL", 200]]);
    const s = deriveHoldings([
      tx({ event_type: "DEPOSIT", gross_amount: 100000 }),
      tx({ event_type: "BUY", ticker: "AAPL", quantity: 10, price: 150, gross_amount: 1500 }),
    ], prices);
    expect(s.holdings.get("AAPL")?.market_value).toBe(2000);
    expect(s.holdings.get("AAPL")?.unrealized_pl).toBeCloseTo(500);
  });

  it("XIRR calculation", () => {
    const r = calculateXIRR([
      tx({ event_type: "DEPOSIT", event_date: "2026-01-01", gross_amount: 1000 }),
      tx({ event_type: "WITHDRAWAL", event_date: "2026-07-01", gross_amount: 500 }),
    ], 600);
    expect(r).not.toBe(0);
    expect(isFinite(r)).toBe(true);
  });
});
