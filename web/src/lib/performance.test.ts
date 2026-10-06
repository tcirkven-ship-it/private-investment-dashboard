import { describe, it, expect } from "vitest";
import {
  computeInvestedCapital,
  totalPnl,
  totalReturnPct,
  buildQuarterRows,
  buildInceptionRow,
  benchmarkQuarterReturns,
  quarterBounds,
  hasDeposit,
  type PerfTransaction,
} from "./performance";

function tx(overrides: Partial<PerfTransaction> = {}): PerfTransaction {
  return {
    event_type: "DEPOSIT",
    event_date: "2026-07-01",
    gross_amount: 0,
    commission: 0,
    ...overrides,
  };
}

describe("invested capital", () => {
  it("scenario 1: deposit 15000, value 16000 -> P&L +1000, return +6.67%", () => {
    const txs = [
      tx({ event_type: "DEPOSIT", gross_amount: 15000 }),
      tx({ event_type: "BUY", gross_amount: 15000, commission: 10 }),
    ];
    const inv = computeInvestedCapital(txs);
    expect(inv).toEqual({ value: 15000, estimated: false });
    const pnl = totalPnl(16000, inv.value);
    expect(pnl).toBe(1000);
    expect(totalReturnPct(pnl, inv.value)).toBeCloseTo(6.6667, 3);
  });

  it("scenario 2: buys and sells never change invested capital", () => {
    const txs = [
      tx({ event_type: "DEPOSIT", gross_amount: 15000 }),
      tx({ event_type: "BUY", gross_amount: 5000, commission: 5 }),
      tx({ event_type: "SELL", gross_amount: 4000, commission: 5 }),
      tx({ event_type: "BUY", gross_amount: 4200, commission: 4 }),
    ];
    expect(computeInvestedCapital(txs).value).toBe(15000);
  });

  it("scenario 3: deposit 15000, withdraw 1000 -> net invested 14000, value 15500 -> P&L +1500", () => {
    const txs = [
      tx({ event_type: "DEPOSIT", gross_amount: 15000 }),
      tx({ event_type: "WITHDRAWAL", event_date: "2026-08-01", gross_amount: 1000 }),
      tx({ event_type: "BUY", gross_amount: 9000, commission: 5 }),
    ];
    const inv = computeInvestedCapital(txs);
    expect(inv.value).toBe(14000);
    expect(totalPnl(15500, inv.value)).toBe(1500);
    expect(totalReturnPct(1500, 14000)).toBeCloseTo(10.7143, 3);
  });

  it("falls back to an estimated capital when no deposits exist", () => {
    const txs = [
      tx({ event_type: "BUY", gross_amount: 500, commission: 5 }),
      tx({ event_type: "SELL", gross_amount: 100, commission: 2 }),
    ];
    const inv = computeInvestedCapital(txs);
    expect(inv.estimated).toBe(true);
    expect(inv.value).toBeCloseTo(407); // 505 in - 98 out
    expect(hasDeposit(txs)).toBe(false);
  });
});

describe("quarter rows", () => {
  it("scenario 4: quarter start 15000, end 16000, no flows -> +6.67%", () => {
    const rows = buildQuarterRows({
      transactions: [tx({ event_type: "DEPOSIT", event_date: "2026-06-30", gross_amount: 15000 })],
      valuations: [
        { valuation_date: "2026-07-01", total_value: 15000 },
        { valuation_date: "2026-09-30", total_value: 16000 },
      ],
      currentValue: 16000,
      today: "2026-10-06",
    });
    const q3 = rows.find((r) => r.label === "2026-Q3")!;
    expect(q3.startValue).toBe(15000);
    expect(q3.endValue).toBe(16000);
    expect(q3.externalFlow).toBe(0);
    expect(q3.pnl).toBe(1000);
    expect(q3.returnPct).toBeCloseTo(6.6667, 3);
  });

  it("scenario 5: quarter start 15000, end 17000, deposit 1000 in-quarter -> P&L +1000", () => {
    const rows = buildQuarterRows({
      transactions: [
        tx({ event_type: "DEPOSIT", event_date: "2026-06-30", gross_amount: 15000 }),
        tx({ event_type: "DEPOSIT", event_date: "2026-08-15", gross_amount: 1000 }),
      ],
      valuations: [
        { valuation_date: "2026-07-01", total_value: 15000 },
        { valuation_date: "2026-09-30", total_value: 17000 },
      ],
      currentValue: 17000,
      today: "2026-10-06",
    });
    const q3 = rows.find((r) => r.label === "2026-Q3")!;
    expect(q3.externalFlow).toBe(1000);
    expect(q3.pnl).toBe(1000);
  });

  it("sells are not treated as withdrawals in quarter flows", () => {
    const rows = buildQuarterRows({
      transactions: [
        tx({ event_type: "DEPOSIT", event_date: "2026-07-01", gross_amount: 15000 }),
        tx({ event_type: "SELL", event_date: "2026-08-01", gross_amount: 3000 }),
        tx({ event_type: "BUY", event_date: "2026-08-02", gross_amount: 2900 }),
      ],
      valuations: [],
      currentValue: 15500,
      today: "2026-08-10",
    });
    const q3 = rows.find((r) => r.label === "2026-Q3")!;
    expect(q3.externalFlow).toBe(15000);
  });

  it("current quarter uses the live value as end value", () => {
    const rows = buildQuarterRows({
      transactions: [tx({ event_type: "DEPOSIT", event_date: "2026-07-01", gross_amount: 15000 })],
      valuations: [{ valuation_date: "2026-09-30", total_value: 16000 }],
      currentValue: 16500,
      today: "2026-10-06",
    });
    const q4 = rows.find((r) => r.label === "2026-Q4")!;
    expect(q4.isCurrent).toBe(true);
    expect(q4.startValue).toBe(16000);
    expect(q4.endValue).toBe(16500);
    expect(q4.pnl).toBe(500);
  });
});

describe("benchmark quarter returns", () => {
  it("computes a quarterly return from total-return index observations", () => {
    const map = benchmarkQuarterReturns([
      { observation_date: "2026-07-01", total_return_index: 100 },
      { observation_date: "2026-09-30", total_return_index: 110 },
    ]);
    expect(map.get("2026-Q3")).toBeCloseTo(10);
  });

  it("returns null when a quarter lacks observations", () => {
    const map = benchmarkQuarterReturns([
      { observation_date: "2026-09-30", total_return_index: 110 },
    ]);
    expect(map.get("2026-Q3")).toBeNull();
  });
});

describe("quarter bounds", () => {
  it("computes correct calendar bounds", () => {
    expect(quarterBounds("2026-Q3")).toEqual({ start: "2026-07-01", end: "2026-09-30" });
    expect(quarterBounds("2026-Q4")).toEqual({ start: "2026-10-01", end: "2026-12-31" });
    expect(quarterBounds("2027-Q1")).toEqual({ start: "2027-01-01", end: "2027-03-31" });
  });
});

describe("populated fallbacks and inception row", () => {
  it("inception quarter start is 0 when the portfolio had no prior activity", () => {
    const rows = buildQuarterRows({
      transactions: [tx({ event_type: "DEPOSIT", event_date: "2026-07-01", gross_amount: 15000 })],
      valuations: [],
      currentValue: 13239.33,
      today: "2026-10-06",
    });
    const q3 = rows.find((r) => r.label === "2026-Q3")!;
    expect(q3.startValue).toBe(0);
    expect(q3.endValue).toBeCloseTo(13239.33);
    expect(q3.endValueEstimated).toBe(true);
    expect(q3.pnl).toBeCloseTo(-1760.67);
    expect(q3.returnPct).toBeCloseTo(-11.7378, 3);
  });

  it("only the last completed quarter uses the current value when no snapshots exist", () => {
    const rows = buildQuarterRows({
      transactions: [
        tx({ event_type: "DEPOSIT", event_date: "2026-01-05", gross_amount: 1000 }),
        tx({ event_type: "DEPOSIT", event_date: "2026-07-05", gross_amount: 1000 }),
      ],
      valuations: [],
      currentValue: 2100,
      today: "2026-10-06",
    });
    const q1 = rows.find((r) => r.label === "2026-Q1")!;
    const q3 = rows.find((r) => r.label === "2026-Q3")!;
    expect(q3.endValue).toBe(2100);
    expect(q1.endValue).toBeNull();
    expect(q1.pnl).toBeNull();
  });

  it("an in-quarter snapshot is used as start with a date note", () => {
    const rows = buildQuarterRows({
      transactions: [tx({ event_type: "DEPOSIT", event_date: "2026-06-15", gross_amount: 5000 })],
      valuations: [{ valuation_date: "2026-08-01", total_value: 5200 }],
      currentValue: 5300,
      today: "2026-10-06",
    });
    const q3 = rows.find((r) => r.label === "2026-Q3")!;
    expect(q3.startValue).toBe(5200);
    expect(q3.startValueNote).toBe("as of 2026-08-01");
  });

  it("inception row reports lifetime figures and benchmark range", () => {
    const row = buildInceptionRow({
      transactions: [tx({ event_type: "DEPOSIT", event_date: "2026-07-01", gross_amount: 15000 })],
      currentValue: 13239.33,
      netInvested: 15000,
      today: "2026-10-06",
      benchmarkObservations: {
        SPY: [
          { observation_date: "2026-06-30", total_return_index: 100 },
          { observation_date: "2026-10-06", total_return_index: 102 },
        ],
      },
    });
    expect(row.label).toBe("Since inception");
    expect(row.isInception).toBe(true);
    expect(row.startValue).toBe(0);
    expect(row.externalFlow).toBe(15000);
    expect(row.pnl).toBeCloseTo(-1760.67);
    expect(row.returnPct).toBeCloseTo(-11.7378, 3);
    expect(row.spyReturnPct).toBeCloseTo(2);
  });
});
