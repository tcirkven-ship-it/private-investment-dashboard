"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { insertTransaction } from "@/lib/actions";
import { Plus, Trash2, X } from "lucide-react";

interface Holding {
  ticker: string;
  quantity: number;
  total_cost: number;
  average_cost: number;
  market_value?: number;
  current_price?: number;
  unrealized_pl?: number;
}

export default function HoldingsManager({
  portfolioId, holdings, totalMarketValue, totalCostBasis, totalUnrealized, unrealizedPct, modelTickers,
}: {
  portfolioId: string; holdings: Holding[]; totalMarketValue: number; totalCostBasis: number;
  totalUnrealized: number; unrealizedPct: number; modelTickers: Set<string>;
}) {
  const router = useRouter();
  const [showForm, setShowForm] = useState<"opening" | "buy" | "sell" | null>(null);
  const [ticker, setTicker] = useState("");
  const [shares, setShares] = useState("");
  const [price, setPrice] = useState("");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [deletingTicker, setDeletingTicker] = useState<string | null>(null);

  function reset() { setTicker(""); setShares(""); setPrice(""); setSaving(false); setError(""); setShowForm(null); }

  async function submit(eventType: string) {
    setSaving(true); setError("");
    const t = ticker.toUpperCase().trim();
    const qty = parseFloat(shares);
    const pr = parseFloat(price);
    const fd = new FormData();
    fd.set("portfolio_id", portfolioId);
    fd.set("event_type", eventType);
    fd.set("event_date", date);
    if (t) fd.set("ticker", t);
    if (!isNaN(qty)) fd.set("quantity", String(qty));
    if (!isNaN(pr)) fd.set("price", String(pr));
    if (eventType === "SELL" && qty > 0) {
      const h = holdings.find(x => x.ticker === t);
      if (h && qty > h.quantity) { setError(`Cannot sell ${qty} shares. You own ${h.quantity.toFixed(3)}.`); setSaving(false); return; }
    }
    if (!t || isNaN(qty) || qty <= 0 || isNaN(pr) || pr < 0) { setError("Ticker, shares (>0), and price (>=0) are required"); setSaving(false); return; }
    fd.set("gross_amount", String(qty * pr));
    const r = await insertTransaction(fd);
    if (r.error) { setError(r.error); setSaving(false); } else { reset(); router.refresh(); }
  }

  async function handleDelete(ticker: string, h: Holding) {
    setSaving(true); setError("");
    const today = new Date().toISOString().split("T")[0];
    const fd = new FormData();
    fd.set("portfolio_id", portfolioId);
    fd.set("event_type", "SELL");
    fd.set("event_date", today);
    fd.set("ticker", ticker);
    fd.set("quantity", String(h.quantity));
    fd.set("price", String(h.average_cost));
    fd.set("gross_amount", String(h.quantity * h.average_cost));
    const r = await insertTransaction(fd);
    if (r.error) { setError(r.error); } else { setDeletingTicker(null); router.refresh(); }
    setSaving(false);
  }

  const sortedHoldings = [...holdings].sort((a, b) => (b.market_value || 0) - (a.market_value || 0));

  return (
    <>
      {error && <div className="text-sm text-red-400 bg-red-500/10 rounded px-3 py-2">{error}</div>}

      <div className="flex flex-wrap gap-2">
        <button onClick={() => { setShowForm("opening"); reset(); }} className="btn-ghost text-sm"><Plus className="w-3.5 h-3.5 mr-1" />Add Opening Position</button>
        <button onClick={() => { setShowForm("buy"); reset(); }} className="btn-ghost text-sm"><Plus className="w-3.5 h-3.5 mr-1" />Add Buy</button>
        <button onClick={() => { setShowForm("sell"); reset(); }} className="btn-ghost text-sm">Add Sell</button>
      </div>

      {showForm && (
        <form onSubmit={(e) => { e.preventDefault(); submit(showForm); }} className="card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Add {showForm === "opening" ? "Opening Position" : showForm === "buy" ? "Buy" : "Sell"}</h3>
            <button type="button" onClick={reset} className="btn-ghost p-1"><X className="w-4 h-4" /></button>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div><label className="text-xs text-neutral-500 block mb-1">Ticker</label><input value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())} className="input text-sm" required /></div>
            <div><label className="text-xs text-neutral-500 block mb-1">Shares</label><input type="number" value={shares} onChange={e => setShares(e.target.value)} className="input text-sm" step="any" min="0" required /></div>
            <div><label className="text-xs text-neutral-500 block mb-1">{showForm === "opening" ? "Avg Cost ($)" : "Price ($)"}</label><input type="number" value={price} onChange={e => setPrice(e.target.value)} className="input text-sm" step="0.01" min="0" required /></div>
          </div>
          <div className="flex items-center gap-2">
            <div><label className="text-xs text-neutral-500 block mb-1">Date</label><input type="date" value={date} onChange={e => setDate(e.target.value)} className="input text-sm" /></div>
            <button type="submit" disabled={saving} className="btn-primary text-sm mt-4">{saving ? "Saving..." : "Save"}</button>
          </div>
        </form>
      )}

      {holdings.length === 0 ? (
        <div className="card text-center py-12"><p className="text-neutral-500">No holdings yet.</p></div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="table-header">Ticker</th><th className="table-header text-right">Shares</th><th className="table-header text-right">Avg Cost</th>
                  <th className="table-header text-right">Price</th><th className="table-header text-right">Mkt Value</th><th className="table-header text-right">P/L</th><th className="table-header text-right">In Top 30?</th><th className="table-header text-right"></th>
                </tr>
              </thead>
              <tbody>
                {sortedHoldings.map((h) => {
                  const uplPct = h.total_cost > 0 ? ((h.unrealized_pl || 0) / h.total_cost) * 100 : 0;
                  const rows = [];
                  rows.push(
                    <tr key={h.ticker} className="border-b border-neutral-800/50">
                      <td className="table-cell-text font-semibold">{h.ticker}</td>
                      <td className="table-cell text-right">{h.quantity.toFixed(3)}</td>
                      <td className="table-cell text-right">${h.average_cost.toFixed(2)}</td>
                      <td className="table-cell text-right">{h.current_price ? `$${h.current_price.toFixed(2)}` : "—"}</td>
                      <td className="table-cell text-right">{h.market_value ? `$${h.market_value.toLocaleString()}` : "—"}</td>
                      <td className={`table-cell text-right ${(h.unrealized_pl || 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                        {h.unrealized_pl !== undefined ? `$${h.unrealized_pl.toFixed(2)}` : "—"}
                      </td>
                      <td className="table-cell text-right">{modelTickers.size > 0 ? (modelTickers.has(h.ticker) ? "Yes" : "No") : "—"}</td>
                      <td className="table-cell text-right">
                        {deletingTicker === h.ticker ? (
                          <span className="flex items-center gap-1"><button onClick={() => handleDelete(h.ticker, h)} disabled={saving} className="text-red-400 text-xs">Confirm</button><button onClick={() => setDeletingTicker(null)} className="text-neutral-400 text-xs">Cancel</button></span>
                        ) : (
                          <button onClick={() => setDeletingTicker(h.ticker)} className="btn-ghost p-1 text-neutral-400 hover:text-red-400"><Trash2 className="w-3 h-3" /></button>
                        )}
                      </td>
                    </tr>
                  );
                  return rows;
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
