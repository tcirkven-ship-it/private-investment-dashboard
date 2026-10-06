"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { updateTransaction } from "@/lib/actions";
import { deleteTransaction } from "@/app/(app)/portfolios/[id]/transactions/actions";
import { Pencil, Trash2, Check, X } from "lucide-react";

export default function ActivityRow({ tx, portfolioId }: { tx: Record<string, unknown>; portfolioId: string }) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [editQty, setEditQty] = useState(tx.quantity != null ? String(Number(tx.quantity)) : "");
  const [editPrice, setEditPrice] = useState(tx.price != null ? String(Number(tx.price)) : "");
  const [deleting, setDeleting] = useState(false);
  const [saving, setSaving] = useState(false);
  const sec = tx.security as { ticker?: string } | null;
  const ticker = sec?.ticker || (Number(tx.quantity) ? "" : "—");
  const type = String(tx.event_type || "");
  const qty = tx.quantity != null ? Number(tx.quantity) : null;
  const price = tx.price != null ? Number(tx.price) : null;
  const gross = tx.gross_amount != null ? Number(tx.gross_amount) : 0;

  let details = "";
  if (type === "BUY" || type === "SELL") {
    details = qty != null && price != null ? `${qty.toFixed(3)} @ $${price.toFixed(2)}` : `$${gross.toFixed(2)}`;
  } else if (type === "OPENING_POSITION") {
    details = `${qty?.toFixed(3) ?? "?"} @ $${price?.toFixed(2) ?? "?"} (opening)`;
  } else {
    details = `$${gross.toFixed(2)}`;
  }

  const dateStr = new Date(String(tx.event_date || tx.created_at || "")).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });

  async function handleSave() {
    setSaving(true);
    const fd = new FormData();
    fd.set("quantity", editQty);
    fd.set("price", editPrice);
    fd.set("ticker", ticker);
    const r = await updateTransaction(String(tx.id), portfolioId, fd);
    if (!r.error) { setEditing(false); router.refresh(); }
    setSaving(false);
  }

  async function handleDelete() {
    setDeleting(true);
    const r = await deleteTransaction(String(tx.id), portfolioId);
    if (!r.error) router.refresh();
    setDeleting(false);
  }

  return (
    <tr className="table-row">
      <td className="table-cell td-left text-sm">{dateStr}</td>
      <td className="table-cell td-center text-sm">
        <span className={type === "BUY" || type === "OPENING_POSITION" ? "badge badge-green" : type === "SELL" ? "badge badge-red" : ""}>
          {type}
        </span>
      </td>
      <td className="table-cell-text td-left font-semibold text-neutral-200">{ticker || "—"}</td>
      <td className="table-cell-text td-left text-sm text-neutral-400">
        {editing ? (
          <span className="flex items-center gap-2">
            <input type="number" value={editQty} onChange={e => setEditQty(e.target.value)} className="input text-xs w-16" step="any" />
            <span>@ $</span>
            <input type="number" value={editPrice} onChange={e => setEditPrice(e.target.value)} className="input text-xs w-20" step="0.01" />
          </span>
        ) : details}
      </td>
      <td className="table-cell td-right text-sm">
        {editing ? (
          <span className="flex items-center gap-1 justify-end">
            <button onClick={handleSave} disabled={saving} className="btn-icon btn-ghost text-green-400"><Check className="w-3.5 h-3.5" /></button>
            <button onClick={() => setEditing(false)} className="btn-icon btn-ghost text-red-400"><X className="w-3.5 h-3.5" /></button>
          </span>
        ) : deleting ? (
          <span className="flex items-center gap-1 justify-end">
            <span className="text-xs text-red-400">Delete?</span>
            <button onClick={handleDelete} className="text-red-400 text-xs">Yes</button>
            <button onClick={() => setDeleting(false)} className="text-neutral-400 text-xs">No</button>
          </span>
        ) : (
          <span className="flex items-center gap-1 justify-end">
            <button onClick={() => setEditing(true)} className="btn-icon btn-ghost text-neutral-400 hover:text-blue-400"><Pencil className="w-3.5 h-3.5" /></button>
            <button onClick={() => setDeleting(true)} className="btn-icon btn-ghost text-neutral-400 hover:text-red-400"><Trash2 className="w-3.5 h-3.5" /></button>
          </span>
        )}
      </td>
    </tr>
  );
}
