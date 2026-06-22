# Superseded invalid current output

## Root cause

The four files under `mechanics_smoke_2/` are invalid as current reset evidence.

The mechanics command explicitly supplied `/tmp/yf_checkpoint2_post_cleanup` to `src.daily_screen`. That path was a reconstruction of the old Checkpoint 2 raw snapshot. The scanner recalculated factors from that cached 698-name `base_eligible_universe.csv`, then its unconditional compact-publication block copied the smoke report, ranking and portfolio into `outputs/final/`.

Therefore the files were not copied from an old report and were not produced by a fresh run that discarded 374 names. They were generated anew from the cached old 698-name snapshot, and then wrongly published because the scanner lacked a rehearsal/source-age publication guard.

## Preserved invalid files

| File | SHA-256 |
|---|---|
| `current_daily_qvp_ranking.csv` | `597ea85bc3f5f7b21fee5ed9fe2495b115d92233b4aa1fca01ac1f417cf37702` |
| `current_daily_qvp_portfolio.csv` | `013a0bc91e46014319137759eb890c280b9ea1275ba8ccd708f4f41772eae658` |
| `current_daily_qvp_report.md` | `bd9b536d5841fd1a66fe077661f55ef57b122b35a732357ee1b2392da9d36601` |
| `current_daily_qvp_report.html` | `36424250e3d74170bd5a8284d7bbb6d5731f8f46b94e4036641f2d9a06af57e6` |

They must never be restored as compact current outputs or used for current decisions.
