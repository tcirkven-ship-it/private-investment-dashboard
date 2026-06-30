"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { insertTransaction } from "@/lib/actions";
import { Plus, Pencil, Trash2, X, Check } from "lucide-react";

interface Holding {
  ticker: string;
  quantity: number;
  total_cost: number;
  average_cost: number;
  market_value?: number;
  current_price?: number;
  unrealized_pl?: number;
}

interface AddForm {
  ticker: string;
  shares: string;
  avgCost: string;
  date: string;
}

interface EditForm {
  shares: string;
  avgCost: string;
}

export default function HoldingsManager({
  portfolioId,
  holdings,
  totalMarketValue,
  totalCostBasis,
  totalUnrealized,
  unrealizedPct,
  modelTickers,
}: {
  portfolioId: string;
  holdings: Holding[];
  totalMarketValue: number;
  totalCostBasis: number;
  totalUnrealized: number;
  unrealizedPct: number;
  modelTickers: Set<string>;
}) {
  const router = useRouter();
  const [showAdd, setShowAdd] = useState(false);
  const [addForm, setAddForm] = useState<AddForm>({ ticker: "", shares: "", avgCost: "", date: new Date().toISOString().split("T")[0] });
  const [editingTicker, setEditingTicker] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<EditForm>({ shares: "", avgCost: "" });
  const [deletingTicker, setDeletingTicker] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");

    const ticker = addForm.ticker.toUpperCase().trim();
    const shares = parseFloat(addForm.shares);
    const avgCost = parseFloat(addForm.avgCost);

    if (!ticker || isNaN(shares) || shares <= 0 || isNaN(avgCost) || avgCost < 0) {
      setError("Ticker, shares (>0), and avg cost (>=0) are required");
      setSaving(false);
      return;
    }

    if (holdings.some((h) => h.ticker === ticker)) {
      setError("Ticker already exists.");
      setSaving(false);
      return;
    }

    const fd = new FormData();
    fd.set("portfolio_id", portfolioId);
    fd.set("event_type", "BUY");
    fd.set("event_date", addForm.date);
    fd.set("ticker", ticker);
    fd.set("quantity", String(shares));
    fd.set("price", String(avgCost));
    fd.set("gross_amount", String(shares * avgCost));
    fd.set("commission", "0");

    const result = await insertTransaction(fd);
    if (result.error) {
      setError(result.error);
      setSaving(false);
    } else {
      setShowAdd(false);
      setAddForm({ ticker: "", shares: "", avgCost: "", date: new Date().toISOString().split("T")[0] });
      setSaving(false);
      router.refresh();
    }
  }

  function startEdit(h: Holding) {
    setEditingTicker(h.ticker);
    setEditForm({ shares: String(h.quantity), avgCost: String(h.average_cost.toFixed(2)) });
    setError("");
  }

  function cancelEdit() {
    setEditingTicker(null);
    setEditForm({ shares: "", avgCost: "" });
  }

  async function handleEdit(e: React.FormEvent, oldHolding: Holding) {
    e.preventDefault();
    setSaving(true);
    setError("");

    const newQty = parseFloat(editForm.shares);
    const newAvg = parseFloat(editForm.avgCost);

    if (isNaN(newQty) || newQty <= 0 || isNaN(newAvg) || newAvg < 0) {
      setError("Shares (>0) and avg cost (>=0) are required");
      setSaving(false);
      return;
    }

    const today = new Date().toISOString().split("T")[0];

    // SELL old position
    const sellFd = new FormData();
    sellFd.set("portfolio_id", portfolioId);
    sellFd.set("event_type", "SELL");
    sellFd.set("event_date", today);
    sellFd.set("ticker", oldHolding.ticker);
    sellFd.set("quantity", String(oldHolding.quantity));
    sellFd.set("price", String(oldHolding.average_cost));
    sellFd.set("gross_amount", String(oldHolding.quantity * oldHolding.average_cost));
    sellFd.set("commission", "0");
    const sellResult = await insertTransaction(sellFd);
    if (sellResult.error) {
      setError(sellResult.error);
      setSaving(false);
      return;
    }

    // BUY new position
    const buyFd = new FormData();
    buyFd.set("portfolio_id", portfolioId);
    buyFd.set("event_type", "BUY");
    buyFd.set("event_date", today);
    buyFd.set("ticker", oldHolding.ticker);
    buyFd.set("quantity", String(newQty));
    buyFd.set("price", String(newAvg));
    buyFd.set("gross_amount", String(newQty * newAvg));
    buyFd.set("commission", "0");
    const buyResult = await insertTransaction(buyFd);
    if (buyResult.error) {
      setError(buyResult.error);
      setSaving(false);
      return;
    }

    setEditingTicker(null);
    setEditForm({ shares: "", avgCost: "" });
    setSaving(false);
    router.refresh();
  }

  async function handleDelete(ticker: string, h: Holding) {
    setSaving(true);
    setError("");

    const today = new Date().toISOString().split("T")[0];

    const fd = new FormData();
    fd.set("portfolio_id", portfolioId);
    fd.set("event_type", "SELL");
    fd.set("event_date", today);
    fd.set("ticker", ticker);
    fd.set("quantity", String(h.quantity));
    fd.set("price", String(h.average_cost));
    fd.set("gross_amount", String(h.quantity * h.average_cost));
    fd.set("commission", "0");

    const result = await insertTransaction(fd);
    if (result.error) {
      setError(result.error);
    } else {
      setDeletingTicker(null);
      router.refresh();
    }
    setSaving(false);
  }

  const sortedHoldings = [...holdings].sort((a, b) => (b.market_value || 0) - (a.market_value || 0));

  return (
    <>
      {error && (
        <div className="text-sm text-red-400 bg-red-500/10 rounded px-3 py-2">{error}</div>
      )}

      <div className="flex items-center gap-2">
        <button onClick={() => { setShowAdd(!showAdd); setError(""); }} className="btn-primary text-sm">
          <Plus className="w-4 h-4 mr-1.5" />
          Add Holding
        </button>
      </div>

      {showAdd && (
        <form onSubmit={handleAdd} className="card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Add Holding</h3>
            <button type="button" onClick={() => setShowAdd(false)} className="btn-ghost p-1">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label className="text-xs text-neutral-500 block mb-1">Ticker</label>
              <input
                value={addForm.ticker}
                onChange={(e) => setAddForm({ ...addForm, ticker: e.target.value.toUpperCase() })}
                className="input text-sm"
                placeholder="AAPL"
                required
              />
            </div>
            <div>
              <label className="text-xs text-neutral-500 block mb-1">Shares</label>
              <input
                type="number"
                value={addForm.shares}
                onChange={(e) => setAddForm({ ...addForm, shares: e.target.value })}
                className="input text-sm"
                step="any"
                min="0"
                placeholder="100"
                required
              />
            </div>
            <div>
              <label className="text-xs text-neutral-500 block mb-1">Avg Cost ($)</label>
              <input
                type="number"
                value={addForm.avgCost}
                onChange={(e) => setAddForm({ ...addForm, avgCost: e.target.value })}
                className="input text-sm"
                step="0.01"
                min="0"
                placeholder="150.00"
                required
              />
            </div>
            <div>
              <label className="text-xs text-neutral-500 block mb-1">Purchase Date</label>
              <input
                type="date"
                value={addForm.date}
                onChange={(e) => setAddForm({ ...addForm, date: e.target.value })}
                className="input text-sm"
              />
            </div>
          </div>
          <button type="submit" disabled={saving || !addForm.ticker.trim() || !addForm.shares.trim()} className="btn-primary text-sm">
            {saving ? "Saving..." : "Add Holding"}
          </button>
        </form>
      )}

      {holdings.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No holdings yet.</p>
          <p className="text-sm text-neutral-600 mt-2">Click Add Holding to get started.</p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="table-header">Ticker</th>
                  <th className="table-header text-right">Shares</th>
                  <th className="table-header text-right">Avg Cost</th>
                  <th className="table-header text-right">Current Price</th>
                  <th className="table-header text-right">Market Value</th>
                  <th className="table-header text-right">Unrealized P/L</th>
                  <th className="table-header text-right">Unrealized P/L %</th>
                  <th className="table-header text-right">In Top 30?</th>
                  <th className="table-header text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedHoldings.map((h) => {
                  const isEditing = editingTicker === h.ticker;
                  const uplPct = h.total_cost > 0 ? ((h.unrealized_pl || 0) / h.total_cost) * 100 : 0;

                  if (isEditing) {
                    return (
                      <tr key={h.ticker} className="border-b border-neutral-800/50 bg-neutral-900/50">
                        <td className="table-cell-text font-semibold">{h.ticker}</td>
                        <td className="table-cell text-right">
                          <input
                            type="number"
                            value={editForm.shares}
                            onChange={(e) => setEditForm({ ...editForm, shares: e.target.value })}
                            className="input text-sm w-24 text-right"
                            step="any"
                            min="0"
                          />
                        </td>
                        <td className="table-cell text-right">
                          <input
                            type="number"
                            value={editForm.avgCost}
                            onChange={(e) => setEditForm({ ...editForm, avgCost: e.target.value })}
                            className="input text-sm w-24 text-right"
                            step="0.01"
                            min="0"
                          />
                        </td>
                        <td className="table-cell text-right">—</td>
                        <td className="table-cell text-right">—</td>
                        <td className="table-cell text-right">—</td>
                        <td className="table-cell text-right">—</td>
                        <td className="table-cell text-right">—</td>
                        <td className="table-cell text-right">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              onClick={(e) => handleEdit(e, h)}
                              disabled={saving}
                              className="btn-ghost p-1 text-green-400"
                              title="Save"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                            <button onClick={cancelEdit} className="btn-ghost p-1 text-red-400" title="Cancel">
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  }

                  return (
                    <tr key={h.ticker} className="border-b border-neutral-800/50">
                      <td className="table-cell-text font-semibold">{h.ticker}</td>
                      <td className="table-cell text-right">{h.quantity.toFixed(3)}</td>
                      <td className="table-cell text-right">${h.average_cost.toFixed(2)}</td>
                      <td className="table-cell text-right">
                        {h.current_price ? `$${h.current_price.toFixed(2)}` : "—"}
                      </td>
                      <td className="table-cell text-right">
                        {h.market_value ? `$${h.market_value.toLocaleString()}` : "—"}
                      </td>
                      <td className={`table-cell text-right ${(h.unrealized_pl || 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                        {h.unrealized_pl !== undefined ? `$${h.unrealized_pl.toFixed(2)}` : "—"}
                      </td>
                      <td className={`table-cell text-right ${uplPct >= 0 ? "text-green-400" : "text-red-400"}`}>
                        {h.unrealized_pl !== undefined ? `${uplPct >= 0 ? "+" : ""}${uplPct.toFixed(2)}%` : "—"}
                      </td>
                      <td className="table-cell text-right">
                        {modelTickers.size > 0
                          ? (modelTickers.has(h.ticker) ? "Yes" : "No")
                          : "—"}
                      </td>
                      <td className="table-cell text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => startEdit(h)}
                            className="btn-ghost p-1 text-neutral-400 hover:text-blue-400"
                            title="Edit"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          {deletingTicker === h.ticker ? (
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => handleDelete(h.ticker, h)}
                                disabled={saving}
                                className="btn-ghost p-1 text-red-400 text-xs"
                              >
                                Confirm
                              </button>
                              <button
                                onClick={() => setDeletingTicker(null)}
                                className="btn-ghost p-1 text-neutral-400 text-xs"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => setDeletingTicker(h.ticker)}
                              className="btn-ghost p-1 text-neutral-400 hover:text-red-400"
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
