"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { seedAcceptanceData } from "@/lib/actions";

export interface DashboardData {
  portfolioCount: number;
  modelPublished: boolean;
  isOwner: boolean;
}

function EmptyDashboard({ isOwner }: { isOwner: boolean }) {
  const router = useRouter();
  const [seeding, setSeeding] = useState(false);
  const [seedResult, setSeedResult] = useState<string | null>(null);

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-neutral-500 mt-1">Welcome to your investment dashboard</p>
        </div>
      </div>

      <div className="card p-6">
        <h2 className="text-sm font-semibold mb-3">Getting Started</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Link href="/portfolios/new" className="btn-primary text-center text-sm">
            Create Portfolio
          </Link>
          <Link href="/model" className="btn-secondary text-center text-sm">
            View Model
          </Link>
          {isOwner && (
            <button onClick={handleSeed} disabled={seeding} className="btn-ghost text-sm border border-dashed border-neutral-600">
              {seeding ? "Creating..." : "Seed Test Data"}
            </button>
          )}
        </div>
        {seedResult && (
          <p className={`text-xs mt-3 ${seedResult.startsWith("Error") ? "text-red-400" : "text-green-400"}`}>
            {seedResult}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-6">
          <h3 className="text-sm font-semibold mb-2">Portfolios</h3>
          <p className="text-neutral-500 text-sm mb-3">No portfolios yet</p>
          <Link href="/portfolios/new" className="text-xs text-blue-400 hover:underline">Create your first portfolio →</Link>
        </div>
        <div className="card p-6">
          <h3 className="text-sm font-semibold mb-2">Official Model</h3>
          <p className="text-neutral-500 text-sm">No published model yet</p>
        </div>
      </div>
    </div>
  );
}

export default function DashboardClient({ data, error }: {
  data: DashboardData | null;
  error: string | null;
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
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-neutral-500 mt-1">Portfolio summary</p>
        </div>
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
    </div>
  );
}
