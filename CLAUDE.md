# CLAUDE.md

Guidance for Claude Code sessions in this repository.

## What this repo is

The **reasoning-graph framework**: declared, confidence-weighted reasoning graphs — reasoning retrieved by traversal instead of re-derived in prose, with a mechanized mint→verify→freeze→retire loop. Corpus-agnostic core (`reasoning_graph/`); the claude-code-tools corpus at `/root/reasoning-graph` is **instance 0** and is never edited from here except through `migrate` / `loop freeze` / `loop retire`.

**Read first:** `Reasoning-Graph-source-of-truth-2026-07-19.ngf.md` (the build contract), then `gates/run_all.py`.

## Commands

- `pip install -e . --break-system-packages` — editable install (zero required deps; numpy is an optional `[analytics]` booster).
- `reasoning-graph --help` — full subcommand tree; every subcommand supports `--json`.
- `python3 gates/run_all.py` — the gate harness. Exit codes: 0 PASS · 1 FAIL · 2 NOT-BUILT · 4 TAMPER · 5 INFRA-FLAKE. **Gates, not narration, decide "done."**
- `pytest -q` — the test suite (1:1 with `tests/INVARIANTS.md`).
- `python3 -m reasoning_graph.demo` — deterministic demo; ends `Verify your build: ok`.

## Load-bearing invariants (1:1 with tests/INVARIANTS.md)

1. No corpus vocabulary hardcoded in `reasoning_graph/` core — kinds arrive only via `GraphSchema` (the tiny non-default-named fixture proves it).
2. Missing/NULL edge confidence raises `MissingConfidence` → REFUSE; never a silent 1.0.
3. Every confidence carries a closed-vocabulary basis (`declared:*` / `derived:*`).
4. Path confidence is `path_product_score` — a score, not a probability.
5. Unminted edges are never inferred; a miss REFUSEs and drafts an FCL stub.
6. Contradiction refusal fires only through `cycle_class='contradiction'` edges.
7. Promotion needs declared `gap_shape` recurrence ≥ threshold; disposed classes are never re-proposed.
8. Freeze is idempotent on `synthesis_chain`.
9. Retirement demotes to dormant with evidence — never deletes.
10. numpy absent → pagerank output byte-identical.
11. Unknown node/edge kind raises — never coerced.
12. `GraphSchema.validate()` enforces the structural rules.

## What NOT to do

- Do NOT rebuild or "improve" P0–P2 in instance 0 (the graph, nai read side, query.py) — G0 breakage is a failed session.
- Do NOT edit `gates/**` (tamper-manifested + git-anchored) or the frozen instance-0 files.
- Do NOT infer edges: unminted = dropped; a miss drafts an FCL stub.
- Do NOT default a missing confidence to anything. Refuse.
- Do NOT present path confidence as a probability, or any number as measured except A/B api-usage tokens.
- Do NOT add learned/opaque ranking signals — declared > inferred is the thesis.
- Do NOT resolve the SoT's §13 open questions — log an FCL entry and continue.
