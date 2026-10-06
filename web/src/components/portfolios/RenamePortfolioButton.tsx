"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Pencil, Check, X } from "lucide-react";
import { renamePortfolio } from "@/lib/actions";

export default function RenamePortfolioButton({ portfolioId, currentName }: { portfolioId: string; currentName: string }) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(currentName);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing && inputRef.current) inputRef.current.focus();
  }, [editing]);

  async function handleSave() {
    const trimmed = name.trim();
    if (!trimmed) { setError("Name cannot be empty."); return; }
    if (trimmed.length > 80) { setError("Name too long (max 80 characters)."); return; }
    setSaving(true);
    setError("");
    const result = await renamePortfolio(portfolioId, trimmed);
    if (result.error) { setError(result.error); setSaving(false); }
    else { setEditing(false); setSaving(false); router.refresh(); }
  }

  if (editing) {
    return (
      <span className="inline-flex items-center gap-2">
        <input
          ref={inputRef}
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleSave(); if (e.key === "Escape") setEditing(false); }}
          className="input text-sm w-48"
          maxLength={80}
          disabled={saving}
        />
        <button onClick={handleSave} disabled={saving} className="btn-icon btn-ghost text-green-400"><Check className="w-4 h-4" /></button>
        <button onClick={() => setEditing(false)} className="btn-icon btn-ghost text-neutral-400"><X className="w-4 h-4" /></button>
        {error && <span className="text-xs text-red-400">{error}</span>}
      </span>
    );
  }

  return (
    <button onClick={() => { setName(currentName); setEditing(true); }} className="btn-icon btn-ghost text-neutral-400 hover:text-neutral-200" title="Rename portfolio">
      <Pencil className="w-3.5 h-3.5" />
    </button>
  );
}
