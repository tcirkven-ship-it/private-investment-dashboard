"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function NewPortfolioPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [openingDate, setOpeningDate] = useState(new Date().toISOString().split("T")[0]);
  const [startingCash, setStartingCash] = useState("100000");
  const [notes, setNotes] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // In production, save to Supabase
    router.push("/portfolios");
  }

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/portfolios" className="btn-ghost p-1">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <h1 className="text-xl font-semibold">New Portfolio</h1>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-4">
        <div>
          <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-1.5">Name</label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="input" placeholder="Main Brokerage" required />
        </div>
        <div>
          <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-1.5">Opening Date</label>
          <input type="date" value={openingDate} onChange={(e) => setOpeningDate(e.target.value)} className="input" required />
        </div>
        <div>
          <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-1.5">Starting Cash ($)</label>
          <input type="number" value={startingCash} onChange={(e) => setStartingCash(e.target.value)} className="input" min="0" step="0.01" required />
        </div>
        <div>
          <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-1.5">Notes</label>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} className="input" rows={3} placeholder="Optional notes..." />
        </div>
        <button type="submit" className="btn-primary w-full">Create Portfolio</button>
      </form>
    </div>
  );
}
