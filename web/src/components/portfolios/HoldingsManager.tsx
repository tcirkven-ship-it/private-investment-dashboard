"use client";

import { useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { insertTransaction } from "@/lib/actions";
import { DUST_QUANTITY_THRESHOLD } from "@/lib/holdings";
import { Plus, X, Trash2 } from "lucide-react";

const TX_TYPES = ["DEPOSIT", "WITHDRAWAL", "BUY", "SELL"] as const;

interface Holding {
  ticker: string; quantity: number; total_cost: number; average_cost: number;
  market_value?: number; current_price?: number; unrealized_pl?: number;
}

export default function HoldingsManager({
  portfolioId, holdings, cash, totalMarketValue, totalCostBasis, totalUnrealized, totalRealized, modelTickers,
  toolbarActions,
}: {
  portfolioId: string; holdings: Holding[]; cash: number; totalMarketValue: number;
  totalCostBasis: number; totalUnrealized: number; totalRealized: number; modelTickers: Set<string>;
  toolbarActions?: ReactNode;
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
  const [deletingTicker, setDeletingTicker] = useState<string | null>(null);

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

  async function handleDelete(h: Holding) {
    setSaving(true); setError("");
    // Dust/closed positions cannot be sold (below the ledger's 6-dp resolution).
    // The holdings engine already treats them as closed; no transaction is recorded.
    if (h.quantity < DUST_QUANTITY_THRESHOLD) {
      setDeletingTicker(null);
      setSaving(false);
      router.refresh();
      return;
    }
    const fd = new FormData();
    fd.set("portfolio_id", portfolioId);
    fd.set("event_type", "SELL");
    fd.set("event_date", new Date().toISOString().split("T")[0]);
    fd.set("ticker", h.ticker);
    fd.set("quantity", String(h.quantity));
    const avg = Number.isFinite(h.average_cost) ? h.average_cost : 0;
    const price = Math.max(avg, 0.0001);
    fd.set("price", String(price));
    fd.set("gross_amount", String(h.quantity * price));
    const r = await insertTransaction(fd);
    if (r.error) { setError(r.error); setSaving(false); } else { setDeletingTicker(null); router.refresh(); }
  }

  const nav = cash + totalMarketValue;
  const sorted = [...holdings].sort((a, b) => (b.market_value || 0) - (a.market_value || 0));

  return (
    <div className="space-y-5">
      {error && <div className="alert alert-error">{error}</div>}

      <div className="flex items-center justify-between gap-4 flex-wrap pb-4 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <button onClick={() => { setShowForm(!showForm); reset(); }} className="btn btn-primary"><Plus className="w-3.5 h-3.5" />New Transaction</button>
        {toolbarActions && <div className="flex items-center gap-2">{toolbarActions}</div>}
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">New Transaction</h3>
            <button type="button" onClick={() => setShowForm(false)} className="btn-icon btn-ghost"><X className="w-4 h-4" /></button>
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
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div><label className="text-xs text-neutral-500 block mb-1">Ticker</label><input value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())} className="input text-sm" placeholder="MU" /></div>
              <div><label className="text-xs text-neutral-500 block mb-1">Shares</label><input type="number" value={shares} onChange={e => setShares(e.target.value)} className="input text-sm" step="any" min="0" /></div>
              <div><label className="text-xs text-neutral-500 block mb-1">Price ($)</label><input type="number" value={price} onChange={e => setPrice(e.target.value)} className="input text-sm" step="0.01" min="0" /></div>
            </div>
          ) : (
            <div><label className="text-xs text-neutral-500 block mb-1">Amount ($)</label><input type="number" value={amount} onChange={e => setAmount(e.target.value)} className="input text-sm w-48" step="0.01" min="0" /></div>
          )}
          <button type="submit" disabled={saving} className="btn btn-primary">{saving ? "Saving..." : "Save Transaction"}</button>
        </form>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
        <div className="metric-card metric-primary"><p className="metric-label">Total Value</p><p className="metric-value">${nav.toLocaleString()}</p><p className="metric-sub">Cash + Holdings</p></div>
        <div className="metric-card"><p className="metric-label">Cash</p><p className="metric-value">${cash.toLocaleString()}</p></div>
        <div className="metric-card"><p className="metric-label">Holdings</p><p className="metric-value">${totalMarketValue.toLocaleString()}</p></div>
        <div className="metric-card"><p className="metric-label">Unrealized P/L</p><p className={`metric-value ${totalUnrealized >= 0 ? "metric-positive" : "metric-negative"}`}>{totalUnrealized >= 0 ? "+" : "−"}${Math.abs(totalUnrealized).toFixed(2)}</p></div>
        <div className="metric-card"><p className="metric-label">Realized P/L</p><p className={`metric-value ${totalRealized >= 0 ? "metric-positive" : "metric-negative"}`}>{totalRealized >= 0 ? "+" : "−"}${Math.abs(totalRealized).toFixed(2)}</p></div>
      </div>

      {sorted.length === 0 ? (
        <div className="card empty-state">No holdings yet. Add a Buy transaction to get started.</div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px]">
              <colgroup>
                <col style={{ width: "12%" }} />
                <col style={{ width: "12%" }} />
                <col style={{ width: "14%" }} />
                <col style={{ width: "14%" }} />
                <col style={{ width: "16%" }} />
                <col style={{ width: "14%" }} />
                <col style={{ width: "10%" }} />
                <col style={{ width: "8%" }} />
              </colgroup>
              <thead><tr><th className="table-header td-left">Ticker</th><th className="table-header td-right">Shares</th><th className="table-header td-right">Avg Cost</th><th className="table-header td-right">Price</th><th className="table-header td-right">Mkt Value</th><th className="table-header td-right">P/L</th><th className="table-header td-center">Top 30</th><th className="table-header td-right">Actions</th></tr></thead>
              <tbody>
                {sorted.map(h => (
                  <tr key={h.ticker} className="table-row">
                    <td className="table-cell-text td-left font-semibold text-neutral-200">{h.ticker}</td>
                    <td className="table-cell td-right">{h.quantity.toFixed(3)}</td>
                    <td className="table-cell td-right">${h.average_cost.toFixed(2)}</td>
                    <td className="table-cell td-right">{h.current_price ? `$${h.current_price.toFixed(2)}` : "—"}</td>
                    <td className="table-cell td-right">{h.market_value ? `$${h.market_value.toLocaleString()}` : "—"}</td>
                    <td className={`table-cell td-right ${(h.unrealized_pl||0) >= 0 ? "metric-positive" : "metric-negative"}`}>{h.unrealized_pl !== undefined ? `${h.unrealized_pl >= 0 ? "+" : "−"}$${Math.abs(h.unrealized_pl).toFixed(2)}` : "—"}</td>
                    <td className="table-cell td-center">{modelTickers.size > 0 ? <span className={modelTickers.has(h.ticker) ? "badge badge-green" : "badge badge-red"}>{modelTickers.has(h.ticker) ? "Yes" : "No"}</span> : "—"}</td>
                    <td className="table-cell td-right">
                      {deletingTicker === h.ticker ? (
                        <span className="flex items-center gap-1 justify-end"><button onClick={() => handleDelete(h)} disabled={saving} className="text-red-400 text-xs">Confirm</button><button onClick={() => setDeletingTicker(null)} className="text-neutral-400 text-xs">Cancel</button></span>
                      ) : (
                        <button onClick={() => setDeletingTicker(h.ticker)} className="btn-icon btn-ghost text-neutral-400 hover:text-red-400"><Trash2 className="w-3 h-3" /></button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      </div>
  );
}
