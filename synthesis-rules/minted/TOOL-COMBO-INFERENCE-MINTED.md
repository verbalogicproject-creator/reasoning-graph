# Tool Combo Inference — Minted Rules (P3→P4→P5 loop output)

**Status**: MINTED 2026-07-14, FROZEN 2026-07-14 (first live pass through the P3–P5 loop, per `Distillation-workflow-formalization-2026-07-14.ngf.md`)
**Provenance**: `frontier-call-log.ngf.md` entry FCL-001 — the 2 notebook tools (P0 patch, 2026-07-13) landed with zero reasoning-typed edges, because `claude-code-tools/*.json` has no field carrying `tool_requires_tool`/`tool_similar_to`/`tool_complements`/`tool_alternative_to`/`tool_conflicts_with` directly; those edge types are DB-native content for the original 12 tools, not JSON-derivable.

**Not part of the original Synthesis relic corpus** (the 8 files at `synthesis-rules/` top level, extracted from the prior "Synthesis" system, Dec 2025). This file is genuinely new, frontier-minted content produced *by this project's own loop*, kept in `synthesis-rules/minted/` specifically so it stays provenance-distinct from the pre-frozen extraction corpus — conflating the two would misrepresent P3-mint output as P0.5 extraction, exactly the mistake the P0.5 diff (`P0.5-gap-report-2026-07-13.md`) already flagged for the 92 rules with no declared `Related Rules`.

---

## mint_001: Tool-combo-derived reasoning edges (MATCHER)

**Rule ID**: mint_001_tool_combo_inference
**Category**: Mint (P3, verified + frozen at P4/P5)
**Confidence**: 0.85 — grounded in dual evidence (JSON content + structural analogy), not single-source inference
**Source**: `frontier-call-log.ngf.md` FCL-001

**Statement**: When a tool's JSON `suggested_combinations` entry (`with_tool` / `pattern` / `rationale`) can be matched to an already-frozen reasoning edge between the nearest analogous existing tool pair, mint the same edge type for the new tool — writing the edge's `properties` specifically for the new tool's actual mechanics, never copied verbatim from the anchor.

**Signature** (cheap triage — locates candidates): a tool node has `tool_has_combination` child nodes (its JSON declared `suggested_combinations`) but zero `tool_requires_tool` / `tool_similar_to` / `tool_complements` / `tool_alternative_to` / `tool_conflicts_with` edges to any other tool.

**Confirm** (anti-false-positive gate — a candidate only mints if BOTH hold):
1. The relationship is stated or clearly implied in the tool's own `suggested_combinations` / `prerequisites` / `limitations` / `metadata` text — not invented.
2. An existing frozen edge of the same type already exists between the two nearest analogous tools (e.g. `edit_file → read_file` is the anchor for `notebook_edit → notebook_read`).

**Fix**: the typed edge, `properties` JSON matching the existing corpus convention (`rationale`/`reason`, `severity` where the anchor edge has one, `ordered`/`symmetric` where applicable) — tailored, never pasted.

**Validation Formula**:
```
mint_if: has_suggested_combination(tool, target) AND exists_analogous_frozen_edge(nearest_sibling(tool), target, edge_type)
confidence = 0.85 when both grounding sources agree (held for all 11 instances below); would drop to ~0.6 if only one did — not needed here.
```

**What this rule deliberately does NOT do**: mint `tool_alternative_to` or additional `tool_conflicts_with` edges without an equally strong dual anchor — padding coverage past what's actually grounded would cross from pattern-completion into fabrication (extract-vs-decide law, datapacket §2 dot 4).

**Related Rules**: comp_001 (`TOOL-REGISTRY-SYNTHESIS-RULES.md`, general composition requirements); anchor edges listed per-instance below.

---

## Instances minted 2026-07-14 (first application of mint_001)

| # | Edge | Anchor (existing frozen edge) | Grounding in source JSON |
|---|---|---|---|
| 1 | `notebook_edit --tool_requires_tool--> notebook_read` | `edit_file → read_file` | notebook_read combo #1: "NotebookRead → NotebookEdit cells" |
| 2 | `notebook_edit --tool_similar_to--> edit_file` | `edit_file ~ write_file` | shared "modifies content in place" description |
| 3 | `notebook_read --tool_similar_to--> read_file` | (direct) | notebook_read metadata: `"tool_call_name": "Read"` |
| 4 | `notebook_edit --tool_conflicts_with--> write_file` | `edit_file ↔ write_file` | notebook_edit combo #5: "NotebookEdit fails → Write new notebook" |
| 5 | `glob_pattern_search --tool_complements--> notebook_edit` | `glob_pattern_search → edit_file` | notebook_edit combo #4: "Glob for *.ipynb → NotebookEdit" |
| 6 | `glob_pattern_search --tool_complements--> notebook_read` | `glob_pattern_search → read_file` | notebook_read combo #5: "Glob for *.ipynb → NotebookRead" |
| 7 | `grep_content_search --tool_complements--> notebook_edit` | `grep_content_search ~ edit_file` | notebook_edit combo #3: "Grep to find notebooks → NotebookEdit" |
| 8 | `grep_content_search --tool_complements--> notebook_read` | `grep_content_search → read_file` | notebook_read combo #3: "Grep for notebooks → NotebookRead" |
| 9 | `notebook_edit --tool_complements--> bash_execute` | `edit_file → bash_execute` | notebook_edit combo #2: "NotebookEdit code → Bash to test" |
| 10 | `notebook_read --tool_complements--> bash_execute` | `read_file → bash_execute` | notebook_read combo #4: "NotebookRead → Bash to execute" |
| 11 | `notebook_read --tool_complements--> write_file` | `read_file ~ write_file` | notebook_read combo #2: "NotebookRead template → Write new notebook" |

Each row's full tailored `rationale`/`reason` text lives in the DB edge's `properties` column (`kgs/reasoning-graph.db`) — this table is the provenance index, not a duplicate of the content. Written by `mint_notebook_edges.py` (scratchpad), `synthesis_chain` column tags every inserted edge `"mint_001_tool_combo_inference / FCL-001"` for traceability.

## Reuse

`mint_001` is domain-general, not notebook-specific: any future JSON-only tool patch (a tool added to `claude-code-tools/*.json` without corresponding DB-native reasoning-edge curation) is a candidate for the same signature → confirm → fix pass. Re-run it whenever P0 patches in a new tool.
