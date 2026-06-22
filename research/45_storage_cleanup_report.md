# Pre-activation storage cleanup

## Decision

Cleanup passed. The project remains reconstructable and activation-ready. The deletion gate was not opened until the full Checkpoint 2 content-addressed archive had reproduced all 20,518 logical files and matched every original checksum.

## Inventory and recovery

The machine-readable inventories count file bytes rather than filesystem allocation.

| Scope | Before bytes | After bytes | Change |
|---|---:|---:|---:|
| Entire project | 1,639,403,094 | 567,973,808 | -1,071,429,286 |
| `.git` | 3,687,411 | 8,199,534 | +4,512,123 |
| `.venv` | 229,517,404 | 229,517,404 | 0 |
| `data` | 1,241,164,374 | 295,222,414 | -945,941,960 |
| `outputs` | 163,958,301 | 34,341,056 | -129,617,245 |
| `research` | 339,345 | 327,053 | -12,292 |
| `src` | 591,830 | 274,727 | -317,103 |
| `tests` | 57,816 | 17,299 | -40,517 |

The allowlisted deletion operation removed 1,100,381,776 bytes across 22,973 file/symlink manifest rows. The net inventory reduction is smaller because Git metadata and cleanup evidence were created during the operation.

## Dependency classification

Retained as active dependencies:

- frozen simplified configuration, factor/alias definitions, source, tests and environment lock;
- the Checkpoint 2 CAS manifest and all 17,616 referenced gzip objects;
- the compact logical snapshot manifest and compact EXP-0014 score/semantic outputs;
- the latest deterministic simplified rehearsal;
- all Git-tracked research and governance history.

Retained as uncertain:

- `.venv`, because it is the currently tested environment;
- older Phase 1A yfinance, FRED and universe inputs, because audit reconstruction still refers to them.

Deleted as superseded, duplicated or safely generated:

- the 790.78 MB uncompressed Checkpoint 2 snapshot after full CAS reconstruction;
- the earlier 110-name yfinance capability raw sample, while retaining its manifest and compact results;
- superseded Checkpoint 3 intraday/smoke-test data and execution-heavy rehearsals;
- EXP-0014's regenerable 147 MB factor-level intermediate table;
- the first of two byte-identical simplified rehearsal directories;
- provider caches, Python caches, editor/macOS temporary files and related generated material.

Exact file-level decisions are in `outputs/storage_cleanup/deletion_manifest.csv`; retained dependencies and classifications are in `retained_dependencies.csv`.

## Content-addressed archive validation

- Logical files: 20,518.
- Unique referenced objects: 17,616.
- Objects present before cleanup: 17,616.
- Missing, corrupt or checksum-failing objects: 0.
- Original logical files checksum-compared: 20,518; failures: 0.
- Orphan objects: 0; orphan bytes: 0.
- Full pre-deletion reconstruction: PASS.
- Full post-deletion reconstruction from retained CAS only: PASS.

The canonical raw snapshot is therefore the CAS representation; retaining the uncompressed duplicate was unnecessary.

## Post-cleanup reconstruction and tests

The reconstructed snapshot produced 698 eligible companies and byte-identical versions of all six selected frozen evidence outputs: candidate composites, category scores, Checkpoint 2 metrics, primary factor sets, factor admission and semantic reconciliation summary.

The repository's original 44-test `unittest` suite passed immediately after deletion. After adding four tests for the required contribution-event mechanism, all 48 tests passed. Two new simplified daily rehearsals were also byte-identical with tree SHA-256 `34779f95136080d2fbfdf3a008b8ddfe08888ef2e1ed67dc4d86d51b1da5ecc4`; benchmark cash-flow parity passed and both states had SHA-256 `58582388d5164e4fa7e076331d0e846b39b55f8f281866f56f9054596017626d`.

All tracked files remain intact. No retained active manifest points to a missing CAS object. Activation readiness remains PASS.
