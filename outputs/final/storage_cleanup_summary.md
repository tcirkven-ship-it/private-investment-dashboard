# Storage cleanup summary

**Result:** PASS — safe cleanup completed and activation readiness preserved.

- File bytes before: 1,639,403,094 (1.639 GB).
- File bytes after: 567,973,808 (0.568 GB).
- Net space recovered: 1,071,429,286 bytes (1.071 GB; 65.35%).
- CAS validation: 20,518/20,518 logical files and 17,616/17,616 unique objects passed; zero orphans.
- Frozen score reproduction: six of six selected outputs byte-identical.
- Tests after cleanup: 48 passed, zero failures/errors (44 pre-existing plus four contribution-ledger tests).
- Simplified rehearsals after cleanup: two runs, byte-identical, benchmark parity passed.

The raw Checkpoint 2 duplicate, superseded intraday/execution artifacts, repeated intermediates and caches were removed. The canonical CAS, compact audit evidence, active environment and uncertain historical dependencies were retained.
