# CONTRIBUTING

<!-- OPUS-FILLS to the house bar. Required content: -->

- Invariants live in `tests/INVARIANTS.md`, 1:1 with named tests — a change that breaks an invariant needs the invariant's line changed in the same commit, with grounds.
- `gates/**` is immutable except by the repo owner; `MANIFEST-GATES.sha256` guards it.
- Retrieval/traversal math changes belong in `reasoning_graph/` core; instance vocabulary never does (G1 enforces).
- Every confidence number added anywhere must carry a closed-vocabulary basis label.
