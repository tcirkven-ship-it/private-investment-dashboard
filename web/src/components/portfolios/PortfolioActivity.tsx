import { createServerSupabase } from "@/lib/supabase";
import ActivityRow from "./ActivityRow";

export default async function PortfolioActivity({ portfolioId }: { portfolioId: string }) {
  const supabase = await createServerSupabase();
  const { data: transactions } = await supabase
    .from("transactions")
    .select("id, event_type, event_date, quantity, price, gross_amount, created_at, security:security_id(ticker)")
    .eq("portfolio_id", portfolioId)
    .is("corrected_by", null)
    .order("created_at", { ascending: false })
    .limit(20);

  if (!transactions || transactions.length === 0) {
    return (
      <div className="card">
        <h2 className="text-sm font-semibold mb-3">Recent Activity</h2>
        <p className="text-sm text-neutral-500">No activity yet.</p>
      </div>
    );
  }

  return (
    <div className="card p-0 overflow-hidden">
      <h2 className="text-sm font-semibold p-4 pb-2">Recent Activity</h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-neutral-800">
              <th className="table-header">Date</th>
              <th className="table-header">Type</th>
              <th className="table-header">Ticker</th>
              <th className="table-header">Details</th>
              <th className="table-header">Actions</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx: Record<string, unknown>) => (
              <ActivityRow key={String(tx.id)} tx={tx} portfolioId={portfolioId} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
