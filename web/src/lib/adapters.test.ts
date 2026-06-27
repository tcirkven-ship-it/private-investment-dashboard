import { describe, it, expect } from "vitest";
import { getSecurity, getTicker, getPriceObservation, getModelHolding, getTransaction } from "./adapters";

describe("adapters", () => {
  describe("getSecurity", () => {
    it("returns null for null input", () => {
      expect(getSecurity(null)).toBeNull();
    });
    it("returns null for missing ticker", () => {
      expect(getSecurity({})).toBeNull();
    });
    it("extracts ticker from single object", () => {
      expect(getSecurity({ ticker: "AAPL" })?.ticker).toBe("AAPL");
    });
    it("extracts ticker from array", () => {
      expect(getSecurity([{ ticker: "MSFT" }])?.ticker).toBe("MSFT");
    });
    it("returns null for empty array", () => {
      expect(getSecurity([])).toBeNull();
    });
  });

  describe("getTicker", () => {
    it("returns empty string for null", () => {
      expect(getTicker(null)).toBe("");
    });
    it("returns ticker from object", () => {
      expect(getTicker([{ ticker: "GOOGL" }])).toBe("GOOGL");
    });
  });

  describe("getPriceObservation", () => {
    it("returns null for missing security", () => {
      expect(getPriceObservation({ close: 150 })).toBeNull();
    });
    it("extracts ticker and close", () => {
      const obs = getPriceObservation({ close: 200, security: { ticker: "AAPL" } });
      expect(obs?.ticker).toBe("AAPL");
      expect(obs?.close).toBe(200);
    });
  });

  describe("getModelHolding", () => {
    it("returns null for missing rank", () => {
      expect(getModelHolding({ target_weight: 0.5 })).toBeNull();
    });
    it("extracts rank, weight and ticker", () => {
      const h = getModelHolding({ rank: 1, target_weight: 0.0333, security: { ticker: "AAPL" } });
      expect(h?.rank).toBe(1);
      expect(h?.target_weight).toBeCloseTo(0.0333);
      expect(h?.ticker).toBe("AAPL");
    });
  });

  describe("getTransaction", () => {
    it("returns null for missing id", () => {
      expect(getTransaction({ event_type: "BUY" })).toBeNull();
    });
    it("extracts all fields", () => {
      const t = getTransaction({
        id: "tx-1", event_type: "DEPOSIT", event_date: "2026-01-01",
        gross_amount: 1000, security: { ticker: "" },
      });
      expect(t?.id).toBe("tx-1");
      expect(t?.event_type).toBe("DEPOSIT");
      expect(t?.gross_amount).toBe(1000);
    });
  });
});
