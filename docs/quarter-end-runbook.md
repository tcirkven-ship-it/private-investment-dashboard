# Quarter-End Runbook — M1_B2_QUALITY_VETO_N30

## Pipeline Overview

```
Stage 1 (local/offline)          Stage 2 (cloud/GitHub Actions)
────────────────────────         ──────────────────────────────
build_m1_b2_factor_snapshot     generate_m1_b2_official
    ↓                                ↓
reads 200MB raw factor panel     reads small factor CSV
    ↓                                ↓
extracts B2 + Quality columns    applies Quality Veto + caps
    ↓                                ↓
outputs small dated CSV          produces 30 M1_B2 holdings
    ↓                                ↓
upload artifact                  write to Supabase
```

## Quarter-End Checklist

### 1. After Final Close — Stage 1 (Local)

Run the factor snapshot builder after the final trading session of March/June/September/December:

```bash
python scripts/build_m1_b2_factor_snapshot.py \
  --snapshot-id 2026-06-24T080500Z \
  --output-dir outputs/quarterly/factor_inputs
```

Output:
- `outputs/quarterly/factor_inputs/m1_b2_factor_input_YYYY-MM-DD.csv` (~260 KB)
- `outputs/quarterly/factor_inputs/m1_b2_factor_manifest_YYYY-MM-DD.json`

Commit the output files to the repository.

### 2. Stage 2 — GitHub Actions (Dry Run)

Go to Actions → Generate Official Quarterly M1_B2 Model → dry_run=true → Run.

Verify:
- Input row count: ~1070
- Quality veto applied
- 30 holdings selected
- Validation passed
- Artifacts uploaded

### 3. Stage 2 — Write Mode

Run again with dry_run=false.

This writes the validated 30 holdings to Supabase.

### 4. Refresh Prices (Vercel)

On the dashboard, click Refresh Closing Prices to fetch latest market data.

### 5. Review Rebalance

Open the Rebalance Instructions page for each portfolio.
Compare current holdings against the newly generated Top 30.
Mark decisions: Planned / Executed / Skipped / Watch / Not now.

## Manual Fallback

If GitHub Actions or the Python pipeline is unavailable:

1. The latest committed `outputs/quarterly/m1_b2_factor_input.csv` can be used directly
2. Stage 2 can run locally: `python scripts/generate_m1_b2_official.py`
3. Write to Supabase manually via the Vercel "Load Latest Generated Top 30" button

## Freshness Rules

- Factor snapshot older than 90 days → Stage 2 refuses to write
- No `generated_at` column → Stage 2 accepts but warns
- Missing B2_score or Q_score → Stage 2 fails
- Missing sector/industry → Stage 2 fails
