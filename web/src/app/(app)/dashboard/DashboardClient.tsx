"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { seedAcceptanceData, importM1B2Model } from "@/lib/actions";
import { Briefcase, TrendingUp, PlusCircle, Database, Download } from "lucide-react";

export interface DashboardData {
  portfolioCount: number;
  modelPublished: boolean;
  modelStatus: string | null;
  modelName: string | null;
  modelDate: string | null;
  holdingsCount: number;
  isOwner: boolean;
}

function EmptyDashboard({ isOwner }: { isOwner: boolean }) {
  const router = useRouter();
  const [seeding, setSeeding] = useState(false);
  const [seedResult, setSeedResult] = useState<string | null>(null);
  const [importingModel, setImportingModel] = useState(false);
  const [modelResult, setModelResult] = useState<string | null>(null);

  async function handleSeed() {
    setSeeding(true);
    setSeedResult(null);
    const result = await seedAcceptanceData();
    if (result.error) {
      setSeedResult(`Error: ${result.error}`);
    } else {
      setSeedResult(result.message || "Done");
      router.refresh();
    }
    setSeeding(false);
  }

  async function handleImportModel() {
    setImportingModel(true);
    setModelResult(null);
    const result = await importM1B2Model();
    if (result.error) {
      setModelResult(`Error: ${result.error}`);
    } else {
      setModelResult(result.message || "Imported");
      router.refresh();
    }
    setImportingModel(false);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      <div className="card p-6">
        <h2 className="text-sm font-semibold mb-4">Getting Started</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <Link href="/portfolios/new" className="flex items-center gap-3 p-3 rounded-lg border border-neutral-700 hover:border-blue-500/50 transition-colors">
            <PlusCircle className="w-5 h-5 text-blue-400" />
            <div>
              <p className="text-sm font-medium">Create Portfolio</p>
              <p className="text-xs text-neutral-500">Start with a new portfolio</p>
            </div>
          </Link>
          <Link href="/model" className="flex items-center gap-3 p-3 rounded-lg border border-neutral-700 hover:border-blue-500/50 transition-colors">
            <TrendingUp className="w-5 h-5 text-green-400" />
            <div>
              <p className="text-sm font-medium">View Model</p>
              <p className="text-xs text-neutral-500">See the official model</p>
            </div>
          </Link>
          {isOwner && (
            <button onClick={handleImportModel} disabled={importingModel} className="flex items-center gap-3 p-3 rounded-lg border border-neutral-700 hover:border-green-500/50 transition-colors text-left">
              <Download className="w-5 h-5 text-green-400" />
              <div>
                <p className="text-sm font-medium">{importingModel ? "Importing..." : "Import Official Model"}</p>
                <p className="text-xs text-neutral-500">M1_B2_QUALITY_VETO_N30</p>
              </div>
            </button>
          )}
          {isOwner && (
            <button onClick={handleSeed} disabled={seeding} className="flex items-center gap-3 p-3 rounded-lg border border-dashed border-neutral-600 hover:border-yellow-500/50 transition-colors text-left">
              <Database className="w-5 h-5 text-yellow-400" />
              <div>
                <p className="text-sm font-medium">{seeding ? "Creating..." : "Seed Test Data"}</p>
                <p className="text-xs text-neutral-500">Populate app for testing</p>
              </div>
            </button>
          )}
        </div>
        {seedResult && (
          <p className={`text-xs mt-3 ${seedResult.startsWith("Error") ? "text-red-400" : "text-green-400"}`}>
            {seedResult}
          </p>
        )}
        {modelResult && (
          <p className={`text-xs mt-3 ${modelResult.startsWith("Error") ? "text-red-400" : "text-green-400"}`}>
            {modelResult}
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
            <h3 className="text-sm font-semibold">Official Model</h3>
          </div>
          <p className="text-neutral-500 text-sm">No published model yet</p>
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

  if (!data || (data.portfolioCount === 0 && !data.modelPublished)) {
    return <EmptyDashboard isOwner={data?.isOwner ?? false} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="metric-label">Portfolios</p>
          <p className="metric-value mt-1">{data.portfolioCount}</p>
        </div>
        <div className="card">
          <p className="metric-label">Model</p>
          <p className="metric-value mt-1">{data.modelPublished ? "Published" : "Draft"}</p>
        </div>
      </div>

      {data.modelName && (
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="metric-label">Official Model</p>
              <p className="font-semibold mt-0.5">{data.modelName}</p>
              {data.modelDate && <p className="text-xs text-neutral-500 mt-0.5">Effective {data.modelDate}</p>}
            </div>
            <div className="text-right">
              <p className="metric-label">Holdings</p>
              <p className="font-semibold mt-0.5">{data.holdingsCount}</p>
            </div>
          </div>
          <div className="flex gap-2 mt-3">
            <Link href="/model" className="nav-link text-xs">View Model →</Link>
            <Link href="/model/history" className="nav-link text-xs">History →</Link>
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
                    <Link href={`/portfolios/${p.id}`} className="nav-link text-xs">Detail</Link>
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
          <span className="text-sm font-medium">Official Model</span>
        </Link>
      </div>
    </div>
  );
}
