"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { createPortfolio } from "@/lib/actions";

export default function NewPortfolioPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");

    const formData = new FormData();
    formData.set("name", name);
    formData.set("currency", currency);

    const result = await createPortfolio(formData);
    if (result.error) {
      setError(result.error);
      setSaving(false);
    } else {
      router.push("/portfolios");
    }
  }

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/portfolios" className="btn-ghost p-1">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <h1 className="text-xl font-semibold">Create Portfolio</h1>
      </div>

      {error && <div className="text-sm text-red-400 bg-red-500/10 rounded px-3 py-2">{error}</div>}

      <form onSubmit={handleSubmit} className="card space-y-4">
        <div>
          <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-1.5">Portfolio Name</label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="input" placeholder="Main Portfolio" required />
        </div>
        <div>
          <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-1.5">Base Currency</label>
          <select value={currency} onChange={(e) => setCurrency(e.target.value)} className="input">
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
            <option value="GBP">GBP</option>
          </select>
        </div>
        <button type="submit" disabled={saving} className="btn-primary w-full">{saving ? "Creating..." : "Create Portfolio"}</button>
      </form>
    </div>
  );
}
