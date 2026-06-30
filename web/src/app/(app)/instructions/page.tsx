export default function InstructionsPage() {
  return (
    <div className="space-y-10 max-w-3xl">
      <h1 className="text-2xl font-semibold">Instructions</h1>

      <section>
        <h2 className="text-lg font-semibold mb-4">Quarterly Review &mdash; How To</h2>
        <ol className="space-y-3 text-sm text-neutral-300 list-decimal list-inside">
          <li>Wait for final trading session of quarter.</li>
          <li>Run official generator on notebook.</li>
          <li>Export Top 30 CSV + manifest.</li>
          <li>Open app. Load notebook-generated Top 30.</li>
          <li>Review Top 30 sorted by score.</li>
          <li>Refresh current prices.</li>
          <li>Open Compare page.</li>
          <li>Decide manually what to buy/sell.</li>
        </ol>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">CSV Requirements</h2>
        <p className="text-sm text-neutral-300">
          Required columns: <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">ticker</code>,{" "}
          <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">sector</code>,{" "}
          <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">industry</code>,{" "}
          <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">B2_score</code>,{" "}
          <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">Q_percentile</code> or{" "}
          <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">Q_score</code>,{" "}
          <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">company</code> (optional but recommended),{" "}
          <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">rank</code> (optional but recommended).
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Price Refresh</h2>
        <p className="text-sm text-neutral-300">
          Prices are latest available market quotes and may be delayed.
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Manual Decisions</h2>
        <p className="text-sm text-neutral-300">
          The app does not trade. User executes manually elsewhere.
        </p>
      </section>
    </div>
  );
}
