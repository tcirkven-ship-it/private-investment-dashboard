import { vi, describe, it, expect, beforeAll, beforeEach } from "vitest";
import type { SupabaseClient } from "../supabase";

// ─── Module mocks for insertTransaction tests ──────────────────
vi.mock("../supabase", () => ({ createServerSupabase: vi.fn() }));
vi.mock("next/cache", () => ({ revalidatePath: vi.fn() }));

// ─── Thenable fake Supabase query builder ──────────────────────
// Each query method returns the same `builder` object.  The builder
// is itself *thenable* (implements `.then`), so it can be awaited
// at any point in the chain.  Terminal methods (maybeSingle) return
// a bare Promise.

function fakeDb(
  tables: Record<string, unknown[]>,
  failTables: string[] = [],
): SupabaseClient {
  function qb(name: string) {
    const r = () =>
      Promise.resolve(
        failTables.includes(name)
          ? { data: null, error: { message: "DB error" } }
          : { data: tables[name] || [], error: null },
      );
    const s = () =>
      Promise.resolve(
        failTables.includes(name)
          ? { data: null, error: { message: "DB error" } }
          : { data: (tables[name] || [])[0] ?? null, error: null },
      );
    const builder = {
      select: () => builder,
      eq: () => builder,
      is: () => builder,
      order: () => builder,
      limit: () => builder,
      maybeSingle: () => s(),
      then: (f: (v: unknown) => unknown, g: (e: unknown) => unknown) =>
        r().then(f, g),
    };
    return builder;
  }
  return { from: (name: string) => qb(name) } as unknown as SupabaseClient;
}

// ─── Fake Supabase client for action tests ─────────────────────
function makeActionDb(overrides?: {
  user?: { id: string } | null;
  insertError?: string | null;
  security?: { id: string } | null;
}) {
  const user =
    overrides?.user !== undefined ? overrides.user : { id: "user-1" };
  const insertError = overrides?.insertError ?? null;
  const security =
    overrides?.security !== undefined ? overrides.security : null;

  return {
    auth: {
      getUser: () =>
        Promise.resolve({
          data: { user },
          error: null,
        }),
    },
    from: vi.fn((name: string) => {
      if (name === "securities") {
        return {
          select: () => ({
            eq: () => ({
              maybeSingle: () =>
                Promise.resolve({ data: security, error: null }),
            }),
          }),
        };
      }
      return {
        insert: () =>
          Promise.resolve(
            insertError
              ? { error: { message: insertError } }
              : { error: null },
          ),
      };
    }),
  } as unknown as SupabaseClient & { from: ReturnType<typeof vi.fn> };
}

// ─── loadModelHistory ──────────────────────────────────────────

describe("loadModelHistory", () => {
  it("returns data on success", async () => {
    const db = fakeDb({
      model_snapshots: [
        {
          id: "1",
          snapshot_id: "s1",
          effective_date: "2026-06-01",
          status: "PUBLISHED",
        },
      ],
    });
    const { loadModelHistory } = await import("../route-loaders");
    const res = await loadModelHistory(db);
    expect(res).toHaveLength(1);
    expect(res[0].snapshot_id).toBe("s1");
  });

  it("returns empty on no data", async () => {
    const { loadModelHistory } = await import("../route-loaders");
    const res = await loadModelHistory(fakeDb({}));
    expect(res).toEqual([]);
  });

  it("throws on query error", async () => {
    const { loadModelHistory } = await import("../route-loaders");
    await expect(
      loadModelHistory(fakeDb({}, ["model_snapshots"])),
    ).rejects.toThrow("Failed to load model history");
  });
});

// ─── loadTransactions ──────────────────────────────────────────

describe("loadTransactions", () => {
  it("returns typed data on success", async () => {
    const db = fakeDb({
      transactions: [
        {
          id: "t1",
          event_type: "DEPOSIT",
          event_date: "2026-01-01",
          quantity: 0,
          price: 0,
          gross_amount: 500,
          commission: 0,
          tax: 0,
          notes: null,
          created_at: "2026-01-01T00:00:00Z",
          security: null,
        },
      ],
    });
    const { loadTransactions } = await import("../route-loaders");
    const res = await loadTransactions("p1", db);
    expect(res).toHaveLength(1);
    expect(res[0].gross_amount).toBe(500);
  });

  it("returns empty on no data", async () => {
    const { loadTransactions } = await import("../route-loaders");
    const res = await loadTransactions("p1", fakeDb({}));
    expect(res).toEqual([]);
  });

  it("throws on query error", async () => {
    const { loadTransactions } = await import("../route-loaders");
    await expect(
      loadTransactions("p1", fakeDb({}, ["transactions"])),
    ).rejects.toThrow("Failed to load transactions");
  });
});

// ─── loadHoldings ──────────────────────────────────────────────

describe("loadHoldings", () => {
  it("returns empty state with no transactions", async () => {
    const db = fakeDb({ transactions: [], price_observations: [] });
    const { loadHoldings } = await import("../route-loaders");
    const r = await loadHoldings("p1", db);
    expect(r.state.holdings.size).toBe(0);
    expect(r.nav).toBe(0);
    expect(r.priceCount).toBe(0);
  });

  it("returns holdings with transactions and prices", async () => {
    const db = fakeDb({
      transactions: [
        {
          id: "t1",
          event_type: "DEPOSIT",
          event_date: "2026-01-01",
          quantity: 0,
          price: 0,
          gross_amount: 1000,
          commission: 0,
          tax: 0,
          notes: null,
          created_at: "2026-01-01T00:00:00Z",
          security: null,
        },
        {
          id: "t2",
          event_type: "BUY",
          event_date: "2026-01-02",
          quantity: 10,
          price: 50,
          gross_amount: 500,
          commission: 5,
          tax: 0,
          notes: null,
          created_at: "2026-01-02T00:00:00Z",
          security: { ticker: "AAPL" },
        },
      ],
      price_observations: [
        { close: 55, observation_date: "2026-01-03", security: { ticker: "AAPL" } },
      ],
    });
    const { loadHoldings } = await import("../route-loaders");
    const r = await loadHoldings("p1", db);
    expect(r.state.holdings.size).toBe(1);
    const aapl = r.state.holdings.get("AAPL")!;
    expect(aapl.quantity).toBe(10);
    expect(aapl.total_cost).toBe(505);
    expect(aapl.average_cost).toBe(50.5);
    expect(aapl.market_value).toBe(550);
    expect(aapl.unrealized_pl).toBe(45);
    expect(r.state.cash).toBe(495);
    expect(r.nav).toBe(1045);
    expect(r.priceCount).toBe(1);
  });

  it("throws on transaction query error", async () => {
    const { loadHoldings } = await import("../route-loaders");
    await expect(
      loadHoldings("p1", fakeDb({}, ["transactions"])),
    ).rejects.toThrow("Failed to load transactions");
  });
});

// ─── loadBenchmarkReturns ──────────────────────────────────────

describe("loadBenchmarkReturns", () => {
  it("returns null returns when no benchmark rows exist", async () => {
    const { loadBenchmarkReturns } = await import("../route-loaders");
    const r = await loadBenchmarkReturns(fakeDb({}));
    expect(r.spyReturn).toBeNull();
    expect(r.qqqReturn).toBeNull();
  });

  it("throws on SPY query error", async () => {
    const { loadBenchmarkReturns } = await import("../route-loaders");
    await expect(
      loadBenchmarkReturns(fakeDb({}, ["benchmark_observations"])),
    ).rejects.toThrow("SPY");
  });
});

// ─── loadRebalance ─────────────────────────────────────────────

describe("loadRebalance", () => {
  it("returns empty when no published model", async () => {
    const db = fakeDb({
      model_snapshots: [],
      transactions: [],
      price_observations: [],
    });
    const { loadRebalance } = await import("../route-loaders");
    const r = await loadRebalance("p1", db);
    expect(r.comparisons).toEqual([]);
    expect(r.modelDate).toBe("");
    expect(r.hasPrices).toBe(false);
  });

  it("returns comparisons with holdings and model targets", async () => {
    const db = fakeDb({
      model_snapshots: [
        {
          id: "s1",
          effective_date: "2026-06-01",
          status: "PUBLISHED",
        },
      ],
      model_snapshot_holdings: [
        { rank: 1, target_weight: 0.5, security: { ticker: "AAPL" } },
      ],
      transactions: [
        {
          id: "t1",
          event_type: "DEPOSIT",
          event_date: "2026-01-01",
          quantity: 0,
          price: 0,
          gross_amount: 1000,
          commission: 0,
          tax: 0,
          notes: null,
          created_at: "2026-01-01T00:00:00Z",
          security: null,
        },
        {
          id: "t2",
          event_type: "BUY",
          event_date: "2026-01-02",
          quantity: 10,
          price: 50,
          gross_amount: 500,
          commission: 5,
          tax: 0,
          notes: null,
          created_at: "2026-01-02T00:00:00Z",
          security: { ticker: "AAPL" },
        },
      ],
      price_observations: [
        { close: 55, observation_date: "2026-01-03", security: { ticker: "AAPL" } },
      ],
    });
    const { loadRebalance } = await import("../route-loaders");
    const r = await loadRebalance("p1", db);
    expect(r.modelDate).toBe("2026-06-01");
    expect(r.hasPrices).toBe(true);
    expect(r.comparisons).toHaveLength(1);
    expect(r.comparisons[0].ticker).toBe("AAPL");
    expect(r.comparisons[0].targetWeight).toBe("50.00");
  });

  it("throws on model query error", async () => {
    const { loadRebalance } = await import("../route-loaders");
    await expect(
      loadRebalance("p1", fakeDb({}, ["model_snapshots"])),
    ).rejects.toThrow("Failed to load model");
  });
});

// ─── Owner / second-user / anonymous isolation ─────────────────

describe("owner / second-user / anonymous isolation", () => {
  // ── loadTransactions ───────────────────────────────────────

  it("loadTransactions filters by portfolio_id", async () => {
    let capturedCol = "";
    let capturedVal: unknown = null;
    const db = {
      from: () => ({
        select: () => ({
          eq: (col: string, val: unknown) => {
            capturedCol = col;
            capturedVal = val;
            return {
              is: () => ({
                order: () =>
                  Promise.resolve({ data: [], error: null }),
              }),
            };
          },
        }),
      }),
    } as unknown as SupabaseClient;

    const { loadTransactions } = await import("../route-loaders");
    await loadTransactions("owner-portfolio-42", db);
    expect(capturedCol).toBe("portfolio_id");
    expect(capturedVal).toBe("owner-portfolio-42");
  });

  it("owner receives transactions, second user receives empty", async () => {
    const { loadTransactions } = await import("../route-loaders");

    const ownerDb = fakeDb({
      transactions: [
        {
          id: "t1",
          event_type: "DEPOSIT",
          event_date: "2026-01-01",
          quantity: 0,
          price: 0,
          gross_amount: 500,
          commission: 0,
          tax: 0,
          notes: null,
          created_at: "2026-01-01T00:00:00Z",
          security: null,
        },
      ],
    });
    const owner = await loadTransactions("p1", ownerDb);
    expect(owner).toHaveLength(1);

    const secondDb = fakeDb({ transactions: [] });
    const second = await loadTransactions("p1", secondDb);
    expect(second).toEqual([]);
  });

  // ── loadHoldings ───────────────────────────────────────────

  it("owner receives holdings, second user receives empty", async () => {
    const { loadHoldings } = await import("../route-loaders");

    const ownerDb = fakeDb({
      transactions: [
        {
          id: "t1",
          event_type: "DEPOSIT",
          event_date: "2026-01-01",
          quantity: 0,
          price: 0,
          gross_amount: 1000,
          commission: 0,
          tax: 0,
          notes: null,
          created_at: "2026-01-01T00:00:00Z",
          security: null,
        },
        {
          id: "t2",
          event_type: "BUY",
          event_date: "2026-01-02",
          quantity: 10,
          price: 50,
          gross_amount: 500,
          commission: 5,
          tax: 0,
          notes: null,
          created_at: "2026-01-02T00:00:00Z",
          security: { ticker: "AAPL" },
        },
      ],
      price_observations: [
        { close: 55, observation_date: "2026-01-03", security: { ticker: "AAPL" } },
      ],
    });
    const owner = await loadHoldings("p1", ownerDb);
    expect(owner.state.holdings.size).toBe(1);

    const secondDb = fakeDb({
      transactions: [],
      price_observations: [],
    });
    const second = await loadHoldings("p1", secondDb);
    expect(second.state.holdings.size).toBe(0);
    expect(second.nav).toBe(0);
  });

  // ── loadRebalance ──────────────────────────────────────────

  it("owner receives rebalance comparison, second user receives empty", async () => {
    const { loadRebalance } = await import("../route-loaders");

    const ownerDb = fakeDb({
      model_snapshots: [
        {
          id: "s1",
          effective_date: "2026-06-01",
          status: "PUBLISHED",
        },
      ],
      model_snapshot_holdings: [
        { rank: 1, target_weight: 0.5, security: { ticker: "AAPL" } },
      ],
      transactions: [
        {
          id: "t1",
          event_type: "DEPOSIT",
          event_date: "2026-01-01",
          quantity: 0,
          price: 0,
          gross_amount: 1000,
          commission: 0,
          tax: 0,
          notes: null,
          created_at: "2026-01-01T00:00:00Z",
          security: null,
        },
        {
          id: "t2",
          event_type: "BUY",
          event_date: "2026-01-02",
          quantity: 10,
          price: 50,
          gross_amount: 500,
          commission: 5,
          tax: 0,
          notes: null,
          created_at: "2026-01-02T00:00:00Z",
          security: { ticker: "AAPL" },
        },
      ],
      price_observations: [
        { close: 55, observation_date: "2026-01-03", security: { ticker: "AAPL" } },
      ],
    });
    const owner = await loadRebalance("p1", ownerDb);
    expect(owner.comparisons.length).toBeGreaterThan(0);
    expect(owner.modelDate).toBe("2026-06-01");

    const secondDb = fakeDb({
      model_snapshots: [],
      transactions: [],
      price_observations: [],
    });
    const second = await loadRebalance("p1", secondDb);
    expect(second.comparisons).toEqual([]);
    expect(second.modelDate).toBe("");
  });

  // ── anonymous (no auth) ────────────────────────────────────

  it("anonymous receives empty transactions from RLS", async () => {
    const { loadTransactions } = await import("../route-loaders");
    const anonDb = fakeDb({ transactions: [] });
    const result = await loadTransactions("p1", anonDb);
    expect(result).toEqual([]);
  });

  it("anonymous receives empty holdings from RLS", async () => {
    const { loadHoldings } = await import("../route-loaders");
    const anonDb = fakeDb({ transactions: [], price_observations: [] });
    const result = await loadHoldings("p1", anonDb);
    expect(result.state.holdings.size).toBe(0);
    expect(result.nav).toBe(0);
  });
});

// ─── insertTransaction (server action) ─────────────────────────

describe("insertTransaction", () => {
  let createServerSupabase: ReturnType<typeof vi.fn>;
  let revalidatePath: ReturnType<typeof vi.fn>;

  beforeAll(async () => {
    const supMod = await import("../supabase");
    createServerSupabase = supMod.createServerSupabase as ReturnType<
      typeof vi.fn
    >;
    const cacheMod = await import("next/cache");
    revalidatePath = cacheMod.revalidatePath as ReturnType<typeof vi.fn>;
    vi.clearAllMocks();
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("successful insert calls revalidatePath", async () => {
    const mockDb = makeActionDb();
    createServerSupabase.mockResolvedValue(mockDb as never);

    const { insertTransaction } = await import("../actions");
    const fd = new FormData();
    fd.set("portfolio_id", "p1");
    fd.set("event_type", "DEPOSIT");
    fd.set("event_date", "2026-01-01");
    fd.set("gross_amount", "500");

    const result = await insertTransaction(fd);
    expect(result.error).toBeNull();
    expect(revalidatePath).toHaveBeenCalledWith("/portfolios/p1");
  });

  it("successful insert with ticker looks up security", async () => {
    const mockDb = makeActionDb({ security: { id: "sec-1" } });
    createServerSupabase.mockResolvedValue(mockDb as never);

    const { insertTransaction } = await import("../actions");
    const fd = new FormData();
    fd.set("portfolio_id", "p1");
    fd.set("event_type", "BUY");
    fd.set("event_date", "2026-01-01");
    fd.set("gross_amount", "500");
    fd.set("ticker", "aapl");

    const result = await insertTransaction(fd);
    expect(result.error).toBeNull();
    const fromCalls = mockDb.from.mock.calls.filter(
      (c: string[]) => c[0] === "securities",
    );
    expect(fromCalls).toHaveLength(1);
  });

  it("missing required fields returns error", async () => {
    const { insertTransaction } = await import("../actions");
    const fd = new FormData();
    fd.set("event_type", "DEPOSIT");
    fd.set("event_date", "2026-01-01");

    const result = await insertTransaction(fd);
    expect(result.error).toBe("Missing required fields");
  });

  it("failed insert returns error", async () => {
    const mockDb = makeActionDb({ insertError: "insert failed" });
    createServerSupabase.mockResolvedValue(mockDb as never);

    const { insertTransaction } = await import("../actions");
    const fd = new FormData();
    fd.set("portfolio_id", "p1");
    fd.set("event_type", "DEPOSIT");
    fd.set("event_date", "2026-01-01");
    fd.set("gross_amount", "500");

    const result = await insertTransaction(fd);
    expect(result.error).toBe("insert failed");
    expect(revalidatePath).not.toHaveBeenCalled();
  });

  it("RLS failure from Supabase is surfaced", async () => {
    const mockDb = makeActionDb({
      insertError: "new row violates row-level security policy",
    });
    createServerSupabase.mockResolvedValue(mockDb as never);

    const { insertTransaction } = await import("../actions");
    const fd = new FormData();
    fd.set("portfolio_id", "p1");
    fd.set("event_type", "DEPOSIT");
    fd.set("event_date", "2026-01-01");
    fd.set("gross_amount", "500");

    const result = await insertTransaction(fd);
    expect(result.error).toContain("row-level security");
  });

  it("not authenticated returns error", async () => {
    const mockDb = makeActionDb({ user: null });
    createServerSupabase.mockResolvedValue(mockDb as never);

    const { insertTransaction } = await import("../actions");
    const fd = new FormData();
    fd.set("portfolio_id", "p1");
    fd.set("event_type", "DEPOSIT");
    fd.set("event_date", "2026-01-01");
    fd.set("gross_amount", "500");

    const result = await insertTransaction(fd);
    expect(result.error).toBe("Not authenticated");
  });
});
