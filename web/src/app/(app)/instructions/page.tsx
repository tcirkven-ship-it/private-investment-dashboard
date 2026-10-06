export default function InstructionsPage() {
  return (
    <div className="space-y-10 max-w-3xl">
      <h1 className="text-2xl font-semibold">Instructions</h1>

      <section>
        <h2 className="text-lg font-semibold mb-4">Quarterly Review</h2>
        <ol className="space-y-3 text-sm text-neutral-300 list-decimal list-inside">
          <li>Wait for the final trading session of the quarter to close.</li>
          <li>Double-click <strong>Run Quarterly Top30 Generator.command</strong> in the project folder.</li>
          <li>Confirm the quarter-end date (defaults to last day of previous quarter).</li>
          <li>Wait for generation to complete (opens output folder automatically).</li>
          <li>Open the app → Top 30 → Load Notebook-Generated Top 30.</li>
          <li>Select <code className="text-xs bg-neutral-800 px-1 py-0.5 rounded">m1_b2_quality_veto_targets.csv</code> from the output folder.</li>
          <li>Confirm 30 holdings with B2 scores and Quality percentiles are visible.</li>
          <li>Go to Compare to see Keep / Consider Buying / Consider Selling.</li>
          <li>Make manual buy/sell decisions at your brokerage. The app does not execute trades.</li>
        </ol>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Portfolio — Add / Edit / Delete Holdings</h2>
        <ul className="space-y-2 text-sm text-neutral-300 list-disc list-inside">
          <li><strong>Add Holding</strong>: Enter ticker, shares, and average cost. Click Add.</li>
          <li><strong>Edit Holding</strong>: Click the edit icon next to a holding. Update shares or average cost. Save.</li>
          <li><strong>Delete Holding</strong>: Click the delete icon, then confirm.</li>
          <li>You cannot add a ticker already in your portfolio. Edit the existing holding instead.</li>
          <li>Blank tickers are not allowed. Shares must be greater than zero.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Price Refresh</h2>
        <ul className="space-y-2 text-sm text-neutral-300 list-disc list-inside">
          <li>Click <strong>Refresh Current Prices</strong> on the Portfolio page.</li>
          <li>Only tickers currently in your portfolio are refreshed.</li>
          <li>The result shows how many succeeded and which tickers failed.</li>
          <li>Prices are latest available quotes from Yahoo Finance and may be delayed.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Required CSV Columns</h2>
        <p className="text-sm text-neutral-400 mb-3">The generator CSV must include these columns:</p>
        <ul className="space-y-1 text-sm text-neutral-400 list-disc list-inside">
          <li><code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">model_id</code> — must be M1_B2_QUALITY_VETO_N30</li>
          <li><code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">quarter_label</code> — e.g. 2026-Q2</li>
          <li><code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">as_of_date</code> — quarter-end market date</li>
          <li><code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">generated_at</code> — when the CSV was created</li>
          <li><code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">source</code> — offline notebook official generator</li>
          <li><code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">rank</code> — 1-30 position</li>
          <li><code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">ticker</code> — required</li>
          <li><code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">company</code> — optional (ticker-only display if missing)</li>
          <li><code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">sector</code> — required</li>
          <li><code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">industry</code> — required</li>
          <li><code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">B2_score</code> — required (rejected if missing)</li>
          <li><code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">Q_score</code> or <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">Q_percentile</code> — required</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Date Meanings</h2>
        <div className="space-y-3 text-sm text-neutral-300">
          <div><p className="font-medium text-neutral-200">as_of_date</p><p className="text-neutral-400">The market data date / quarter-end date.</p></div>
          <div><p className="font-medium text-neutral-200">generated_at</p><p className="text-neutral-400">When the notebook generated the CSV.</p></div>
          <div><p className="font-medium text-neutral-200">loaded_at</p><p className="text-neutral-400">When the app loaded the CSV. Set by the app at import time.</p></div>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Compare</h2>
        <ul className="space-y-2 text-sm text-neutral-300 list-disc list-inside">
          <li><strong>Already Own / In Top 30</strong>: Stocks you hold that are in the Top 30.</li>
          <li><strong>Consider Buying</strong>: Top 30 stocks you do not currently own.</li>
          <li><strong>Consider Selling</strong>: Stocks you own that are not in the Top 30.</li>
          <li>All decisions are manual. The app does not trade or connect to a broker.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Reset App Data</h2>
        <ul className="space-y-2 text-sm text-neutral-300 list-disc list-inside">
          <li>Go to <strong>Settings</strong> to reset all app data.</li>
          <li>Click <strong>Reset App Data</strong>, review row counts, type RESET to confirm.</li>
          <li>Clears portfolios, transactions, model snapshots, prices, and decisions.</li>
          <li>Supabase auth users and migrations are never touched.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Manual Decisions</h2>
        <ul className="space-y-2 text-sm text-neutral-300 list-disc list-inside">
          <li>The app does <strong>not</strong> trade, execute orders, or connect to any broker.</li>
          <li>All buy/sell decisions are made and executed manually by you at your brokerage.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Investment Strategy</h2>

        <div className="space-y-4 text-sm text-neutral-300">
          <div>
            <p className="font-medium text-neutral-200 mb-1">Model</p>
            <p className="text-neutral-400">
              The model used is <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded">M1_B2_QUALITY_VETO_N30</code>.
              It selects 30 stocks, targeting equal weight across the selected names.
              The app does not execute trades or force position sizes.
            </p>
          </div>

          <div>
            <p className="font-medium text-neutral-200 mb-1">Rebalance schedule</p>
            <p className="text-neutral-400">
              The official review is quarterly, using the final market session of March, June, September, and December.
              The model should use quarter-end closing data. Mid-quarter snapshots can be loaded for research or comparison,
              but the official workflow is quarterly.
            </p>
          </div>

          <div>
            <p className="font-medium text-neutral-200 mb-1">Ranking — B2 price score</p>
            <p className="text-neutral-400">
              Stocks are ranked by the B2 price-strength/trend score, based on
              <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded mx-1">M12_1</code>
              <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded mx-1">M6_1</code>
              <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded mx-1">TREND200</code>.
              Higher B2 score is better.
            </p>
          </div>

          <div>
            <p className="font-medium text-neutral-200 mb-1">Quality veto</p>
            <p className="text-neutral-400">
              Before final selection, the bottom 10% of stocks by quality are excluded.
              Quality is based on
              <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded mx-1">ROA</code>
              <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded mx-1">GPA</code>
              <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded mx-1">FCF_MARGIN</code>
              <code className="text-xs bg-neutral-800 px-1.5 py-0.5 rounded mx-1">DEBT_ASSETS</code>.
            </p>
          </div>

          <div>
            <p className="font-medium text-neutral-200 mb-1">Concentration caps</p>
            <p className="text-neutral-400">
              The final 30-stock list applies concentration controls: sector cap at 25%, industry cap at 15%.
              For 30 names this means approximately max 7 names per sector and max 4 names per industry.
            </p>
          </div>

          <div>
            <p className="font-medium text-neutral-200 mb-1">Selection criteria</p>
            <p className="text-neutral-400">
              A stock can enter the Top 30 if: it is in the eligible scored universe; required B2 and quality
              factors are present; it passes the bottom 10% quality veto; it ranks high enough by B2 score;
              and sector/industry caps allow it.
            </p>
          </div>

          <div>
            <p className="font-medium text-neutral-200 mb-1">Buy / Hold / Sell interpretation</p>
            <div className="space-y-1.5 text-neutral-400 mt-1">
              <div><span className="font-medium text-green-400">Already Own / In Top 30</span> — stocks you hold that are in the current Top 30 snapshot.</div>
              <div><span className="font-medium text-blue-400">New in Top 30 / Consider Buying</span> — Top 30 stocks you do not currently own.</div>
              <div><span className="font-medium text-red-400">Owned but Not in Top 30 / Consider Selling</span> — stocks you own that are not in the current snapshot. This is not an automatic sell order; all decisions are manual.</div>
            </div>
          </div>

          <div>
            <p className="font-medium text-neutral-200 mb-1">Snapshots</p>
            <p className="text-neutral-400">
              Each loaded CSV creates a separate model snapshot. The latest snapshot is used by default.
              Historical snapshots can be selected on Top 30 and Compare via the dropdown selector.
              Loading a new snapshot does not delete old snapshots or change portfolio holdings.
            </p>
          </div>

          <div>
            <p className="font-medium text-neutral-200 mb-1">Important</p>
            <p className="text-neutral-400">
              This app is a decision-support tool. It does not place trades, connect to a broker,
              provide financial advice, guarantee performance, or automatically rebalance.
              All trades are manual. Historical performance does not guarantee future results.
            </p>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Troubleshooting</h2>
        <div className="space-y-3 text-sm">
          <div><p className="font-medium text-amber-400">Scores missing in Top 30</p><p className="text-neutral-400">Re-upload the CSV with B2_score and Q_percentile columns.</p></div>
          <div><p className="font-medium text-amber-400">Price refresh failed</p><p className="text-neutral-400">Some tickers may not have quotes. Retry later.</p></div>
          <div><p className="font-medium text-amber-400">Blank holdings</p><p className="text-neutral-400">Clear old data via Settings → Reset App Data.</p></div>
          <div><p className="font-medium text-amber-400">No Top 30 loaded</p><p className="text-neutral-400">Go to Top 30 → Load Notebook-Generated Top 30.</p></div>
          <div><p className="font-medium text-amber-400">Reset failed</p><p className="text-neutral-400">Ensure OWNER_EMAIL and SUPABASE_SERVICE_ROLE_KEY are configured.</p></div>
        </div>
      </section>
    </div>
  );
}
