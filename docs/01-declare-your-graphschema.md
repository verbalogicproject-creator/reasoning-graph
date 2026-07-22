# 01 — Declare your GraphSchema

`GraphSchema` is the one declaration object (`reasoning_graph/schema.py`):

- `node_kinds`: the stored noun types.
- `edge_kinds`: each an `EdgeKind(name, ConfidenceRule, symmetric, cycle_class)`.
- `profile`: the `Profile` mapping table/column names (defaults match instance 0; the tiny fixture overrides every field).
- `floor` (default 0.30): sub-floor paths are `WEAK_ANSWER`.
- `promotion_threshold` (default 2): recurrence needed to promote a gap-shape.
- `retirement`: `RetirementPolicy(active_cap, min_uses, contradiction_ratio)`.

A `ConfidenceRule` carries a closed-vocabulary `basis` and either a declared `value` or a derivation note. `validate()` is pure-python (unique kinds, floor in (0,1), threshold ≥ 2 unless `allow_single_occurrence_promotion`). `edge_kind()` raises on an undeclared kind — silent mis-typing is worse than an error. See `instances/claude_code_tools/graphschema.py` (13 node kinds, 24 edge kinds) and `tests/fixtures/tiny/graphschema.py` (an alien weaving domain proving nothing is hardcoded).
