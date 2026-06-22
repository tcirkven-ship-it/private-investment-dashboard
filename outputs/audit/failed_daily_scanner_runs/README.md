# Failed daily scanner runs

These directories are retained only as audit evidence and are not publishable
current outputs.

- `2026-06-22T160222Z` stopped during fresh retrieval after a network/DNS
  failure and contains no output files.
- `2026-06-22T160715Z` completed fresh retrieval and scoring, but publication
  stopped when duplicate provenance-column insertion raised an error. It has
  no passing run manifest or compact report. The metadata writer was fixed and
  covered by regression test before the successful replacement run.

Neither directory may be used as a prior valid ranking. The scanner accepts a
previous ranking for change comparison only when its manifest classification
is `current_decision_support_integrity_passed`.
