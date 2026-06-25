"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Download, Check } from "lucide-react";

interface RebalanceLine {
  ticker: string;
  current_qty: number;
  current_weight: number;
  target_weight: number;
  action: string;
  est_cost: number;
  owner_decision: string;
}

const MOCK_LINES: RebalanceLine[] = [
  { ticker: "AAPL", current_qty: 50, current_weight: 4.2, target_weight: 3.33, action: "Reduce", est_cost: 5, owner_decision: "Pending" },
  { ticker: "MSFT", current_qty: 30, current_weight: 5.8, target_weight: 3.33, action: "Reduce", est_cost: 5, owner_decision: "Pending" },
  { ticker: "GOOGL", current_qty: 20, current_weight: 1.6, target_weight: 3.33, action: "Increase", est_cost: 5, owner_decision: "Pending" },
  { ticker: "MU", current_qty: 0, current_weight: 0, target_weight: 3.33, action: "Add", est_cost: 10, owner_decision: "Pending" },
  { ticker: "NVDA", current_qty: 10, current_weight: 3.1, target_weight: 3.33, action: "Keep", est_cost: 0, owner_decision: "Pending" },
];

export default function RebalancePage() {
  const { id } = useParams();
  const [lines, setLines] = useState<RebalanceLine[]>(MOCK_LINES);
  const [completed, setCompleted] = useState(false);

  function setDecision(ticker: string, decision: string) {
    setLines(lines.map(l => l.ticker === ticker ? { ...l, owner_decision: decision } : l));
  }

  const csvContent = [
    "Ticker,Current Qty,Current Weight,Target Weight,Action,Est Cost,Owner Decision",
    ...lines.map(l => `${l.ticker},${l.current_qty},${l.current_weight}%,${l.target_weight}%,${l.action},$${l.est_cost},${l.owner_decision}`),
  ].join("\n");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <div>
            <h1 className="text-xl font-semibold">Quarterly Review</h1>
            <p className="text-sm text-neutral-500">Official model: 2026-09-30 vs portfolio Main Brokerage</p>
          </div>
        </div>
        <div className="flex gap-2">
          <a href={`data:text/csv;charset=utf-8,${encodeURIComponent(csvContent)}`}
             download="rebalance.csv" className="btn-secondary"><Download className="w-4 h-4 mr-1" />CSV</a>
          <button onClick={() => setCompleted(true)} className="btn-primary">
            <Check className="w-4 h-4 mr-1" />Complete Review
          </button>
        </div>
      </div>

      {completed && (
        <div className="card border-green-500/30 bg-green-500/5">
          <p className="text-sm text-green-400">Review completed. Trades recorded as pending execution.</p>
        </div>
      )}

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-neutral-800">
              <th className="table-header">Ticker</th>
              <th className="table-header text-right">Current</th>
              <th className="table-header text-right">Target</th>
              <th className="table-header">Action</th>
              <th className="table-header">Decision</th>
              <th className="table-header text-right">Est. Cost</th>
            </tr>
          </thead>
          <tbody>
            {lines.map((l) => (
              <tr key={l.ticker} className="border-b border-neutral-800/50">
                <td className="table-cell-text font-semibold">{l.ticker}</td>
                <td className="table-cell text-right">{l.current_weight.toFixed(1)}%</td>
                <td className="table-cell text-right">{l.target_weight.toFixed(2)}%</td>
                <td className="table-cell-text">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                    l.action === "Add" ? "bg-green-500/10 text-green-400" :
                    l.action === "Reduce" ? "bg-red-500/10 text-red-400" :
                    l.action === "Increase" ? "bg-blue-500/10 text-blue-400" :
                    "bg-neutral-800 text-neutral-300"
                  }`}>{l.action}</span>
                </td>
                <td className="table-cell-text">
                  <select value={l.owner_decision} onChange={(e) => setDecision(l.ticker, e.target.value)}
                    className="text-xs bg-neutral-900 border border-neutral-700 rounded px-2 py-1">
                    <option>Pending</option>
                    <option>Follow</option>
                    <option>Partial</option>
                    <option>Skip</option>
                    <option>Defer</option>
                  </select>
                </td>
                <td className="table-cell text-right">${l.est_cost}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2 className="text-sm font-semibold mb-3">Summary</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><span className="text-neutral-500">Model overlap:</span> <span className="font-semibold">63.3%</span></div>
          <div><span className="text-neutral-500">Holdings to add:</span> <span className="font-semibold">4</span></div>
          <div><span className="text-neutral-500">Holdings to remove:</span> <span className="font-semibold">2</span></div>
          <div><span className="text-neutral-500">Est. total cost:</span> <span className="font-semibold">$45</span></div>
        </div>
      </div>
    </div>
  );
}
