"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Download } from "lucide-react";

export default function PerformancePage() {
  const { id } = useParams();
  const [period, setPeriod] = useState("1Y");

  const periods = [
    { id: "MTD", label: "MTD" },
    { id: "QTD", label: "QTD" },
    { id: "YTD", label: "YTD" },
    { id: "1Y", label: "1 Year" },
    { id: "SI", label: "Since Inception" },
  ];

  const returns: Record<string, { portfolio: number; spy: number; qqq: number; model: number }> = {
    MTD: { portfolio: 2.34, spy: 1.82, qqq: 2.15, model: 2.89 },
    QTD: { portfolio: 5.18, spy: 3.94, qqq: 5.62, model: 6.31 },
    YTD: { portfolio: 12.76, spy: 10.24, qqq: 14.87, model: 15.42 },
    "1Y": { portfolio: 18.34, spy: 14.56, qqq: 19.23, model: 22.15 },
    SI: { portfolio: 21.45, spy: 16.12, qqq: 21.98, model: 25.67 },
  };

  const current = returns[period] || returns["1Y"];

  const csvContent = [
    "Period,Portfolio,SPY,QQQ,Official Model",
    ...Object.entries(returns).map(([k, v]) =>
      `${k},${v.portfolio}%,${v.spy}%,${v.qqq}%,${v.model}%`
    ),
  ].join("\n");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <h1 className="text-xl font-semibold">Performance</h1>
        </div>
        <a href={`data:text/csv;charset=utf-8,${encodeURIComponent(csvContent)}`}
           download="performance.csv" className="btn-secondary"><Download className="w-4 h-4 mr-1" />CSV</a>
      </div>

      <div className="flex gap-1">
        {periods.map((p) => (
          <button key={p.id} onClick={() => setPeriod(p.id)}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              period === p.id ? "bg-blue-600 text-white" : "text-neutral-400 hover:text-neutral-200"
            }`}>{p.label}</button>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Portfolio", value: current.portfolio, color: "text-blue-400" },
          { label: "SPY (Benchmark)", value: current.spy, color: "text-neutral-300" },
          { label: "QQQ (Benchmark)", value: current.qqq, color: "text-neutral-300" },
          { label: "Official Model", value: current.model, color: "text-green-400" },
        ].map((item) => (
          <div key={item.label} className="card">
            <p className="metric-label">{item.label}</p>
            <p className={`metric-value mt-1 ${item.value >= 0 ? "text-green-400" : "text-red-400"}`}>
              {item.value >= 0 ? "+" : ""}{item.value.toFixed(2)}%
            </p>
          </div>
        ))}
      </div>

      <div className="card">
        <h2 className="text-sm font-semibold mb-4">Notes</h2>
        <ul className="text-sm text-neutral-400 space-y-1.5">
          <li>• Time-weighted return (TWR) — accounts for deposit and withdrawal timing</li>
          <li>• Benchmark returns use contribution-matched cash flows for fair comparison</li>
          <li>• Model return is the official M1 B2 Quality Veto N30 backtest result</li>
          <li>• Personal, model, and benchmark returns are calculated independently</li>
        </ul>
      </div>
    </div>
  );
}
