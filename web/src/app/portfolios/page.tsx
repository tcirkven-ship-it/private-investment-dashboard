"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase";
import { Plus, ArrowRight, TrendingUp, TrendingDown } from "lucide-react";

interface Portfolio {
  id: string;
  name: string;
  opening_date: string;
  starting_cash: number;
  is_archived: boolean;
}

export default function PortfoliosPage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);

  useEffect(() => {
    // In production, load from Supabase
    setPortfolios([
      { id: "1", name: "Main Brokerage", opening_date: "2025-01-01", starting_cash: 100000, is_archived: false },
      { id: "2", name: "Retirement", opening_date: "2025-06-01", starting_cash: 50000, is_archived: false },
      { id: "3", name: "Paper Account", opening_date: "2026-03-01", starting_cash: 25000, is_archived: false },
    ]);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Portfolios</h1>
          <p className="text-sm text-neutral-500 mt-1">Manage your personal portfolios</p>
        </div>
        <Link href="/portfolios/new" className="btn-primary">
          <Plus className="w-4 h-4 mr-1.5" /> New Portfolio
        </Link>
      </div>

      {portfolios.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No portfolios yet. Create your first one.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {portfolios.map((p) => (
            <Link key={p.id} href={`/portfolios/${p.id}`} className="card hover:bg-neutral-900/50 transition-colors block">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{p.name}</h3>
                  <p className="text-sm text-neutral-500 mt-0.5">
                    Opened {p.opening_date} · ${p.starting_cash.toLocaleString()} initial
                    {p.is_archived && <span className="ml-2 text-yellow-500">Archived</span>}
                  </p>
                </div>
                <ArrowRight className="w-4 h-4 text-neutral-500" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
