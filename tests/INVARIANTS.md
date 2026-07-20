# INVARIANTS

One line per load-bearing invariant, 1:1 with a named test. Gate G8 cross-checks
this file against the suite: every line's test must exist and pass; every
`test_inv_*` test must appear here. Keep in lockstep with CLAUDE.md's list.

| # | Invariant | Test |
|---|---|---|
| 1 | No corpus vocabulary hardcoded in core — the tiny fixture (non-default names, alien domain) round-trips every core operation | `tests/test_schema.py::test_inv_tiny_profile_roundtrip` |
| 2 | Missing/NULL edge confidence raises MissingConfidence → REFUSE; never a silent 1.0 | `tests/test_store.py::test_inv_null_confidence_refuses` |
| 3 | Every confidence carries a closed-vocabulary basis; unknown basis raises at declaration time | `tests/test_schema.py::test_inv_closed_basis_vocabulary` |
| 4 | Path confidence reports confidence_kind=path_product_score and equals the independent product to 1e-9 | `tests/test_resolver.py::test_inv_path_product_exact` |
| 5 | Unminted edges are never inferred: a no-support resolve REFUSEs and drafts an FCL stub | `tests/test_refusal.py::test_inv_no_support_refuses_with_stub` |
| 6 | Contradiction refusal fires ONLY through cycle_class='contradiction' edges; benign reciprocal cycles never refuse | `tests/test_refusal.py::test_inv_cycle_classes` |
| 7 | Promotion requires declared gap_shape recurrence >= threshold; disposed classes are never re-proposed | `tests/test_promote.py::test_inv_recurrence_gate_and_dispositions` |
| 8 | Freeze is idempotent on synthesis_chain — second run inserts 0 | `tests/test_freeze.py::test_inv_freeze_idempotent` |
| 9 | Retirement demotes to dormant with evidence, never deletes; ratio-demotions apply before cap enforcement | `tests/test_retire.py::test_inv_demote_not_delete` |
| 10 | numpy [analytics] absent → pagerank ranked output byte-identical | `tests/test_numpy_absent_byte_identical.py::test_inv_byte_identical` |
| 11 | Unknown node/edge kind on load or write raises — never coerced | `tests/test_store.py::test_inv_unknown_kind_raises` |
| 12 | schema validate structural rules (unique kinds, floor range, threshold>=2 unless flagged) | `tests/test_schema.py::test_inv_structural_validation` |
