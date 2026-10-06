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
    .limit(10000);

  if (!transactions || transactions.length === 0) {
    return (
      <div className="card">
        <h2 className="text-sm font-semibold mb-2 text-neutral-300">Recent Activity</h2>
        <p className="text-sm text-neutral-500">No transactions recorded yet.</p>
      </div>
    );
  }

  return (
    <div className="card p-0 overflow-hidden">
      <h2 className="text-sm font-semibold text-neutral-300 p-4 pb-0">Recent Activity</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px]">
          <colgroup>
            <col style={{ width: "18%" }} />
            <col style={{ width: "12%" }} />
            <col style={{ width: "14%" }} />
            <col style={{ width: "36%" }} />
            <col style={{ width: "20%" }} />
          </colgroup>
          <thead>
            <tr>
              <th className="table-header td-left">Date</th>
              <th className="table-header td-center">Type</th>
              <th className="table-header td-left">Ticker</th>
              <th className="table-header td-left">Details</th>
              <th className="table-header td-right">Actions</th>
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
