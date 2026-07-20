# CLAUDE.md

This file guides Claude Code sessions working in this repository.

## What this repo is

The **reasoning-graph framework**: declared, confidence-weighted reasoning graphs — reasoning retrieved by traversal instead of re-derived in prose, with a mechanized mint→verify→freeze loop for what the graph can't yet answer. Corpus-agnostic core; the claude-code-tools corpus at `/root/reasoning-graph` is **instance 0** and is NEVER edited from here (its DB is written only through this package's `migrate` and `loop freeze` commands).

**Read first, in order:** `Reasoning-Graph-source-of-truth-2026-07-19.ngf.md` (the build contract — decisions locked, phase plan, gate contract), then `gates/run_all.py --help`.

## Commands

- `pip install -e .` — editable install (zero required deps).
- `reasoning-graph --help` — full subcommand tree; every subcommand supports `--json`.
- `python3 gates/run_all.py` — the gate harness; exit codes per gate: 0 PASS, 1 FAIL, 2 NOT-BUILT. **Gates, not narration, decide "done."**
- `pytest -q` — test suite.
- `python3 -m reasoning_graph.demo` — deterministic demo; must end `Verify your build: ok`.

## Load-bearing invariants

<!-- OPUS-FILLS: keep this list 1:1 with tests/INVARIANTS.md; every invariant names its test. Seed list: -->
1. No hardcoded corpus vocabulary in `reasoning_graph/` core — node/edge kinds arrive only via `GraphSchema` (G1 greps for instance tokens; the tiny fixture uses non-default table/column names).
2. NULL/missing edge confidence → `MissingConfidence` → REFUSE. Never a silent 1.0.
3. Every confidence value carries a `confidence_basis` from the closed vocabulary (`declared:*` / `derived:*`). Nothing is presented as measured except API-usage token counts in the A/B harness.
4. Path confidence is `confidence_kind: path_product_score` — a ranking score, not a probability.
5. Unminted edges are dropped, never inferred. A traversal miss drafts an FCL stub; it does not guess.
6. Promotion to mint candidate requires `gap_shape` recurrence ≥ `promotion_threshold` (declared field, never NLP-inferred similarity).
7. Freeze is idempotent (keyed on `synthesis_chain`); re-running inserts 0.
8. Minted rules carry outcome counters; retirement demotes to `dormant` with evidence — never deletes.
9. The numpy `[analytics]` booster degrades byte-identically when absent (named test).
10. Instance-0 frozen files (`query.py`, `systems/nai/**`, fixtures) are never edited; G0's hash manifest enforces this.

## What NOT to do

- Do NOT rebuild P0–P2 (the graph, the nai read side, query.py) — they exist and are verified; see the SoT's "P0–P2 EXIST" section.
- Do NOT edit `gates/**` — `MANIFEST-GATES.sha256` makes tampering visible; the human re-running `run_all.py` is the final arbiter.
- Do NOT add a learned/opaque ranking signal — declared > inferred is the thesis this library demonstrates.
- Do NOT resolve open questions listed in the SoT — log an FCL entry and continue.
- Do NOT claim a feature in README that isn't proven by a runnable example or named test — put it in ROADMAP.md.
