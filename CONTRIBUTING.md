# CONTRIBUTING

- **Invariants are the contract.** `tests/INVARIANTS.md` is 1:1 with `test_inv_*` tests (both directions, enforced by G8). Changing an invariant means changing its line and its test in the same commit, with grounds.
- **Core stays corpus-agnostic.** No node/edge kind, table/column name, or corpus id in `reasoning_graph/` — thread it through `GraphSchema` (G1 greps the live DB's own vocabulary against core). The `tiny` fixture uses non-default names to prove it.
- **Gates are immutable to build sessions.** `gates/**` is guarded three ways — `MANIFEST-GATES.sha256`, an external anchor under instance-0's root, and git. `run_all.py` refuses on any mismatch (exit 4). Only the repo owner edits gates.
- **Every confidence carries a closed-vocabulary basis.** New numbers are `declared:*` or `derived:*` — never presented as measured (except A/B api-usage tokens).
- **Retrieval/traversal math is core; corpus facts are instance data.** A change about BM25/Dijkstra/pagerank goes to core; a change about *what a corpus contains* goes to `instances/<name>/`.
- **Bugs found → RG-n.** Fix, add a regression test, note it in `CHANGELOG.md` under the hardening pass with an `RG-<n>` id, and put that id in the commit subject (G8 cross-checks against `git log`).
