"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { upsertPrice } from "@/lib/actions";

export default function PriceEntryForm() {
  const router = useRouter();
  const [ticker, setTicker] = useState("");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [price, setPrice] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true); setMsg(null);
    const fd = new FormData();
    fd.set("ticker", ticker);
    fd.set("date", date);
    fd.set("close", price);
    const r = await upsertPrice(fd);
    setMsg(r.error || "Price updated");
    if (!r.error) { setTicker(""); setPrice(""); router.refresh(); }
    setSaving(false);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="text-xs text-neutral-500 block mb-1">Ticker</label>
          <input value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())} className="input text-sm" placeholder="MU" required />
        </div>
        <div>
          <label className="text-xs text-neutral-500 block mb-1">Date</label>
          <input type="date" value={date} onChange={e => setDate(e.target.value)} className="input text-sm" required />
        </div>
        <div>
          <label className="text-xs text-neutral-500 block mb-1">Close Price ($)</label>
          <input type="number" value={price} onChange={e => setPrice(e.target.value)} className="input text-sm" step="0.01" min="0" required />
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button type="submit" disabled={saving} className="btn btn-secondary text-xs">{saving ? "Saving..." : "Update Price"}</button>
        {msg && <span className={`text-xs ${msg.startsWith("Error") || msg.startsWith("Security") ? "text-red-400" : "text-green-400"}`}>{msg}</span>}
      </div>
    </form>
  );
}
