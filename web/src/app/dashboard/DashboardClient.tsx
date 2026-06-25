"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase";
import { TrendingUp, TrendingDown, DollarSign, PiggyBank, RefreshCw } from "lucide-react";

interface DashboardData {
  totalValue: number;
  cash: number;
  dailyChange: number;
  dailyChangePct: number;
  mtdReturn: number;
  qtdReturn: number;
  ytdReturn: number;
  oneYearReturn: number;
  sinceInceptionReturn: number;
  modelAlignment: number;
  modelDate: string;
  nextReview: string;
  spyYtd: number;
  qqqYtd: number;
  lastUpdated: string;
}

export default function DashboardClient() {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    // Load from Supabase or initialize with empty state
    setData({
      totalValue: 100000,
      cash: 5000,
      dailyChange: 1250.45,
      dailyChangePct: 1.27,
      mtdReturn: 3.42,
      qtdReturn: 5.18,
      ytdReturn: 12.76,
      oneYearReturn: 18.34,
      sinceInceptionReturn: 24.51,
      modelAlignment: 73.3,
      modelDate: "2026-06-23",
      nextReview: "2026-09-30",
      spyYtd: 10.24,
      qqqYtd: 14.87,
      lastUpdated: "2026-06-24 14:30 UTC",
    });
  }, []);

  if (!data) return <div className="text-neutral-500 text-sm p-8">Loading dashboard...</div>;

  const MetricCard = ({ label, value, change, isCurrency }: {
    label: string; value: string; change?: string; isCurrency?: boolean;
  }) => (
    <div className="card">
      <p className="metric-label">{label}</p>
      <p className="metric-value mt-1">{value}</p>
      {change && (
        <p className={change.startsWith("+") ? "metric-change-positive mt-1" : "metric-change-negative mt-1"}>
          {change}
        </p>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-neutral-500 mt-1">Last updated {data.lastUpdated}</p>
        </div>
        <button className="btn-ghost text-sm flex items-center gap-2">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Summary row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard label="Total Value" value={`$${data.totalValue.toLocaleString()}`} change={`${data.dailyChangePct >= 0 ? "+" : ""}${data.dailyChangePct.toFixed(2)}% today`} />
        <MetricCard label="Cash" value={`$${data.cash.toLocaleString()}`} />
        <MetricCard label="Model Alignment" value={`${data.modelAlignment.toFixed(1)}%`} />
        <MetricCard label="Next Review" value={data.nextReview} />
      </div>

      {/* Performance */}
      <div className="card">
        <h2 className="text-sm font-semibold mb-4">Performance</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "MTD", value: data.mtdReturn },
            { label: "QTD", value: data.qtdReturn },
            { label: "YTD", value: data.ytdReturn },
            { label: "1 Year", value: data.oneYearReturn },
            { label: "Since Inception", value: data.sinceInceptionReturn },
          ].map((item) => (
            <div key={item.label}>
              <p className="metric-label">{item.label}</p>
              <p className={`text-lg font-mono font-semibold tabular-nums mt-0.5 ${item.value >= 0 ? "text-green-400" : "text-red-400"}`}>
                {item.value >= 0 ? "+" : ""}{item.value.toFixed(2)}%
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Benchmarks */}
      <div className="card">
        <h2 className="text-sm font-semibold mb-4">Benchmark Comparison (YTD)</h2>
        <div className="grid grid-cols-3 gap-6">
          <div>
            <p className="metric-label">Portfolio</p>
            <p className="text-lg font-mono font-semibold tabular-nums text-green-400">+{data.ytdReturn.toFixed(2)}%</p>
          </div>
          <div>
            <p className="metric-label">SPY</p>
            <p className="text-lg font-mono font-semibold tabular-nums text-green-400">+{data.spyYtd.toFixed(2)}%</p>
          </div>
          <div>
            <p className="metric-label">QQQ</p>
            <p className="text-lg font-mono font-semibold tabular-nums text-green-400">+{data.qqqYtd.toFixed(2)}%</p>
          </div>
        </div>
      </div>

      {/* Model info */}
      <div className="card">
        <h2 className="text-sm font-semibold mb-2">Official Model</h2>
        <p className="text-sm text-neutral-400">
          Latest model: {data.modelDate} — {data.modelAlignment.toFixed(0)}% aligned with your portfolio
        </p>
        <p className="text-sm text-neutral-500 mt-1">Next quarterly review: {data.nextReview}</p>
      </div>
    </div>
  );
}
