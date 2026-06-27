import { loadTransactions } from "@/lib/route-loaders";
import type { TransactionData } from "@/lib/adapters";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import TransactionForm from "@/components/portfolios/TransactionForm";

export default async function TransactionsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let transactions: TransactionData[] = [];
  let error: string | null = null;

  try {
    transactions = await loadTransactions(id as string);
  } catch (e: unknown) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Transactions</h1>
        </div>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <div>
            <h1 className="text-xl font-semibold">Transactions</h1>
            <p className="text-sm text-neutral-500">{transactions.length} records</p>
          </div>
        </div>
      </div>

      {transactions.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No transactions yet.</p>
          <p className="text-sm text-neutral-600 mt-2">Add your first deposit or trade below.</p>
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
                  <th className="table-header text-right">Amount</th>
                  <th className="table-header text-right">Fee</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
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
                    <td className="table-cell text-right">${tx.gross_amount.toLocaleString()}</td>
                    <td className="table-cell text-right">{tx.commission ? `$${tx.commission}` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="text-sm font-semibold mb-4">Add Transaction</h2>
        <TransactionForm portfolioId={id as string} />
      </div>
    </div>
  );
}
