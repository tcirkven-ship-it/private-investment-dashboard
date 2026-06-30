import { createServerSupabase } from "@/lib/supabase";

export default async function PortfolioActivity({ portfolioId }: { portfolioId: string }) {
  const supabase = await createServerSupabase();

  const { data: transactions } = await supabase
    .from("transactions")
    .select(`
      id, event_type, event_date, quantity, price, gross_amount, commission, notes, created_at,
      security:security_id(ticker)
    `)
    .eq("portfolio_id", portfolioId)
    .is("corrected_by", null)
    .order("created_at", { ascending: false })
    .limit(20);

  if (!transactions || transactions.length === 0) {
    return (
      <div className="card">
        <h2 className="text-sm font-semibold mb-3">Recent Activity</h2>
        <p className="text-sm text-neutral-500">No transactions yet.</p>
      </div>
    );
  }

  const formatDateTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  };

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
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx: Record<string, unknown>) => {
              const sec = tx.security as { ticker?: string } | null;
              const ticker = sec?.ticker || "—";
              const type = String(tx.event_type || "");
              const qty = tx.quantity != null ? Number(tx.quantity) : null;
              const price = tx.price != null ? Number(tx.price) : null;
              const gross = tx.gross_amount != null ? Number(tx.gross_amount) : 0;

              let details = "";
              if (type === "BUY" || type === "SELL") {
                details = qty != null && price != null
                  ? `${qty.toFixed(3)} @ $${price.toFixed(2)}`
                  : `$${gross.toFixed(2)}`;
              } else if (type === "DEPOSIT" || type === "WITHDRAWAL") {
                details = `$${gross.toFixed(2)}`;
              } else if (type === "DIVIDEND") {
                details = `$${gross.toFixed(2)}`;
              } else {
                details = `$${gross.toFixed(2)}`;
              }

              return (
                <tr key={String(tx.id)} className="border-b border-neutral-800/50">
                  <td className="table-cell text-sm">{formatDateTime(String(tx.event_date || tx.created_at || ""))}</td>
                  <td className="table-cell text-sm">
                    <span className={type === "BUY" ? "text-green-400" : type === "SELL" ? "text-red-400" : "text-neutral-200"}>
                      {type}
                    </span>
                  </td>
                  <td className="table-cell-text font-semibold text-sm">{ticker}</td>
                  <td className="table-cell-text text-sm text-neutral-400">{details}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
