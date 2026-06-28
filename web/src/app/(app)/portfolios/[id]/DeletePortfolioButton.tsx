"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Trash2 } from "lucide-react";
import { deletePortfolio } from "@/lib/actions";

export default function DeletePortfolioButton({ portfolioId }: { portfolioId: string }) {
  const router = useRouter();
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    setDeleting(true);
    const result = await deletePortfolio(portfolioId);
    if (result.error) {
      alert(result.error);
      setDeleting(false);
    } else {
      router.push("/portfolios");
    }
  }

  if (confirming) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-xs text-red-400">Delete this portfolio?</span>
        <button onClick={handleDelete} disabled={deleting} className="btn-ghost text-xs text-red-400 px-2 py-1">
          {deleting ? "Deleting..." : "Confirm"}
        </button>
        <button onClick={() => setConfirming(false)} className="btn-ghost text-xs px-2 py-1">Cancel</button>
      </div>
    );
  }

  return (
    <button onClick={() => setConfirming(true)} className="btn-ghost text-xs text-red-400 flex items-center gap-1">
      <Trash2 className="w-3 h-3" /> Delete
    </button>
  );
}
