"use client";

import { useState } from "react";

const TX_TYPES = [
  "DEPOSIT", "WITHDRAWAL", "BUY", "SELL", "DIVIDEND", "FEE", "TAX",
  "INTEREST", "SPLIT", "SYMBOL_CHANGE", "CORRECTION",
];

interface TransactionFormProps {
  portfolioId: string;
  onSaved?: () => void;
}

export default function TransactionForm({ portfolioId, onSaved }: TransactionFormProps) {
  const [eventType, setEventType] = useState("BUY");
  const [ticker, setTicker] = useState("");
  const [eventDate, setEventDate] = useState(new Date().toISOString().split("T")[0]);
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [grossAmount, setGrossAmount] = useState("");
  const [commission, setCommission] = useState("0");
  const [tax, setTax] = useState("0");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);

    const payload = {
      portfolio_id: portfolioId,
      event_type: eventType,
      event_date: eventDate,
      ticker: ticker || null,
      quantity: parseFloat(quantity) || 0,
      price: parseFloat(price) || 0,
      gross_amount: parseFloat(grossAmount) || 0,
      commission: parseFloat(commission) || 0,
      tax: parseFloat(tax) || 0,
      notes: notes || null,
    };

    // In production, save to Supabase
    console.log("Saving transaction:", payload);
    await new Promise((r) => setTimeout(r, 500));

    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
    if (onSaved) onSaved();
  }

  const needsTicker = ["BUY", "SELL", "DIVIDEND", "SPLIT", "SYMBOL_CHANGE"].includes(eventType);
  const needsQuantity = ["BUY", "SELL", "SPLIT", "CORRECTION"].includes(eventType);
  const needsPrice = ["BUY", "SELL", "CORRECTION"].includes(eventType);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-medium text-neutral-500 uppercase tracking-wider block mb-1">Type</label>
          <select value={eventType} onChange={(e) => setEventType(e.target.value)} className="input">
            {TX_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs font-medium text-neutral-500 uppercase tracking-wider block mb-1">Date</label>
          <input type="date" value={eventDate} onChange={(e) => setEventDate(e.target.value)} className="input" required />
        </div>
        {needsTicker && (
          <div>
            <label className="text-xs font-medium text-neutral-500 uppercase tracking-wider block mb-1">Ticker</label>
            <input type="text" value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} className="input" placeholder="AAPL" required />
          </div>
        )}
        {needsQuantity && (
          <div>
            <label className="text-xs font-medium text-neutral-500 uppercase tracking-wider block mb-1">Quantity</label>
            <input type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} className="input" step="any" min="0" required />
          </div>
        )}
        {needsPrice && (
          <div>
            <label className="text-xs font-medium text-neutral-500 uppercase tracking-wider block mb-1">Price ($)</label>
            <input type="number" value={price} onChange={(e) => setPrice(e.target.value)} className="input" step="0.0001" min="0" />
          </div>
        )}
        <div>
          <label className="text-xs font-medium text-neutral-500 uppercase tracking-wider block mb-1">Gross Amount ($)</label>
          <input type="number" value={grossAmount} onChange={(e) => setGrossAmount(e.target.value)} className="input" step="0.01" required />
        </div>
        <div>
          <label className="text-xs font-medium text-neutral-500 uppercase tracking-wider block mb-1">Commission ($)</label>
          <input type="number" value={commission} onChange={(e) => setCommission(e.target.value)} className="input" step="0.01" min="0" />
        </div>
        <div>
          <label className="text-xs font-medium text-neutral-500 uppercase tracking-wider block mb-1">Tax ($)</label>
          <input type="number" value={tax} onChange={(e) => setTax(e.target.value)} className="input" step="0.01" min="0" />
        </div>
      </div>
      <div>
        <label className="text-xs font-medium text-neutral-500 uppercase tracking-wider block mb-1">Notes</label>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} className="input" rows={2} placeholder="Optional notes..." />
      </div>
      <button type="submit" disabled={saving} className="btn-primary">
        {saving ? "Saving..." : saved ? "Saved ✓" : "Record Transaction"}
      </button>
    </form>
  );
}
