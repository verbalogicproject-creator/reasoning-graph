# 06 — The frontier-call rate

The framework-health metric (`measure/frontier_rate.py`): the count of newly-promoted gap-shape classes per N logged frontier calls. As reasoning migrates model→graph, the rate falls — new misses re-instance existing classes instead of minting new ones.

`compute()` returns a per-entry series (cumulative distinct classes, `is_new_class`) in chronological order, plus per-batch rates from the log's own organic-batch markers, plus a baseline and an honest one-sentence reading. Every number is `derived:fcl_log_parse`. On instance 0's live log the rate is 0.41 → 0.08 across the two organic batches (falling) — but at 2 batches / 48 queries that is a direction, not a proven trend, and the reading says so.
