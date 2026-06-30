"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { insertTransaction } from "@/lib/actions";
import { Plus, X } from "lucide-react";

const TX_TYPES = ["DEPOSIT", "WITHDRAWAL", "BUY", "SELL"] as const;

interface Holding {
  ticker: string; quantity: number; total_cost: number; average_cost: number;
  market_value?: number; current_price?: number; unrealized_pl?: number;
}

export default function HoldingsManager({
  portfolioId, holdings, cash, totalMarketValue, totalCostBasis, totalUnrealized, modelTickers,
}: {
  portfolioId: string; holdings: Holding[]; cash: number; totalMarketValue: number;
  totalCostBasis: number; totalUnrealized: number; modelTickers: Set<string>;
}) {
  const router = useRouter();
  const [showForm, setShowForm] = useState(false);
  const [txType, setTxType] = useState<string>("BUY");
  const [ticker, setTicker] = useState("");
  const [shares, setShares] = useState("");
  const [price, setPrice] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function reset() { setTicker(""); setShares(""); setPrice(""); setAmount(""); setSaving(false); setError(""); }
  const needsTicker = txType === "BUY" || txType === "SELL";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true); setError("");
    const fd = new FormData();
    fd.set("portfolio_id", portfolioId);
    fd.set("event_type", txType);
    fd.set("event_date", date);
    if (needsTicker) {
      const t = ticker.toUpperCase().trim();
      const qty = parseFloat(shares);
      const pr = parseFloat(price);
      if (!t || isNaN(qty) || qty <= 0 || isNaN(pr) || pr < 0) { setError("Ticker, shares (>0), and price (>=0) required"); setSaving(false); return; }
      if (txType === "SELL") {
        const h = holdings.find(x => x.ticker === t);
        if (h && qty > h.quantity) { setError(`Cannot sell ${qty} shares. You own ${h.quantity.toFixed(3)}.`); setSaving(false); return; }
      }
      fd.set("ticker", t);
      fd.set("quantity", String(qty));
      fd.set("price", String(pr));
      fd.set("gross_amount", String(qty * pr));
    } else {
      const amt = parseFloat(amount);
      if (isNaN(amt) || amt <= 0) { setError("Amount required"); setSaving(false); return; }
      fd.set("gross_amount", String(amt));
    }
    const r = await insertTransaction(fd);
    if (r.error) { setError(r.error); setSaving(false); } else { reset(); router.refresh(); }
  }

  const nav = cash + totalMarketValue;
  const sorted = [...holdings].sort((a, b) => (b.market_value || 0) - (a.market_value || 0));

  return (
    <>
      {error && <div className="text-sm text-red-400 bg-red-500/10 rounded px-3 py-2">{error}</div>}

      <div className="flex flex-wrap gap-2 items-center">
        <button onClick={() => { setShowForm(!showForm); reset(); }} className="btn-primary text-sm"><Plus className="w-3.5 h-3.5 mr-1" />New Transaction</button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">New Transaction</h3>
            <button type="button" onClick={() => setShowForm(false)} className="btn-ghost p-1"><X className="w-4 h-4" /></button>
          </div>
          <div className="flex items-center gap-3">
            <div><label className="text-xs text-neutral-500 block mb-1">Type</label>
              <select value={txType} onChange={e => setTxType(e.target.value)} className="input text-sm">
                {TX_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div><label className="text-xs text-neutral-500 block mb-1">Date</label>
              <input type="date" value={date} onChange={e => setDate(e.target.value)} className="input text-sm w-36" />
            </div>
          </div>
          {needsTicker ? (
            <div className="grid grid-cols-3 gap-3">
              <div><label className="text-xs text-neutral-500 block mb-1">Ticker</label><input value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())} className="input text-sm" placeholder="MU" /></div>
              <div><label className="text-xs text-neutral-500 block mb-1">Shares</label><input type="number" value={shares} onChange={e => setShares(e.target.value)} className="input text-sm" step="any" min="0" /></div>
              <div><label className="text-xs text-neutral-500 block mb-1">Price ($)</label><input type="number" value={price} onChange={e => setPrice(e.target.value)} className="input text-sm" step="0.01" min="0" /></div>
            </div>
          ) : (
            <div><label className="text-xs text-neutral-500 block mb-1">Amount ($)</label><input type="number" value={amount} onChange={e => setAmount(e.target.value)} className="input text-sm w-48" step="0.01" min="0" /></div>
          )}
          <button type="submit" disabled={saving} className="btn-primary text-sm">{saving ? "Saving..." : "Save Transaction"}</button>
        </form>
      )}

      <div className="grid grid-cols-4 gap-4">
        <div className="card"><p className="metric-label">Total Value</p><p className="metric-value mt-1">${nav.toLocaleString()}</p></div>
        <div className="card"><p className="metric-label">Cash</p><p className="metric-value mt-1">${cash.toLocaleString()}</p></div>
        <div className="card"><p className="metric-label">Cost Basis</p><p className="metric-value mt-1">${totalCostBasis.toLocaleString()}</p></div>
        <div className="card"><p className="metric-label">Unrealized P/L</p><p className={`metric-value mt-1 ${totalUnrealized >= 0 ? "text-green-400" : "text-red-400"}`}>${totalUnrealized.toFixed(2)}</p></div>
      </div>

      {sorted.length === 0 ? (
        <div className="card text-center py-12"><p className="text-neutral-500">No holdings yet.</p></div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead><tr className="border-b border-neutral-800"><th className="table-header">Ticker</th><th className="table-header text-right">Shares</th><th className="table-header text-right">Avg Cost</th><th className="table-header text-right">Price</th><th className="table-header text-right">Mkt Value</th><th className="table-header text-right">P/L</th><th className="table-header text-right">In Top 30?</th></tr></thead>
              <tbody>
                {sorted.map(h => (
                  <tr key={h.ticker} className="border-b border-neutral-800/50">
                    <td className="table-cell-text font-semibold">{h.ticker}</td>
                    <td className="table-cell text-right">{h.quantity.toFixed(3)}</td>
                    <td className="table-cell text-right">${h.average_cost.toFixed(2)}</td>
                    <td className="table-cell text-right">{h.current_price ? `$${h.current_price.toFixed(2)}` : "—"}</td>
                    <td className="table-cell text-right">{h.market_value ? `$${h.market_value.toLocaleString()}` : "—"}</td>
                    <td className={`table-cell text-right ${(h.unrealized_pl||0) >= 0 ? "text-green-400" : "text-red-400"}`}>{h.unrealized_pl !== undefined ? `$${h.unrealized_pl.toFixed(2)}` : "—"}</td>
                    <td className="table-cell text-right">{modelTickers.size > 0 ? (modelTickers.has(h.ticker) ? "Yes" : "No") : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
