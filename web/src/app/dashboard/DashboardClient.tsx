"use client";

export interface DashboardData {
  portfolioCount: number;
  modelPublished: boolean;
}

function EmptyDashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-neutral-500 mt-1">Welcome to your investment dashboard</p>
        </div>
      </div>
      <div className="card p-8 text-center">
        <p className="text-neutral-400 text-sm">No portfolio data yet.</p>
        <p className="text-neutral-500 text-xs mt-2">Create a portfolio and add transactions to see your dashboard.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-6">
          <h3 className="text-sm font-semibold mb-2">Portfolios</h3>
          <p className="text-neutral-500 text-sm">No portfolios yet</p>
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
    return <EmptyDashboard />;
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
