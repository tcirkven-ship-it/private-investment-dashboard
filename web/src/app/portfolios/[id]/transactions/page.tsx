"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Plus, Download } from "lucide-react";
import TransactionForm from "@/components/portfolios/TransactionForm";

interface Tx {
  id: string;
  event_type: string;
  event_date: string;
  ticker: string;
  quantity: number;
  price: number;
  gross_amount: number;
  commission: number;
}

const MOCK_TXS: Tx[] = [
  { id: "1", event_type: "DEPOSIT", event_date: "2026-01-02", ticker: "", quantity: 0, price: 0, gross_amount: 100000, commission: 0 },
  { id: "2", event_type: "BUY", event_date: "2026-01-05", ticker: "AAPL", quantity: 50, price: 185, gross_amount: 9250, commission: 5 },
  { id: "3", event_type: "BUY", event_date: "2026-01-05", ticker: "MSFT", quantity: 30, price: 420, gross_amount: 12600, commission: 5 },
  { id: "4", event_type: "DIVIDEND", event_date: "2026-02-15", ticker: "AAPL", quantity: 0, price: 0, gross_amount: 50, commission: 0 },
];

export default function TransactionsPage() {
  const { id } = useParams();
  const [showForm, setShowForm] = useState(false);
  const [txs] = useState<Tx[]>(MOCK_TXS);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <div>
            <h1 className="text-xl font-semibold">Transactions</h1>
            <p className="text-sm text-neutral-500">{txs.length} records</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary"><Download className="w-4 h-4 mr-1" />Export</button>
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
          <p className="text-neutral-500">No transactions yet. Add your first deposit or trade.</p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="table-header">Date</th>
                  <th className="table-header">Type</th>
                  <th className="table-header">Ticker</th>
                  <th className="table-header text-right">Qty</th>
                  <th className="table-header text-right">Price</th>
                  <th className="table-header text-right">Amount</th>
                  <th className="table-header text-right">Fee</th>
                </tr>
              </thead>
              <tbody>
                {txs.map((tx) => (
                  <tr key={tx.id} className="border-b border-neutral-800/50">
                    <td className="table-cell-text">{tx.event_date}</td>
                    <td className="table-cell-text">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                        tx.event_type === "BUY" ? "bg-green-500/10 text-green-400" :
                        tx.event_type === "SELL" ? "bg-red-500/10 text-red-400" :
                        tx.event_type === "DIVIDEND" ? "bg-blue-500/10 text-blue-400" :
                        "bg-neutral-800 text-neutral-300"
                      }`}>{tx.event_type}</span>
                    </td>
                    <td className="table-cell-text font-semibold">{tx.ticker || "—"}</td>
                    <td className="table-cell text-right">{tx.quantity || "—"}</td>
                    <td className="table-cell text-right">{tx.price ? `$${tx.price.toFixed(2)}` : "—"}</td>
                    <td className="table-cell text-right">${tx.gross_amount.toLocaleString()}</td>
                    <td className="table-cell text-right">{tx.commission ? `$${tx.commission.toFixed(2)}` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
