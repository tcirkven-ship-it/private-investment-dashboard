-- Migration 00005: Allow owner to manage model objects
-- Model versions, snapshots, and holdings need owner-write access
-- for the Generate/Refresh Quarterly Top 30 workflow.

-- Model versions: owner can insert
CREATE POLICY "Owner can insert model versions" ON public.model_versions
  FOR INSERT WITH CHECK (public.is_owner());

-- Model snapshots: owner can insert and update
CREATE POLICY "Owner can insert model snapshots" ON public.model_snapshots
  FOR INSERT WITH CHECK (public.is_owner());
CREATE POLICY "Owner can update model snapshots" ON public.model_snapshots
  FOR UPDATE USING (public.is_owner());

-- Model snapshot holdings: owner can insert
CREATE POLICY "Owner can insert snapshot holdings" ON public.model_snapshot_holdings
  FOR INSERT WITH CHECK (public.is_owner());

-- Securities: owner can insert (needed to create new tickers during model generation)
CREATE POLICY "Owner can insert securities" ON public.securities
  FOR INSERT WITH CHECK (public.is_owner());
CREATE POLICY "Owner can update securities" ON public.securities
  FOR UPDATE USING (public.is_owner());
