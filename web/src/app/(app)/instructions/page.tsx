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
      <section>
        <h2 className="text-lg font-semibold mb-4">Portfolio — Add / Edit / Delete Holdings</h2>
        <ul className="space-y-2 text-sm text-neutral-300 list-disc list-inside">
          <li><strong>Add Holding</strong>: Enter ticker, shares, and average cost. Click Add.</li>
          <li><strong>Edit Holding</strong>: Click the edit icon next to a holding. Update shares or average cost. Save.</li>
          <li><strong>Delete Holding</strong>: Click the delete icon, then confirm.</li>
          <li>You cannot add a ticker that is already in your portfolio. Edit the existing holding instead.</li>
          <li>Blank tickers are not allowed. Shares must be greater than zero.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Price Refresh</h2>
        <ul className="space-y-2 text-sm text-neutral-300 list-disc list-inside">
          <li>Click <strong>Refresh Current Prices</strong> on the Portfolio page to fetch latest quotes.</li>
          <li>Only tickers currently in your portfolio are refreshed (not all securities).</li>
          <li>The result shows how many prices refreshed and which tickers failed.</li>
          <li>Prices are latest available quotes from Yahoo Finance and may be delayed.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Compare</h2>
        <ul className="space-y-2 text-sm text-neutral-300 list-disc list-inside">
          <li><strong>Already Own / In Top 30</strong>: Stocks you hold that are also in the current Top 30.</li>
          <li><strong>Consider Buying</strong>: Stocks in the Top 30 that you do not currently own.</li>
          <li><strong>Consider Selling</strong>: Stocks you own that are no longer in the Top 30.</li>
          <li>All decisions are manual. The app does not trade or connect to a broker.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Reset App Data</h2>
        <ul className="space-y-2 text-sm text-neutral-300 list-disc list-inside">
          <li>Go to <strong>Settings</strong> to reset all app data.</li>
          <li>Click <strong>Reset App Data</strong>, review the row counts, then type RESET to confirm.</li>
          <li>This clears portfolios, transactions, model snapshots, prices, and decisions.</li>
          <li>Supabase auth users and migrations are never touched.</li>
          <li>After reset, the app shows an empty Portfolio and no loaded Top 30.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Troubleshooting</h2>
        <div className="space-y-3 text-sm text-neutral-300">
          <div>
            <p className="font-medium text-amber-400">Scores missing in Top 30</p>
            <p className="text-neutral-400">Re-upload the CSV. Ensure it contains B2_score and Q_percentile (or Q_score) columns. The loader rejects CSVs without these columns.</p>
          </div>
          <div>
            <p className="font-medium text-amber-400">Price refresh failed</p>
            <p className="text-neutral-400">Some tickers may not have current quotes available. Check the ticker symbol. Retry later if Yahoo Finance is rate-limiting.</p>
          </div>
          <div>
            <p className="font-medium text-amber-400">Blank holdings</p>
            <p className="text-neutral-400">Old blank holdings from previous versions can be cleared using Settings → Reset App Data.</p>
          </div>
          <div>
            <p className="font-medium text-amber-400">No Top 30 loaded</p>
            <p className="text-neutral-400">Go to the Top 30 page and click Load Notebook-Generated Top 30. Upload a valid CSV with the required columns.</p>
          </div>
          <div>
            <p className="font-medium text-amber-400">Reset failed</p>
            <p className="text-neutral-400">Ensure you are the owner (OWNER_EMAIL environment variable). Check that SUPABASE_SERVICE_ROLE_KEY is configured.</p>
          </div>
        </div>
      </section>
