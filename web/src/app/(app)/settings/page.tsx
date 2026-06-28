"use client";

import { useState } from "react";
import { Shield, Download, Upload, Database, RefreshCw } from "lucide-react";

export default function SettingsPage() {
  const [defaultCurrency] = useState("USD");
  const [benchmark] = useState("SPY");

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-neutral-500 mt-1">Account and application preferences</p>
      </div>

      <div className="card space-y-4">
        <h2 className="text-sm font-semibold flex items-center gap-2"><Shield className="w-4 h-4" /> Account</h2>
        <div className="text-sm text-neutral-400">
          <p>Settings</p>
          <p className="mt-1">MFA: Not enabled</p>
        </div>
      </div>

      <div className="card space-y-4">
        <h2 className="text-sm font-semibold">Preferences</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-1.5">Default Currency</label>
            <select value={defaultCurrency} className="input">
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (€)</option>
              <option value="GBP">GBP (£)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-1.5">Benchmark</label>
            <select value={benchmark} className="input">
              <option value="SPY">SPY (S&P 500)</option>
              <option value="QQQ">QQQ (Nasdaq-100)</option>
              <option value="VOO">VOO (S&P 500)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card space-y-4">
        <h2 className="text-sm font-semibold flex items-center gap-2"><Database className="w-4 h-4" /> Data Management</h2>
        <div className="flex flex-wrap gap-3">
          <button className="btn-secondary"><Download className="w-4 h-4 mr-1.5" /> Export Transactions</button>
          <button className="btn-secondary"><Upload className="w-4 h-4 mr-1.5" /> Import Transactions</button>
          <button className="btn-secondary"><RefreshCw className="w-4 h-4 mr-1.5" /> Refresh Prices</button>
        </div>
      </div>

      <div className="card space-y-4">
        <h2 className="text-sm font-semibold">Admin</h2>
        <div className="flex flex-wrap gap-3">
          <button className="btn-secondary"><Download className="w-4 h-4 mr-1.5" /> Full Backup</button>
          <button className="btn-secondary"><Upload className="w-4 h-4 mr-1.5" /> Restore</button>
        </div>
      </div>
    </div>
  );
}
