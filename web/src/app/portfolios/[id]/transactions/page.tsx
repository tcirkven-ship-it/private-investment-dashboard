"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Plus, Download } from "lucide-react";
import TransactionForm from "@/components/portfolios/TransactionForm";

export default function TransactionsPage() {
  const { id } = useParams();
  const [showForm, setShowForm] = useState(false);
  const [txs] = useState<any[]>([]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <div>
            <h1 className="text-xl font-semibold">Transactions</h1>
            <p className="text-sm text-neutral-500">Connected to Supabase database</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary" disabled><Download className="w-4 h-4 mr-1" />Export</button>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary">
            <Plus className="w-4 h-4 mr-1" />{showForm ? "Close" : "Add"}
          </button>
        </div>
      </div>

      {showForm && (
        <div className="card">
          <h2 className="text-sm font-semibold mb-4">New Transaction</h2>
          <TransactionForm portfolioId={id as string} onSaved={() => setShowForm(false)} />
        </div>
      )}

      {txs.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No transactions yet.</p>
          <p className="text-sm text-neutral-600 mt-2">Add your first deposit or trade to get started.</p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="table-header">Date</th>
                <th className="table-header">Type</th>
                <th className="table-header">Ticker</th>
                <th className="table-header text-right">Qty</th>
                <th className="table-header text-right">Price</th>
                <th className="table-header text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {txs.map((tx: any) => (
                <tr key={tx.id} className="border-b border-neutral-800/50">
                  <td className="table-cell-text">{tx.event_date}</td>
                  <td className="table-cell-text">{tx.event_type}</td>
                  <td className="table-cell-text font-semibold">{tx.ticker || "—"}</td>
                  <td className="table-cell text-right">{tx.quantity || "—"}</td>
                  <td className="table-cell text-right">{tx.price ? `$${tx.price}` : "—"}</td>
                  <td className="table-cell text-right">${tx.gross_amount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
