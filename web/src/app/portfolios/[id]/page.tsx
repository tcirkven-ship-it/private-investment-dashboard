"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, TrendingUp, Wallet, Receipt, BarChart3, RefreshCw } from "lucide-react";

export default function PortfolioDetailPage() {
  const { id } = useParams();
  const [activeTab] = useState("overview");

  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "holdings", label: "Holdings", href: `/portfolios/${id}/holdings` },
    { id: "transactions", label: "Transactions", href: `/portfolios/${id}/transactions` },
    { id: "performance", label: "Performance", href: `/portfolios/${id}/performance` },
    { id: "rebalance", label: "Quarterly Review", href: `/portfolios/${id}/rebalance` },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/portfolios" className="btn-ghost p-1">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-2xl font-semibold">Main Brokerage</h1>
          <p className="text-sm text-neutral-500 mt-0.5">Opened January 1, 2025</p>
        </div>
      </div>

      <div className="flex gap-1 border-b border-neutral-800 pb-0.5">
        {tabs.map((tab) => (
          tab.href ? (
            <Link key={tab.id} href={tab.href} className="px-4 py-2 text-sm font-medium text-neutral-400 hover:text-neutral-100 border-b-2 border-transparent hover:border-neutral-500 transition-colors">
              {tab.label}
            </Link>
          ) : (
            <button key={tab.id} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id ? "text-blue-400 border-blue-500" : "text-neutral-400 border-transparent hover:text-neutral-100"
            }`}>{tab.label}</button>
          )
        ))}
      </div>

      {activeTab === "overview" && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card">
              <p className="metric-label">Total Value</p>
              <p className="metric-value mt-1">$142,350</p>
              <p className="metric-change-positive mt-1">+1.27% today</p>
            </div>
            <div className="card">
              <p className="metric-label">Cash</p>
              <p className="metric-value mt-1">$8,420</p>
            </div>
            <div className="card">
              <p className="metric-label">YTD Return</p>
              <p className="metric-value mt-1 text-green-400">+12.76%</p>
            </div>
            <div className="card">
              <p className="metric-label">Model Alignment</p>
              <p className="metric-value mt-1">73.3%</p>
            </div>
          </div>

          <div className="card">
            <h2 className="text-sm font-semibold mb-4">Performance Summary</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[
                { label: "MTD", value: "+3.42%" },
                { label: "QTD", value: "+5.18%" },
                { label: "YTD", value: "+12.76%" },
                { label: "1 Year", value: "+18.34%" },
                { label: "Since Inception", value: "+24.51%" },
              ].map((item) => (
                <div key={item.label}>
                  <p className="metric-label">{item.label}</p>
                  <p className="text-base font-mono font-semibold tabular-nums mt-0.5 text-green-400">{item.value}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
