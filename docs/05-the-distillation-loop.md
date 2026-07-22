# 05 — The distillation loop (mint → verify → freeze → retire)

What "mechanized" means: the *administration* is code; the *judgment* (what counts as the same gap) stays a human-declared `gap_shape`.

- **scan** (`loop/fcl.py`) parses the frontier-call log's schema (tolerant of the historical compound status tags), pulling `gap_shape`/occurrences from the declared sidecar or inline field.
- **promote** (`loop/promote.py`) flags gap-shapes recurring ≥ `promotion_threshold` and not already disposed. On instance 0 it reproduces history exactly: recurring `{FCL-001,007,008,009}`, promotable `{}` (all disposed — FCL-008's rejection respected, never re-proposed).
- **mint** stages a matcher-v2 file (human sections + a machine-checkable ```yaml block).
- **verify** runs the matcher's `signature_sql` and `confirm` predicates and requires the matcher to fire against ≥ 1 of its own originating entries (no unreproduced rule).
- **freeze** writes the confirmed edges (+ `synthesis_chain` provenance + fact-loop rows + outcome counters), idempotently; requires `--approve` on a real instance.
- **retire** (`loop/retire.py`) demotes minted rules to *dormant* on outcome evidence (contradiction-ratio first, then a bounded active cap) — **never deletes**; dormant edges are excluded from `resolve`.
