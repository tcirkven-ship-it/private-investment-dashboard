import { createServerSupabase } from "@/lib/supabase";
import Link from "next/link";
import { ArrowLeft, Download } from "lucide-react";
import TransactionForm from "@/components/portfolios/TransactionForm";

export default async function TransactionsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createServerSupabase();

  const { data: transactions, error } = await supabase
    .from("transactions")
    .select("id, event_type, event_date, quantity, price, gross_amount, commission, created_at, security:security_id(ticker)")
    .eq("portfolio_id", id)
    .is("corrected_by", null)
    .order("event_date", { ascending: false });

  const csvContent = [
    "Date,Type,Ticker,Qty,Price,Amount",
    ...(transactions || []).map((t: any) =>
      `${t.event_date},${t.event_type},${t.security?.ticker || ""},${t.quantity || 0},${t.price || 0},${t.gross_amount}`
    ),
  ].join("\n");

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Transactions</h1>
        </div>
        <div className="card border-red-500/30 bg-red-500/5">
          <p className="text-sm text-red-400">Error loading transactions: {error.message}</p>
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
            <p className="text-sm text-neutral-500">{transactions?.length || 0} records</p>
          </div>
        </div>
        <a href={`data:text/csv;charset=utf-8,${encodeURIComponent(csvContent)}`}
           download="transactions.csv" className="btn-secondary"><Download className="w-4 h-4 mr-1" />CSV</a>
      </div>

      {(!transactions || transactions.length === 0) ? (
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
                {(transactions || []).map((tx: any) => (
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
                    <td className="table-cell-text font-semibold">{tx.security?.ticker || "—"}</td>
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
