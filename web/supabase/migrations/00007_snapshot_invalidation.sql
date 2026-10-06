-- Migration 00007: Snapshot invalidation support + data fix for the stale-source 2026-Q3 snapshot.
--
-- Context:
--   The app snapshot nb-muwq0av2 (2026-Q3) was loaded from export
--   2026-Q3_asof-2026-09-30_generated-2026-10-06_1328 (csv_sha256 649b271c826f), which had been
--   built from the stale source_snapshot_id 2026-07-01T053352Z (July data) relabeled as 2026-Q3.
--   It is superseded by export 2026-Q3_asof-2026-09-30_generated-2026-10-06_1724
--   (csv_sha256 bb5f7ce025b4, source_snapshot_id 2026-10-06T142958Z).
--
-- Problem fixed:
--   The previous trigger blocked every UPDATE of PUBLISHED snapshots, so a published snapshot could
--   never be marked SUPERSEDED even though the transition table allows it. This migration rewrites
--   the trigger so that PUBLISHED -> SUPERSEDED is possible while all content columns stay immutable,
--   and it marks the invalid snapshot with an auditable reason.

-- ============================================================
-- 1. Replace the snapshot status transition trigger function
-- ============================================================
CREATE OR REPLACE FUNCTION public.check_snapshot_status_transition()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF OLD.status = 'SUPERSEDED' THEN
    RAISE EXCEPTION 'Superseded snapshots are immutable';
  END IF;

  IF OLD.status = 'PUBLISHED' THEN
    -- Content columns may never change on a published snapshot.
    IF (NEW.model_version_id, NEW.snapshot_id, NEW.effective_date, NEW.decision_timestamp,
        NEW.execution_convention, NEW.universe_screened, NEW.eligible_count, NEW.valid_score_count,
        NEW.integrity_hash, NEW.source_commit, NEW.created_at, NEW.published_at)
       IS DISTINCT FROM
       (OLD.model_version_id, OLD.snapshot_id, OLD.effective_date, OLD.decision_timestamp,
        OLD.execution_convention, OLD.universe_screened, OLD.eligible_count, OLD.valid_score_count,
        OLD.integrity_hash, OLD.source_commit, OLD.created_at, OLD.published_at)
    THEN
      RAISE EXCEPTION 'Published snapshots are immutable';
    END IF;

    IF NEW.status = 'PUBLISHED' THEN
      RETURN NEW;
    ELSIF NEW.status = 'SUPERSEDED' THEN
      NEW.superseded_at = COALESCE(NEW.superseded_at, now());
      RETURN NEW;
    ELSE
      RAISE EXCEPTION 'Only PUBLISHED can become SUPERSEDED';
    END IF;
  END IF;

  -- Existing draft lifecycle rules (unchanged)
  IF NEW.status = 'VALIDATED' AND OLD.status != 'DRAFT' THEN
    RAISE EXCEPTION 'Only DRAFT can become VALIDATED';
  END IF;
  IF NEW.status = 'APPROVED' AND OLD.status != 'VALIDATED' THEN
    RAISE EXCEPTION 'Only VALIDATED can become APPROVED';
  END IF;
  IF NEW.status = 'PUBLISHED' AND OLD.status != 'APPROVED' THEN
    RAISE EXCEPTION 'Only APPROVED can become PUBLISHED';
  END IF;
  IF NEW.status = 'SUPERSEDED' AND OLD.status != 'APPROVED' THEN
    RAISE EXCEPTION 'Only PUBLISHED or APPROVED can become SUPERSEDED';
  END IF;
  IF NEW.status = 'PUBLISHED' THEN
    NEW.published_at = now();
  END IF;
  RETURN NEW;
END;
$$;

-- ============================================================
-- 2. Reusable, owner-only invalidation function
--    Usage (SQL editor or service role):
--      SELECT public.invalidate_model_snapshot('nb-xxxx', 'reason text');
-- ============================================================
CREATE OR REPLACE FUNCTION public.invalidate_model_snapshot(p_app_snapshot_id text, p_reason text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  UPDATE public.model_snapshots
  SET status = 'SUPERSEDED',
      superseded_at = now(),
      warnings = COALESCE(warnings, '{}'::jsonb) || jsonb_build_object(
        'invalidated', true,
        'invalidated_at', now(),
        'invalidation_reason', p_reason
      )
  WHERE snapshot_id = p_app_snapshot_id
    AND status = 'PUBLISHED';

  IF NOT FOUND THEN
    RAISE EXCEPTION 'No PUBLISHED snapshot found with app snapshot_id %', p_app_snapshot_id;
  END IF;
END;
$$;

REVOKE ALL ON FUNCTION public.invalidate_model_snapshot(text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.invalidate_model_snapshot(text, text) TO service_role;

-- ============================================================
-- 3. Data fix: invalidate the stale-source 2026-Q3 snapshot (idempotent)
-- ============================================================
UPDATE public.model_snapshots
SET status = 'SUPERSEDED',
    superseded_at = now(),
    warnings = COALESCE(warnings, '{}'::jsonb) || jsonb_build_object(
      'invalidated', true,
      'invalidated_at', now(),
      'invalidation_reason', 'Invalidated 2026-10-06: built from stale source_snapshot_id 2026-07-01T053352Z (July data) relabeled as 2026-Q3 / as_of 2026-09-30. csv_sha256=649b271c826f. Superseded by export 2026-Q3_asof-2026-09-30_generated-2026-10-06_1724 (csv_sha256=bb5f7ce025b4, source_snapshot_id=2026-10-06T142958Z).'
    )
WHERE snapshot_id = 'nb-muwq0av2'
  AND status = 'PUBLISHED'
  AND warnings->>'quarter_label' = '2026-Q3'
  AND warnings->>'generated_at' LIKE '2026-10-06T13:28%';
