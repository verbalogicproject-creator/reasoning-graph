# reasoning-graph

> **Graph = frozen reasoning.** Pay inference once to declare an edge, then retrieve it forever by traversal. Multi-step reasoning becomes path-finding; what the graph can't answer becomes a logged *frontier call* that feeds a mint→verify→freeze→retire loop. This is rung-0 of the lowering ladder applied to reasoning itself.

![tests](https://img.shields.io/badge/tests-40_passing-brightgreen) ![deps](https://img.shields.io/badge/required_deps-0-blue) ![gates](https://img.shields.io/badge/gates-G0..G8_green-brightgreen)

Declared, confidence-weighted reasoning graphs — reasoning retrieved by traversal instead of re-derived in prose, and *honest about the edges of its own competence* (it refuses what its frozen edges don't support). Corpus-agnostic core; ships with `claude-code-tools` as instance 0.

## The 60-second quickstart

```bash
pip install -e . --break-system-packages -q
reasoning-graph schema validate --instance instances/claude_code_tools/instance.json --json
python3 -m reasoning_graph.demo
```

The demo builds a small declared graph, migrates confidence onto its edges, and shows the three honest outcomes — an `ANSWER` that composes to a confidence product, a sub-floor `WEAK_ANSWER` (not hidden), and a `REFUSE(contradiction)` — ending with `Verify your build: ok`.

## What this is

A knowledge graph is reasoning done once: you pay inference to declare a confidence-weighted edge, then look it up by traversal instead of re-deriving it every call. `resolve()` returns an `ANSWER` / `WEAK_ANSWER` / `REFUSE` — refusal is a first-class result, not an error, because a reasoning graph that answers everything is lying about something. Misses become logged frontier calls; a mechanized loop mints, verifies, freezes, and (on evidence) retires rules. Every confidence carries a closed-vocabulary basis (`declared:*` / `derived:*`); nothing is ever presented as measured except A/B API-usage tokens.

## How it fits together

```
GraphSchema (declare: node/edge kinds, confidence rules, floor, retirement)
      │  everything below is derived from it — zero hardcoded corpus vocabulary
      ▼
store.py ──► migrations.py (m001: additive confidence column, per-class backfill)
      │
      ▼
resolver.py + refusal.py ──► Answer{status, path, confidence, path_class, refusal}
      │
      ▼
loop/ : scan → promote (recurrence gate) → mint → verify → freeze → retire
      │
      ▼
measure/ : frontier_rate (health)  +  ab_* (the A/B proof: tokens + accuracy)
```

## Design choices

- **declared > inferred.** A learned or opaque ranking signal is a *bug*, not a feature — the thesis is that declared structure replaces re-derivation.
- **Missing confidence refuses.** A NULL edge weight is never silently treated as 1.0 (the behavior this framework exists to kill).
- **Path confidence is a score, not a probability.** `confidence_kind: path_product_score` — an honest ranking number (arXiv:2601.11956), and `path_class` discloses a structural fact-walk vs a reasoning composition.
- **Cycles ≠ contradictions.** Only `cycle_class='contradiction'` edges refuse; benign reciprocal cycles are data.
- **Retirement, not unbounded growth.** Minted rules carry outcome counters and demote to *dormant* (never deleted) — unmanaged rule libraries degrade below baseline at scale (arXiv:2605.13716).

## Reading paths

- **User (~15 min):** `docs/00-mental-model.md` → `docs/01-declare-your-graphschema.md` → `docs/09-cli-reference.md`.
- **Integrator (~20 min):** `docs/08-api-reference.md` → `docs/10-claude-code-mcp.md` → `examples/`.
- **Contributor:** `CODEBASE-REPORT.md` → `CONTRIBUTING.md` → `tests/INVARIANTS.md`.

## The family

A sibling of Eyal's RAG codifications (`declared_core` / `frontmatter_rag` / `project_memory`) — same house recipe (one declaration object, deterministic, offline-first, a refuses-to-pretend boundary), pointed at reasoning instead of retrieval. Instance 0's substrate lives at `/root/reasoning-graph`; this repo never edits it except through `migrate` / `loop freeze` / `loop retire`.
