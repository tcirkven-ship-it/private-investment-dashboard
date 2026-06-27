import { createServerSupabase } from "@/lib/supabase";
import type { TransactionRow } from "@/lib/types";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import TransactionForm from "@/components/portfolios/TransactionForm";

interface DbTransaction {
  id: string;
  event_type: string;
  event_date: string;
  quantity: number | null;
  price: number | null;
  gross_amount: number;
  commission: number | null;
  created_at: string;
  security: { ticker: string }[] | { ticker: string } | null;
}

export default async function TransactionsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createServerSupabase();

  const { data: dbRows, error } = await supabase
    .from("transactions")
    .select("id, event_type, event_date, quantity, price, gross_amount, commission, created_at, security:security_id(ticker)")
    .eq("portfolio_id", id as string)
    .is("corrected_by", null)
    .order("event_date", { ascending: false });

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

  const transactions: TransactionRow[] = (dbRows || []).map((t: Record<string, any>) => {
    const secData = Array.isArray(t.security) ? t.security[0] : t.security;
    const row: TransactionRow = {
      id: t.id,
      event_type: t.event_type,
      event_date: t.event_date,
      quantity: t.quantity,
      price: t.price,
      gross_amount: t.gross_amount,
      commission: t.commission,
      tax_amount: null,
      notes: null,
      created_at: t.created_at,
      security_ticker: secData?.ticker || null,
    };
    return row;
  });

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
                    <td className="table-cell-text font-semibold">{tx.security_ticker || "—"}</td>
                    <td className="table-cell text-right">{tx.quantity ?? "—"}</td>
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
