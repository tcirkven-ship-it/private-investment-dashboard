"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Download } from "lucide-react";
import { deriveHoldings, totalNav } from "@/lib/holdings";

interface Tx {
  event_type: string; event_date: string; ticker: string;
  quantity: number; price: number; gross_amount: number; commission: number; tax: number;
}

const MOCK_TXS: Tx[] = [
  { event_type: "DEPOSIT", event_date: "2026-01-02", ticker: "", quantity: 0, price: 0, gross_amount: 100000, commission: 0, tax: 0 },
  { event_type: "BUY", event_date: "2026-01-05", ticker: "AAPL", quantity: 50, price: 185, gross_amount: 9250, commission: 5, tax: 0 },
  { event_type: "BUY", event_date: "2026-01-05", ticker: "MSFT", quantity: 30, price: 420, gross_amount: 12600, commission: 5, tax: 0 },
  { event_type: "BUY", event_date: "2026-02-01", ticker: "GOOGL", quantity: 20, price: 190, gross_amount: 3800, commission: 3, tax: 0 },
  { event_type: "DIVIDEND", event_date: "2026-02-15", ticker: "AAPL", quantity: 0, price: 0, gross_amount: 50, commission: 0, tax: 0 },
  { event_type: "FEE", event_date: "2026-03-01", ticker: "", quantity: 0, price: 0, gross_amount: 5, commission: 0, tax: 0 },
];

const PRICES = new Map([["AAPL", 195], ["MSFT", 440], ["GOOGL", 185]]);

export default function HoldingsPage() {
  const { id } = useParams();
  const state = deriveHoldings(MOCK_TXS, PRICES);
  const nav = totalNav(state);

  const csvContent = [
    "Ticker,Quantity,Avg Cost,Market Value,Unrealized P/L,Weight",
    ...[...state.holdings.values()].map(h =>
      `${h.ticker},${h.quantity},${h.average_cost.toFixed(2)},${(h.market_value || 0).toFixed(2)},${(h.unrealized_pl || 0).toFixed(2)},${(h.market_value ? h.market_value / nav * 100 : 0).toFixed(2)}%`
    ),
  ].join("\n");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/portfolios/${id}`} className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <div>
            <h1 className="text-xl font-semibold">Holdings</h1>
            <p className="text-sm text-neutral-500">NAV: ${nav.toLocaleString()}</p>
          </div>
        </div>
        <a href={`data:text/csv;charset=utf-8,${encodeURIComponent(csvContent)}`}
           download="holdings.csv" className="btn-secondary">
          <Download className="w-4 h-4 mr-1" />CSV
        </a>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card"><p className="metric-label">Cash</p><p className="metric-value mt-1">${state.cash.toLocaleString()}</p></div>
        <div className="card"><p className="metric-label">Invested</p><p className="metric-value mt-1">${(nav - state.cash).toLocaleString()}</p></div>
        <div className="card"><p className="metric-label">Realized P/L</p><p className={`metric-value mt-1 ${state.total_realized_pl >= 0 ? "text-green-400" : "text-red-400"}`}>${state.total_realized_pl.toFixed(0)}</p></div>
        <div className="card"><p className="metric-label">Dividends</p><p className="metric-value mt-1 text-blue-400">${state.total_dividends.toFixed(0)}</p></div>
      </div>

      {state.holdings.size === 0 ? (
        <div className="card text-center py-12"><p className="text-neutral-500">No holdings. Add transactions to build your portfolio.</p></div>
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
              {[...state.holdings.values()].sort((a, b) => (b.market_value || 0) - (a.market_value || 0)).map((h) => {
                const weight = h.market_value ? h.market_value / nav * 100 : 0;
                return (
                  <tr key={h.ticker} className="border-b border-neutral-800/50">
                    <td className="table-cell-text font-semibold">{h.ticker}</td>
                    <td className="table-cell text-right">{h.quantity.toFixed(2)}</td>
                    <td className="table-cell text-right">${h.average_cost.toFixed(2)}</td>
                    <td className="table-cell text-right">${(h.current_price || 0).toFixed(2)}</td>
                    <td className="table-cell text-right">${(h.market_value || 0).toLocaleString()}</td>
                    <td className={`table-cell text-right ${(h.unrealized_pl || 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                      ${(h.unrealized_pl || 0).toFixed(2)}
                    </td>
                    <td className="table-cell text-right">{weight.toFixed(1)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
