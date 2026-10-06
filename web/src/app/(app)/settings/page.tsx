"use client";

import { useState } from "react";
import { deleteAllAppData } from "@/lib/actions";

interface DryRunCounts {
  portfolio_valuations: number;
  owner_decisions: number;
  rebalance_lines: number;
  rebalance_events: number;
  transactions: number;
  model_snapshot_holdings: number;
  model_snapshots: number;
  model_versions: number;
  price_observations: number;
  portfolios: number;
  securities: number;
  app_settings: number;
}

export default function SettingsPage() {
  const [counts, setCounts] = useState<DryRunCounts | null>(null);
  const [confirmText, setConfirmText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleDryRun() {
    setLoading(true);
    setError(null);
    setResult(null);
    const res = await deleteAllAppData();
    if (res.error) {
      setError(res.error);
      setCounts(null);
    } else if (res.counts) {
      setCounts({
        portfolio_valuations: res.counts.portfolio_valuations ?? 0,
        owner_decisions: res.counts.owner_decisions ?? 0,
        rebalance_lines: res.counts.rebalance_lines ?? 0,
        rebalance_events: res.counts.rebalance_events ?? 0,
        transactions: res.counts.transactions ?? 0,
        model_snapshot_holdings: res.counts.model_snapshot_holdings ?? 0,
        model_snapshots: res.counts.model_snapshots ?? 0,
        model_versions: res.counts.model_versions ?? 0,
        price_observations: res.counts.price_observations ?? 0,
        portfolios: res.counts.portfolios ?? 0,
        securities: res.counts.securities ?? 0,
        app_settings: res.counts.app_settings ?? 0,
      });
    }
    setLoading(false);
  }

  async function handleReset() {
    if (confirmText !== "RESET") return;
    setLoading(true);
    setError(null);
    const res = await deleteAllAppData(true);
    if (res.error) {
      setError(res.error);
    } else {
      setResult("All app data has been deleted successfully.");
      setCounts(null);
      setConfirmText("");
    }
    setLoading(false);
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-semibold">Settings</h1>

      <div className="card border-red-500/30 space-y-4">
        <h2 className="text-sm font-semibold text-red-400">Reset App Data</h2>
        <p className="text-sm text-neutral-400">
          This will permanently delete all application data including portfolios, transactions, model snapshots,
          price observations, and decisions. This action cannot be undone.
        </p>

        {error && (
          <div className="text-sm text-red-400 bg-red-500/10 rounded px-3 py-2">{error}</div>
        )}
        {result && (
          <div className="text-sm text-green-400 bg-green-500/10 rounded px-3 py-2">{result}</div>
        )}

        {counts && (
          <div className="card bg-neutral-900 border-neutral-800 space-y-2">
            <h3 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider">Rows to be deleted</h3>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              <div className="flex justify-between"><span className="text-neutral-400">Portfolio Valuations</span><span className="font-mono text-neutral-200">{counts.portfolio_valuations}</span></div>
              <div className="flex justify-between"><span className="text-neutral-400">Owner Decisions</span><span className="font-mono text-neutral-200">{counts.owner_decisions}</span></div>
              <div className="flex justify-between"><span className="text-neutral-400">Rebalance Lines</span><span className="font-mono text-neutral-200">{counts.rebalance_lines}</span></div>
              <div className="flex justify-between"><span className="text-neutral-400">Rebalance Events</span><span className="font-mono text-neutral-200">{counts.rebalance_events}</span></div>
              <div className="flex justify-between"><span className="text-neutral-400">Transactions</span><span className="font-mono text-neutral-200">{counts.transactions}</span></div>
              <div className="flex justify-between"><span className="text-neutral-400">Snapshot Holdings</span><span className="font-mono text-neutral-200">{counts.model_snapshot_holdings}</span></div>
              <div className="flex justify-between"><span className="text-neutral-400">Model Snapshots</span><span className="font-mono text-neutral-200">{counts.model_snapshots}</span></div>
              <div className="flex justify-between"><span className="text-neutral-400">Model Versions</span><span className="font-mono text-neutral-200">{counts.model_versions}</span></div>
              <div className="flex justify-between"><span className="text-neutral-400">Price Observations</span><span className="font-mono text-neutral-200">{counts.price_observations}</span></div>
              <div className="flex justify-between"><span className="text-neutral-400">Portfolios</span><span className="font-mono text-neutral-200">{counts.portfolios}</span></div>
              <div className="flex justify-between"><span className="text-neutral-400">Securities</span><span className="font-mono text-neutral-200">{counts.securities}</span></div>
              <div className="flex justify-between"><span className="text-neutral-400">App Settings</span><span className="font-mono text-neutral-200">{counts.app_settings}</span></div>
            </div>
          </div>
        )}

        <button
          onClick={handleDryRun}
          disabled={loading}
          className="btn btn-secondary text-sm"
        >
          {loading ? "Checking..." : "Reset App Data"}
        </button>

        {counts && (
          <div className="space-y-2">
            <p className="text-xs text-neutral-500">
              Type <code className="bg-neutral-800 px-1 rounded">RESET</code> to confirm deletion:
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                className="input text-sm max-w-[200px]"
                placeholder="RESET"
              />
              <button
                onClick={handleReset}
                disabled={confirmText !== "RESET" || loading}
                className="btn btn-primary text-sm bg-red-600 hover:bg-red-500 disabled:opacity-50"
              >
                {loading ? "Deleting..." : "Confirm Reset"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
