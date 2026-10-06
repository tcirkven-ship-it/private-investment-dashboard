import { createServerSupabase } from "@/lib/supabase";
import { loadHoldings } from "@/lib/route-loaders";
import {
  computeInvestedCapital,
  totalPnl,
  totalReturnPct,
  buildQuarterRows,
  buildInceptionRow,
  benchmarkQuarterReturns,
  type PerfTransaction,
  type ValuationSnapshot,
} from "@/lib/performance";
import RecordSnapshotButton from "@/components/performance/RecordSnapshotButton";
import Link from "next/link";

function fmtMoney(n: number | null): string {
  if (n === null || !Number.isFinite(n)) return "—";
  return `$${Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fmtSignedMoney(n: number | null): string {
  if (n === null || !Number.isFinite(n)) return "—";
  return `${n >= 0 ? "+" : "−"}$${Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fmtPct(n: number | null): string {
  if (n === null || !Number.isFinite(n)) return "—";
  return `${n >= 0 ? "+" : "−"}${Math.abs(n).toFixed(2)}%`;
}

export default async function PerformancePage() {
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();

  const { data: portfolios } = await supabase
    .from("portfolios")
    .select("id, name")
    .eq("owner_id", user?.id)
    .order("created_at", { ascending: false });

  if (!portfolios || portfolios.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Performance</h1>
        <div className="card text-center py-12">
          <p className="text-neutral-500">No portfolio yet.</p>
          <Link href="/portfolios" className="btn btn-primary mt-4">Go to Portfolio</Link>
        </div>
      </div>
    );
  }

  const portfolio = portfolios[0];

  let holdingsData: Awaited<ReturnType<typeof loadHoldings>> | null = null;
  let loadError: string | null = null;
  try {
    holdingsData = await loadHoldings(portfolio.id);
  } catch (e: unknown) {
    loadError = e instanceof Error ? e.message : "Unknown error";
  }

  if (loadError || !holdingsData) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Performance</h1>
        <div className="alert alert-error">{loadError || "Failed to load portfolio."}</div>
      </div>
    );
  }

  const { state, transactions, nav } = holdingsData;

  const [valuationsResult, spyResult, qqqResult] = await Promise.all([
    supabase
      .from("portfolio_valuations")
      .select("valuation_date, total_value")
      .eq("portfolio_id", portfolio.id)
      .order("valuation_date", { ascending: true }),
    supabase
      .from("benchmark_observations")
      .select("observation_date, total_return_index")
      .eq("ticker", "SPY")
      .order("observation_date", { ascending: true })
      .limit(5000),
    supabase
      .from("benchmark_observations")
      .select("observation_date, total_return_index")
      .eq("ticker", "QQQ")
      .order("observation_date", { ascending: true })
      .limit(5000),
  ]);

  const valuations: ValuationSnapshot[] = (valuationsResult.data ?? []).map((v) => ({
    valuation_date: String(v.valuation_date),
    total_value: Number(v.total_value),
  }));

  const perfTxs: PerfTransaction[] = transactions.map((t) => ({
    event_type: t.event_type,
    event_date: t.event_date,
    quantity: t.quantity,
    price: t.price,
    gross_amount: t.gross_amount,
    commission: t.commission,
  }));

  const today = new Date().toISOString().slice(0, 10);

  const invested = computeInvestedCapital(perfTxs);
  const currentValue = nav;
  const pnl = totalPnl(currentValue, invested.value);
  const returnPct = totalReturnPct(pnl, invested.value);

  const holdingsList = [...state.holdings.values()];
  const holdingsValue = holdingsList.reduce((s, h) => s + (h.market_value || 0), 0);
  const unrealized = holdingsList.reduce((s, h) => s + (h.unrealized_pl || 0), 0);
  const missingPrices = holdingsList.some((h) => h.market_value === undefined || h.market_value === null);

  const spyObs = (spyResult.data ?? []).map((o) => ({
    observation_date: String(o.observation_date),
    total_return_index: o.total_return_index === null ? null : Number(o.total_return_index),
  }));
  const qqqObs = (qqqResult.data ?? []).map((o) => ({
    observation_date: String(o.observation_date),
    total_return_index: o.total_return_index === null ? null : Number(o.total_return_index),
  }));

  const benchmarkReturns = {
    SPY: benchmarkQuarterReturns(spyObs),
    QQQ: benchmarkQuarterReturns(qqqObs),
  };

  const quarterRows = buildQuarterRows({
    transactions: perfTxs,
    valuations,
    currentValue,
    today,
    benchmarkReturns,
  });

  const inceptionRow = buildInceptionRow({
    transactions: perfTxs,
    currentValue,
    netInvested: invested.value,
    today,
    benchmarkObservations: { SPY: spyObs, QQQ: qqqObs },
  });

  const allRows = [inceptionRow, ...quarterRows];
  const hasEstimatedValues = allRows.some((r) => r.endValueEstimated);

  const pnlClass = pnl >= 0 ? "metric-positive" : "metric-negative";

  return (
    <div className="space-y-5">
      <div className="page-header">
        <h1>
          Performance
          {portfolio.name ? <span className="text-neutral-500 font-normal text-base ml-2">· {portfolio.name}</span> : null}
        </h1>
        <RecordSnapshotButton portfolioId={portfolio.id} />
      </div>

      {invested.estimated && (
        <div className="alert alert-warning">
          <p className="font-medium">Invested capital may be inaccurate. Add a Deposit transaction for the original funding amount.</p>
          <p className="mt-1 text-xs opacity-80">
            No deposit or withdrawal transactions were found. Invested capital shown below is <strong>estimated</strong> from buy/sell activity.
          </p>
        </div>
      )}

      {missingPrices && (
        <div className="alert alert-warning">
          Some holdings lack current prices, so current value and unrealized P/L may be understated. Refresh prices on the Portfolio page.
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="metric-card metric-primary">
          <p className="metric-label">Invested Capital{invested.estimated ? " (est.)" : ""}</p>
          <p className="metric-value metric-value-xl">{fmtMoney(invested.value)}</p>
          <p className="metric-sub">{invested.estimated ? "estimated from buy/sell activity" : "deposits − withdrawals"}</p>
        </div>
        <div className="metric-card metric-primary">
          <p className="metric-label">Current Value</p>
          <p className="metric-value metric-value-xl">{fmtMoney(currentValue)}</p>
          <p className="metric-sub">Cash + Holdings</p>
        </div>
        <div className="metric-card metric-primary">
          <p className="metric-label">Total P&L</p>
          <p className={`metric-value metric-value-xl ${pnlClass}`}>{fmtSignedMoney(pnl)}</p>
        </div>
        <div className="metric-card metric-primary">
          <p className="metric-label">Total Return</p>
          <p className={`metric-value metric-value-xl ${returnPct === null ? "" : returnPct >= 0 ? "metric-positive" : "metric-negative"}`}>{fmtPct(returnPct)}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="metric-card metric-quiet">
          <p className="metric-label">Realized P/L</p>
          <p className={`metric-value ${state.total_realized_pl >= 0 ? "metric-positive" : "metric-negative"}`}>{fmtSignedMoney(state.total_realized_pl)}</p>
        </div>
        <div className="metric-card metric-quiet">
          <p className="metric-label">Unrealized P/L</p>
          <p className={`metric-value ${unrealized >= 0 ? "metric-positive" : "metric-negative"}`}>{fmtSignedMoney(unrealized)}</p>
        </div>
        <div className="metric-card metric-quiet">
          <p className="metric-label">Cash (uninvested)</p>
          <p className="metric-value">{fmtMoney(state.cash)}</p>
        </div>
        <div className="metric-card metric-quiet">
          <p className="metric-label">Holdings Value</p>
          <p className="metric-value">{fmtMoney(holdingsValue)}</p>
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="flex items-center justify-between p-4 pb-3 flex-wrap gap-2">
          <h2 className="text-sm font-semibold text-neutral-300">Quarterly Performance</h2>
          <p className="text-xs text-neutral-500">
            Start/end values come from valuation snapshots. SPY/QQQ use dividend-adjusted benchmark closes.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[960px]">
            <colgroup>
              <col style={{ width: "10%" }} />
              <col style={{ width: "10%" }} />
              <col style={{ width: "11%" }} />
              <col style={{ width: "11%" }} />
              <col style={{ width: "10%" }} />
              <col style={{ width: "9%" }} />
              <col style={{ width: "9%" }} />
              <col style={{ width: "9%" }} />
              <col style={{ width: "10.5%" }} />
              <col style={{ width: "10.5%" }} />
            </colgroup>
            <thead>
              <tr>
                <th className="table-header td-left">Quarter</th>
                <th className="table-header td-right">Start Value</th>
                <th className="table-header td-right">End / Current Value</th>
                <th className="table-header td-right">External Cash Flow</th>
                <th className="table-header td-right">P&L</th>
                <th className="table-header td-right">Return %</th>
                <th className="table-header td-right">Benchmark SPY %</th>
                <th className="table-header td-right">Benchmark QQQ %</th>
                <th className="table-header td-right">Diff vs SPY</th>
                <th className="table-header td-right">Diff vs QQQ</th>
              </tr>
            </thead>
            <tbody>
              {allRows.map((row) => {
                const diffSpy = row.returnPct !== null && row.spyReturnPct !== null ? row.returnPct - row.spyReturnPct : null;
                const diffQqq = row.returnPct !== null && row.qqqReturnPct !== null ? row.returnPct - row.qqqReturnPct : null;
                const rowKey = row.isInception ? "inception" : row.label;
                return (
                  <tr key={rowKey} className={`table-row ${row.isInception ? "border-b border-white/10" : ""}`}>
                    <td className="table-cell-text td-left font-semibold text-neutral-200">
                      {row.label}
                      {row.isCurrent && <span className="badge badge-blue ml-2">current</span>}
                    </td>
                    <td className="table-cell td-right">
                      {fmtMoney(row.startValue)}
                      {row.startValueNote && <span className="block text-[10px] text-neutral-500">{row.startValueNote}</span>}
                    </td>
                    <td className="table-cell td-right">
                      {fmtMoney(row.endValue)}
                      {row.endValueEstimated && <span title="Latest available valuation used">*</span>}
                    </td>
                    <td className={`table-cell td-right ${row.externalFlow > 0 ? "metric-positive" : row.externalFlow < 0 ? "metric-negative" : ""}`}>
                      {row.externalFlow === 0 ? "$0.00" : fmtSignedMoney(row.externalFlow)}
                    </td>
                    <td className={`table-cell td-right ${row.pnl === null ? "" : row.pnl >= 0 ? "metric-positive" : "metric-negative"}`}>
                      {row.pnl === null ? "—" : fmtSignedMoney(row.pnl)}
                    </td>
                    <td className={`table-cell td-right ${row.returnPct === null ? "" : row.returnPct >= 0 ? "metric-positive" : "metric-negative"}`}>
                      {fmtPct(row.returnPct)}
                    </td>
                    <td className="table-cell td-right">{row.spyReturnPct === null ? "N/A" : fmtPct(row.spyReturnPct)}</td>
                    <td className="table-cell td-right">{row.qqqReturnPct === null ? "N/A" : fmtPct(row.qqqReturnPct)}</td>
                    <td className={`table-cell td-right ${diffSpy === null ? "" : diffSpy >= 0 ? "metric-positive" : "metric-negative"}`}>
                      {diffSpy === null ? "N/A" : fmtPct(diffSpy)}
                    </td>
                    <td className={`table-cell td-right ${diffQqq === null ? "" : diffQqq >= 0 ? "metric-positive" : "metric-negative"}`}>
                      {diffQqq === null ? "N/A" : fmtPct(diffQqq)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="px-4 pb-4 space-y-1">
          {hasEstimatedValues && (
            <p className="text-xs text-neutral-500">
              * No snapshot existed at that quarter end; the latest available valuation is shown instead.
            </p>
          )}
          <p className="text-xs text-neutral-500">
            SPY/QQQ show the dividend-adjusted benchmark return over the same period as each row
            ({valuations.length === 0 ? "inception: Jul 1 to today; quarters: quarter start to quarter end or today" : "quarter start to quarter end or today"}).
          </p>
          <p className="text-xs text-neutral-500">
            Deposits made inside a quarter appear as External Cash Flow; a quarter&apos;s start value is the portfolio value
            just before the quarter began (empty portfolio = $0).
          </p>
          <p className="text-xs text-neutral-500">
            {valuations.length === 0
              ? <>No valuation snapshots recorded yet. Use <strong>Record Valuation Snapshot</strong> above — especially at quarter ends — to make quarterly start/end values exact.</>
              : <>Quarter boundaries become exact as snapshots accumulate at quarter ends.</>}
          </p>
        </div>
      </div>
    </div>
  );
}
