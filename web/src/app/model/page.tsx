"use client";

import { useState } from "react";
import Link from "next/link";
import { Info, TrendingUp, Shield, BarChart3 } from "lucide-react";

export default function ModelPage() {
  const [holdings] = useState<any[]>([]);
  const [modelInfo] = useState({ name: "M1 B2 Quality Veto", effective_date: "—", status: "No snapshot imported" });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Official Model</h1>
        <p className="text-sm text-neutral-500 mt-1">M1 B2 Quality Veto N30</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="metric-label">Model</p>
          <p className="text-sm font-semibold mt-1">M1 B2 Quality Veto</p>
        </div>
        <div className="card">
          <p className="metric-label">Effective Date</p>
          <p className="text-sm font-semibold mt-1">{modelInfo.effective_date}</p>
        </div>
        <div className="card">
          <p className="metric-label">Holdings</p>
          <p className="text-sm font-semibold mt-1">{holdings.length} selected</p>
        </div>
        <div className="card">
          <p className="metric-label">Status</p>
          <p className="text-sm font-semibold mt-1 text-yellow-400">{modelInfo.status}</p>
        </div>
      </div>

      {holdings.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No model snapshot imported.</p>
          <p className="text-sm text-neutral-600 mt-2">
            Use the{" "}
            <Link href="/admin/model-import" className="text-blue-400 hover:underline">Model Import</Link>{" "}
            page to import the official M1 B2 Quality Veto snapshot.
          </p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="table-header">#</th>
                <th className="table-header">Ticker</th>
                <th className="table-header text-right">Weight</th>
                <th className="table-header text-right">B2 Score</th>
                <th className="table-header text-right">Q %ile</th>
                <th className="table-header">Sector</th>
                <th className="table-header">Reason</th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((h: any) => (
                <tr key={h.ticker} className="border-b border-neutral-800/50">
                  <td className="table-cell text-neutral-500">{h.rank}</td>
                  <td className="table-cell-text font-semibold">{h.ticker}</td>
                  <td className="table-cell text-right">{h.target_weight}%</td>
                  <td className="table-cell text-right">{h.b2_score}</td>
                  <td className="table-cell text-right">{h.quality_percentile}</td>
                  <td className="table-cell-text text-sm">{h.sector}</td>
                  <td className="table-cell-text text-sm text-neutral-400">{h.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
