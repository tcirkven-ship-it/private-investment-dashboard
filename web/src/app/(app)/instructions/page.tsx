export default function InstructionsPage() {
  return (
    <div className="space-y-10 max-w-3xl">
      <h1 className="text-2xl font-semibold">Instructions</h1>

      <section>
        <h2 className="text-lg font-semibold mb-4">Quarterly Review</h2>
        <ol className="space-y-3 text-sm text-neutral-300 list-decimal list-inside">
          <li>Wait for the final trading session of the quarter to close.</li>
          <li>Download fresh market data from your data provider (e.g. yfinance, API).</li>
          <li>Run the official generator notebook to produce a new Top 30 ranking.</li>
          <li>Export the Top 30 CSV file together with its manifest.</li>
          <li>Open the app and navigate to the <strong>Model</strong> page.</li>
          <li>Load the notebook-generated Top 30 CSV into the app.</li>
          <li>Review the Top 30 list sorted by B2 score on the Model page.</li>
          <li>Go to the <strong>Portfolio</strong> page and click <strong>Refresh Current Prices</strong> to get latest quotes.</li>
          <li>Open the <strong>Compare</strong> page to see which holdings are in/out of the Top 30.</li>
          <li>Review the three comparison sections: Already Own, Consider Buying, and Consider Selling.</li>
          <li>Make manual buy/sell decisions at your brokerage. The app does not execute trades.</li>
        </ol>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Required CSV Columns</h2>
        <p className="text-sm text-neutral-300 mb-2">The notebook-generated Top 30 CSV must include these columns:</p>
        <ul className="space-y-1 text-sm text-neutral-400 list-disc list-inside">
          <li>
            <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">ticker</code> &mdash; required
          </li>
          <li>
            <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">company</code> &mdash; optional
          </li>
          <li>
            <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">sector</code> &mdash; required
          </li>
          <li>
            <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">industry</code> &mdash; required
          </li>
          <li>
            <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">rank</code> &mdash; optional
          </li>
          <li>
            <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">B2_score</code> &mdash; required
          </li>
          <li>
            <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">Q_score</code> or{" "}
            <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">Q_percentile</code> &mdash; required
          </li>
          <li>
            <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">as_of_date</code> &mdash; via manifest
          </li>
          <li>
            <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">generated_at</code> &mdash; via manifest
          </li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Date Meanings</h2>
        <div className="space-y-3 text-sm text-neutral-300">
          <div>
            <p className="font-medium text-neutral-200">as_of_date</p>
            <p className="text-neutral-400">The market data date / quarter-end date. This is the date for which the model was generated (e.g. 2026-06-30 for Q2 2026).</p>
          </div>
          <div>
            <p className="font-medium text-neutral-200">generated_at</p>
            <p className="text-neutral-400">When the notebook generated the CSV file. This is a timestamp from the generator, not from the app.</p>
          </div>
          <div>
            <p className="font-medium text-neutral-200">loaded_at</p>
            <p className="text-neutral-400">When the app loaded/imported the CSV. This is set by the app at import time.</p>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Portfolio Prices</h2>
        <ul className="space-y-2 text-sm text-neutral-300 list-disc list-inside">
          <li>Prices shown are the latest available quotes and may be delayed (not real-time).</li>
          <li>Use the <strong>Refresh Current Prices</strong> button on the Portfolio page to fetch updated prices.</li>
          <li>Prices are sourced from Yahoo Finance and cached per trading day.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Manual Decisions</h2>
        <ul className="space-y-2 text-sm text-neutral-300 list-disc list-inside">
          <li>The app does <strong>not</strong> trade, execute orders, or connect to any broker.</li>
          <li>All buy/sell decisions are made and executed manually by you at your brokerage.</li>
          <li>The Compare page provides decision support only &mdash; it is not investment advice.</li>
        </ul>
      </section>
    </div>
  );
}
