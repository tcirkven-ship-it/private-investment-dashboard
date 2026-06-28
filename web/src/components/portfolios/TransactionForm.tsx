"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { insertTransaction } from "@/lib/actions";

const TX_TYPES = [
  "DEPOSIT", "WITHDRAWAL", "BUY", "SELL", "DIVIDEND", "FEE", "TAX",
  "INTEREST", "SPLIT", "SYMBOL_CHANGE", "CORRECTION",
];

interface TransactionFormProps {
  portfolioId: string;
}

export default function TransactionForm({ portfolioId }: TransactionFormProps) {
  const router = useRouter();
  const [eventType, setEventType] = useState("BUY");
  const [ticker, setTicker] = useState("");
  const [eventDate, setEventDate] = useState(new Date().toISOString().split("T")[0]);
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [grossAmount, setGrossAmount] = useState("");
  const [commission, setCommission] = useState("0");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const needsTicker = ["BUY", "SELL", "DIVIDEND", "SPLIT", "SYMBOL_CHANGE"].includes(eventType);
  const needsQuantity = ["BUY", "SELL", "SPLIT", "CORRECTION"].includes(eventType);
  const needsPrice = ["BUY", "SELL", "CORRECTION"].includes(eventType);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess(false);

    const formData = new FormData();
    formData.set("portfolio_id", portfolioId);
    formData.set("event_type", eventType);
    formData.set("event_date", eventDate);
    const calcGross = ["BUY", "SELL"].includes(eventType)
      ? String((parseFloat(quantity) || 0) * (parseFloat(price) || 0))
      : grossAmount;
    formData.set("gross_amount", calcGross);
    formData.set("commission", commission);
    if (ticker) formData.set("ticker", ticker);
    if (quantity) formData.set("quantity", quantity);
    if (price) formData.set("price", price);

    const result = await insertTransaction(formData);

    if (result.error) {
      setError(result.error);
      setSaving(false);
    } else {
      setSaving(false);
      setSuccess(true);
      router.refresh();
      // Reset form
      setTicker("");
      setQuantity("");
      setPrice("");
      setGrossAmount("");
      setCommission("0");
      setTimeout(() => setSuccess(false), 3000);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <div className="text-sm text-red-400 bg-red-500/10 rounded px-3 py-2">{error}</div>}
      {success && <div className="text-sm text-green-400 bg-green-500/10 rounded px-3 py-2">Transaction recorded. Page refreshed.</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-medium text-neutral-500 uppercase tracking-wider block mb-1">Type</label>
          <select value={eventType} onChange={(e) => setEventType(e.target.value)} className="input" required>
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
            <input type="text" value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} className="input" placeholder="Ticker" />
          </div>
        )}
        {needsQuantity && (
          <div>
            <label className="text-xs font-medium text-neutral-500 uppercase tracking-wider block mb-1">Quantity</label>
            <input type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} className="input" step="any" min="0" />
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
      </div>
      <button type="submit" disabled={saving} className="btn-primary">
        {saving ? "Saving..." : success ? "Saved ✓" : "Record Transaction"}
      </button>
    </form>
  );
}
