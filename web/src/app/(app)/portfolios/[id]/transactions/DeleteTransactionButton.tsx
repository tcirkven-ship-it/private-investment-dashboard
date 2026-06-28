"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Trash2 } from "lucide-react";
import { deleteTransaction } from "./actions";

export default function DeleteTransactionButton({ txId, portfolioId }: { txId: string; portfolioId: string }) {
  const router = useRouter();
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    setDeleting(true);
    const result = await deleteTransaction(txId, portfolioId);
    if (result.error) {
      alert(result.error);
      setDeleting(false);
      setConfirming(false);
    } else {
      router.refresh();
    }
  }

  if (confirming) {
    return (
      <span className="flex items-center gap-1 text-xs">
        <span className="text-red-400">Delete?</span>
        <button onClick={handleDelete} disabled={deleting} className="text-red-400 hover:underline">
          {deleting ? "..." : "Yes"}
        </button>
        <button onClick={() => setConfirming(false)} className="text-neutral-400 hover:underline">No</button>
      </span>
    );
  }

  return (
    <button onClick={() => setConfirming(true)} className="text-neutral-500 hover:text-red-400" title="Delete transaction">
      <Trash2 className="w-3.5 h-3.5" />
    </button>
  );
}
