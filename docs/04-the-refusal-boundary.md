# 04 — The refusal boundary

The differentiator. A reasoning graph that answers everything is lying about something. `resolve` returns one of:

- `ANSWER` — a path exists with composed confidence ≥ floor.
- `WEAK_ANSWER` — a path exists but sub-floor. Honest, never hidden.
- `REFUSE` — with a reason: `no_frozen_support` (no path), `contradiction` (every route crosses a `cycle_class='contradiction'` edge — the pair is named), `missing_confidence` (a structural path exists but an edge lacks confidence — refuse loudly), `unminted_edge_required`, or `below_floor` (only in `--hard` mode).

Contradiction-class edges are **non-traversable for answer paths** — an assertion of incompatibility is not a reasoning step. Every REFUSE drafts a ready-to-append frontier-call-log stub (with `gap_shape` left for a human — lock #20 forbids NLP-inferring it). Refusal is a first-class result: the CLI exits 0.
