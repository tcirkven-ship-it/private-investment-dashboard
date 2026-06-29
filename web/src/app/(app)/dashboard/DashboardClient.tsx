"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { importM1B2Model, refreshClosingPrices } from "@/lib/actions";
import { Briefcase, TrendingUp, PlusCircle, RefreshCw, Clock } from "lucide-react";

function nextReviewWindow(): string {
  const d = new Date();
  const q = Math.floor(d.getMonth() / 3);
  const months = ["March", "June", "September", "December"];
  const qEnd = months[q];
  const year = q === 3 && d.getMonth() >= 9 ? d.getFullYear() + 1 : d.getFullYear();
  return `Next review window: after final trading session of ${qEnd} ${year}`;
}

function quarterLabel(dateStr: string | null): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  const q = Math.floor(d.getMonth() / 3) + 1;
  return `Q${q} ${d.getFullYear()}`;
}

export interface DashboardData {
  nextAction?: string;
  nextReviewWindow?: string;
  portfolioCount: number;
  hasModel: boolean;
  modelStatus: string | null;
  modelDate: string | null;
  holdingsCount: number;
  modelPublished: boolean;
  modelDraft: boolean;
  lastPriceDate: string | null;
}

function EmptyDashboard() {
  const router = useRouter();
  const [generating, setGenerating] = useState(false);
  const [genResult, setGenResult] = useState<string | null>(null);

  async function handleGenerate() {
    setGenerating(true);
    setGenResult(null);
    const result = await importM1B2Model();
    if (result.error) {
      setGenResult(result.error);
    } else {
      setGenResult(result.message || "Done");
      router.refresh();
    }
    setGenerating(false);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      <div className="card p-6">
        <h2 className="text-sm font-semibold mb-4">Getting Started</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-3 p-3 rounded-lg border border-neutral-700 hover:border-blue-500/50 transition-colors text-left disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 text-blue-400 ${generating ? "animate-spin" : ""}`} />
            <div>
              <p className="text-sm font-medium">{generating ? "Generating..." : "Generate Quarter-End Top 30"}</p>
              <p className="text-xs text-neutral-500">Import M1_B2_QUALITY_VETO_N30 model</p>
            </div>
          </button>
          <Link href="/portfolios/new" className="flex items-center gap-3 p-3 rounded-lg border border-neutral-700 hover:border-blue-500/50 transition-colors">
            <PlusCircle className="w-5 h-5 text-blue-400" />
            <div>
              <p className="text-sm font-medium">Create My Portfolio</p>
              <p className="text-xs text-neutral-500">Start with a new portfolio</p>
            </div>
          </Link>
          <Link href="/model" className="flex items-center gap-3 p-3 rounded-lg border border-neutral-700 hover:border-blue-500/50 transition-colors">
            <TrendingUp className="w-5 h-5 text-green-400" />
            <div>
              <p className="text-sm font-medium">View Model</p>
              <p className="text-xs text-neutral-500">See the Quarterly Top 30</p>
            </div>
          </Link>
        </div>
        {genResult && (
          <p className={`text-xs mt-3 ${genResult.includes("generated with") ? "text-green-400" : "text-red-400"}`}>
            {genResult}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-3">
            <Briefcase className="w-4 h-4 text-neutral-400" />
            <h3 className="text-sm font-semibold">Portfolios</h3>
          </div>
          <p className="text-neutral-500 text-sm">No portfolios yet</p>
          <Link href="/portfolios/new" className="text-xs text-blue-400 hover:underline mt-2 inline-block">Create your first portfolio →</Link>
        </div>
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-neutral-400" />
            <h3 className="text-sm font-semibold">Quarterly Top 30</h3>
          </div>
          <p className="text-neutral-500 text-sm">No model imported yet</p>
        </div>
      </div>
    </div>
  );
}

interface PortfolioSummary {
  id: string;
  name: string;
  opening_date: string;
  starting_cash: number | null;
  notes: string | null;
}

export default function DashboardClient({ data, error, portfolios }: {
  data: DashboardData | null;
  error: string | null;
  portfolios: PortfolioSummary[];
}) {
  const [genLoading, setGenLoading] = useState(false);
  const [genResult, setGenResult] = useState<{ msg: string; isErr: boolean } | null>(null);
  const [priceLoading, setPriceLoading] = useState(false);
  const [priceResult, setPriceResult] = useState<{ msg: string; isErr: boolean } | null>(null);
  const router = useRouter();

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="card p-6 border-red-500/20">
          <p className="text-red-400 text-sm">Error loading dashboard</p>
          <p className="text-neutral-500 text-xs mt-1">{error}</p>
        </div>
      </div>
    );
  }

  if (!data || (data.portfolioCount === 0 && !data.hasModel)) {
    return <EmptyDashboard />;
  }

  const modelStatusColor =
    data.modelStatus === "PUBLISHED" ? "text-green-400" :
    data.modelStatus === "DRAFT" ? "text-yellow-400" : "text-neutral-400";

  async function handleGenerate() {
    setGenLoading(true);
    setGenResult(null);
    const res = await importM1B2Model();
    setGenLoading(false);
    if (res.error) {
      setGenResult({ msg: res.error, isErr: true });
    } else {
      setGenResult({ msg: res.message || "Done", isErr: false });
      router.refresh();
    }
  }

  async function handleRefreshPrices() {
    setPriceLoading(true);
    setPriceResult(null);
    const res = await refreshClosingPrices();
    setPriceLoading(false);
    if (res.error) {
      setPriceResult({ msg: res.error, isErr: true });
    } else {
      setPriceResult({ msg: res.message || "Done", isErr: false });
      router.refresh();
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-semibold">Quarter-End Readiness</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm mb-4">
          <div>
            <p className="text-xs text-neutral-500 uppercase tracking-wider">Model Date</p>
            <p className="font-semibold mt-0.5">{data.modelDate || "—"}</p>
          </div>
          <div>
            <p className="text-xs text-neutral-500 uppercase tracking-wider">Holdings</p>
            <p className="font-semibold mt-0.5">{data.holdingsCount}</p>
          </div>
          <div>
            <p className="text-xs text-neutral-500 uppercase tracking-wider">Latest Price Data</p>
            <p className="font-semibold mt-0.5">{data.lastPriceDate || "No data"}</p>
          </div>
        </div>
        <div className="border-t border-neutral-800 pt-4">
          <p className="text-xs text-neutral-500 uppercase tracking-wider mb-3">Next Actions</p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleGenerate}
              disabled={genLoading}
              className="text-xs px-3 py-1.5 rounded border border-neutral-700 hover:border-blue-500/50 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 inline mr-1 ${genLoading ? "animate-spin" : ""}`} />
              Generate Quarter-End Top 30
            </button>
            <button
              onClick={handleRefreshPrices}
              disabled={priceLoading}
              className="text-xs px-3 py-1.5 rounded border border-neutral-700 hover:border-blue-500/50 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 inline mr-1 ${priceLoading ? "animate-spin" : ""}`} />
              Refresh Closing Prices
            </button>
            {portfolios.length > 0 && (
              <>
                <Link
                  href={`/portfolios/${portfolios[0].id}/performance`}
                  className="text-xs px-3 py-1.5 rounded border border-neutral-700 hover:border-blue-500/50 transition-colors inline-flex items-center"
                >
                  Record Valuation Snapshot
                </Link>
                <Link
                  href={`/portfolios/${portfolios[0].id}/rebalance`}
                  className="text-xs px-3 py-1.5 rounded border border-neutral-700 hover:border-blue-500/50 transition-colors inline-flex items-center"
                >
                  Review Rebalance Instructions
                </Link>
              </>
            )}
          </div>
        </div>
        {genResult && (
          <p className={`text-xs mt-3 ${genResult.isErr ? "text-red-400" : "text-green-400"}`}>
            {genResult.msg}
          </p>
        )}
        {priceResult && (
          <p className={`text-xs mt-3 ${priceResult.isErr ? "text-red-400" : "text-green-400"}`}>
            {priceResult.msg}
          </p>
        )}
      </div>

      {data.hasModel && (
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold">Quarterly Workflow</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-xs text-neutral-500 uppercase tracking-wider">Model</p>
              <p className="font-semibold mt-0.5">M1_B2_QUALITY_VETO_N30</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 uppercase tracking-wider">Status</p>
              <p className={`font-semibold mt-0.5 ${modelStatusColor}`}>{data.modelStatus}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 uppercase tracking-wider">Holdings</p>
              <p className="font-semibold mt-0.5">{data.holdingsCount}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 uppercase tracking-wider">Next Review</p>
              <p className="text-xs font-semibold mt-0.5">{data.nextReviewWindow || nextReviewWindow()}</p>
            </div>
          </div>
          {data.nextAction && (
            <p className="text-xs text-blue-400 mt-3 pt-3 border-t border-neutral-800">
              Next step: {data.nextAction}
            </p>
          )}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="metric-label">Portfolios</p>
          <p className="metric-value mt-1">{data.portfolioCount}</p>
        </div>
        <div className="card">
          <p className="metric-label">Model</p>
          <p className="metric-value mt-1">{data.modelStatus || "None"}</p>
        </div>
      </div>

      {data.hasModel && (
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-neutral-400" />
            <h2 className="text-sm font-semibold">M1_B2_QUALITY_VETO_N30</h2>
            {quarterLabel(data.modelDate) && (
              <span className="text-xs text-neutral-500">{quarterLabel(data.modelDate)}</span>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-xs text-neutral-500 uppercase tracking-wider">Status</p>
              <p className={`font-semibold mt-0.5 ${modelStatusColor}`}>{data.modelStatus}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 uppercase tracking-wider">Effective Date</p>
              <p className="font-semibold mt-0.5">{data.modelDate || "—"}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 uppercase tracking-wider">Holdings</p>
              <p className="font-semibold mt-0.5">{data.holdingsCount}</p>
            </div>
          </div>
          <div className="flex gap-4 mt-4 pt-4 border-t border-neutral-800">
            <Link href="/model" className="text-xs text-blue-400 hover:underline">Quarterly Top 30 →</Link>
            <Link href="/model/history" className="text-xs text-blue-400 hover:underline">Model History →</Link>
            <Link href="/portfolios" className="text-xs text-blue-400 hover:underline">Rebalance Instructions →</Link>
          </div>
        </div>
      )}

      {portfolios.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold mb-3">Your Portfolios</h2>
          <div className="grid gap-3">
            {portfolios.map((p) => (
              <div key={p.id} className="card p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Link href={`/portfolios/${p.id}`} className="font-semibold hover:text-blue-400 transition-colors">
                      {p.name}
                    </Link>
                    <p className="text-xs text-neutral-500 mt-0.5">
                      Opened {p.opening_date}{p.starting_cash ? ` · $${p.starting_cash.toLocaleString()} initial` : ""}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Link href={`/portfolios/${p.id}/holdings`} className="nav-link text-xs">Holdings</Link>
                    <Link href={`/portfolios/${p.id}/transactions`} className="nav-link text-xs">Transactions</Link>
                    <Link href={`/portfolios/${p.id}/rebalance`} className="nav-link text-xs">Rebalance</Link>
                  </div>
                </div>
                {p.notes && <p className="text-xs text-neutral-500 mt-2">{p.notes}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link href="/portfolios/new" className="card p-4 flex items-center gap-3 hover:bg-neutral-900/50 transition-colors">
          <PlusCircle className="w-5 h-5 text-blue-400" />
          <span className="text-sm font-medium">New Portfolio</span>
        </Link>
        <Link href="/model" className="card p-4 flex items-center gap-3 hover:bg-neutral-900/50 transition-colors">
          <TrendingUp className="w-5 h-5 text-green-400" />
          <span className="text-sm font-medium">Quarterly Top 30</span>
        </Link>
      </div>
    </div>
  );
}
