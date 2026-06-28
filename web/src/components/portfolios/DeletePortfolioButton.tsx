"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { deletePortfolio } from "@/lib/actions";
import { Trash2 } from "lucide-react";

interface DeletePortfolioButtonProps {
  portfolioId: string;
  portfolioName: string;
}

export default function DeletePortfolioButton({ portfolioId, portfolioName }: DeletePortfolioButtonProps) {
  const router = useRouter();
  const [showConfirm, setShowConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  async function handleDelete() {
    setDeleting(true);
    setError("");

    const result = await deletePortfolio(portfolioId);
    if (result.error) {
      setError(result.error);
      setDeleting(false);
    } else {
      router.push("/portfolios");
    }
  }

  return (
    <>
      <button onClick={() => setShowConfirm(true)} className="btn-ghost text-red-400 hover:text-red-300 p-1" title="Delete portfolio">
        <Trash2 className="w-4 h-4" />
      </button>

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="card max-w-sm w-full mx-4 space-y-4">
            <h3 className="text-lg font-semibold">Delete Portfolio</h3>
            <p className="text-sm text-neutral-300">
              Are you sure you want to delete <strong>{portfolioName}</strong>? This action cannot be undone.
            </p>
            {error && <div className="text-sm text-red-400 bg-red-500/10 rounded px-3 py-2">{error}</div>}
            <div className="flex gap-3 justify-end">
              <button onClick={() => { setShowConfirm(false); setError(""); }} disabled={deleting} className="btn-ghost">
                Cancel
              </button>
              <button onClick={handleDelete} disabled={deleting} className="btn-danger">
                {deleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
