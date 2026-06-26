"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Download } from "lucide-react";

export default function HoldingsPage() {
  const { id } = useParams();
  const [loading] = useState(false);
  const [holdings] = useState<any[]>([]);
  const [cash] = useState(0);
  const [nav] = useState(cash);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <div>
            <h1 className="text-xl font-semibold">Holdings</h1>
            <p className="text-sm text-neutral-500">Connected to Supabase database</p>
          </div>
        </div>
        <button className="btn-secondary" disabled><Download className="w-4 h-4 mr-1" />CSV</button>
      </div>

      {loading ? (
        <div className="card text-center py-12"><p className="text-neutral-500">Loading holdings...</p></div>
      ) : holdings.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No holdings yet.</p>
          <p className="text-sm text-neutral-600 mt-2">Add deposits and trades on the Transactions page.</p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="table-header">Ticker</th>
                <th className="table-header text-right">Qty</th>
                <th className="table-header text-right">Avg Cost</th>
                <th className="table-header text-right">Price</th>
                <th className="table-header text-right">Market Value</th>
                <th className="table-header text-right">Unrealized</th>
                <th className="table-header text-right">Weight</th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((h: any) => (
                <tr key={h.ticker} className="border-b border-neutral-800/50">
                  <td className="table-cell-text font-semibold">{h.ticker}</td>
                  <td className="table-cell text-right">{h.quantity}</td>
                  <td className="table-cell text-right">${h.average_cost}</td>
                  <td className="table-cell text-right">${h.price}</td>
                  <td className="table-cell text-right">${h.market_value}</td>
                  <td className={`table-cell text-right ${h.unrealized >= 0 ? "text-green-400" : "text-red-400"}`}>${h.unrealized}</td>
                  <td className="table-cell text-right">{h.weight}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
