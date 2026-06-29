-- Migration 00006: Allow owner to manage price observations
-- Required for the manual price entry feature on the holdings page.

-- Allow owner to insert and update price observations
CREATE POLICY "Owner can insert price observations" ON public.price_observations
  FOR INSERT WITH CHECK (public.is_owner());
CREATE POLICY "Owner can update price observations" ON public.price_observations
  FOR UPDATE USING (public.is_owner());
