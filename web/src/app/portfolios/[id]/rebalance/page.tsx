"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Download, Check } from "lucide-react";

export default function RebalancePage() {
  const { id } = useParams();
  const [completed] = useState(false);
  const [comparisons] = useState<any[]>([]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <div>
            <h1 className="text-xl font-semibold">Quarterly Review</h1>
            <p className="text-sm text-neutral-500">Compare portfolio with official model</p>
          </div>
        </div>
        <button className="btn-secondary" disabled><Download className="w-4 h-4 mr-1" />CSV</button>
      </div>

      {completed && (
        <div className="card border-green-500/30 bg-green-500/5">
          <p className="text-sm text-green-400 flex items-center gap-2"><Check className="w-4 h-4" />Review completed.</p>
        </div>
      )}

      {comparisons.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No model comparison available.</p>
          <p className="text-sm text-neutral-600 mt-2">Import and publish a model snapshot, then return here for alignment analysis.</p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="table-header">Ticker</th>
                <th className="table-header text-right">Current</th>
                <th className="table-header text-right">Target</th>
                <th className="table-header">Action</th>
                <th className="table-header">Decision</th>
              </tr>
            </thead>
            <tbody>
              {comparisons.map((c: any) => (
                <tr key={c.ticker} className="border-b border-neutral-800/50">
                  <td className="table-cell-text font-semibold">{c.ticker}</td>
                  <td className="table-cell text-right">{c.current_weight}%</td>
                  <td className="table-cell text-right">{c.target_weight}%</td>
                  <td className="table-cell-text">{c.action}</td>
                  <td className="table-cell-text">{c.decision || "Pending"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
