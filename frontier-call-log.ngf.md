---
id: frontier-call-log
kind: log
audience: engineer
status: active
owner_area: reasoning-graph
provides:
  - "The Phase-A field-capture log for this project's own instance of the Distillation workflow (Distillation-workflow-formalization-2026-07-14.ngf.md), domain = reasoning chains. Every P1/P2 frontier call (a query the frozen graph can't resolve by lookup alone) gets one entry here, under one stable schema, appended-not-rewritten."
depends_on:
  - "Distillation-workflow-formalization-2026-07-14.ngf.md — the recipe this log instantiates"
  - "implementation-plan-reasoning-graph-v2-2026-07-13.md — P3/P4/P5, which this log feeds"
graph_rag_entities:
  - distillation-workflow-formalization
  - synthesis-rules
  - COMPOSITION-VALIDATOR
safe_edit_points:
  - "Append new entries under §2 as frontier calls happen. Never rewrite or delete an entry — advance its status tag only (LOGGED -> PROMOTED -> MINTED -> FROZEN)."
last_verified: 2026-07-14
---

# Frontier-call log — reasoning-graph's Phase-A capture

## 0 · What this is

This project's own instance of the Distillation workflow
(`Distillation-workflow-formalization-2026-07-14.ngf.md`), applied to the
domain of **reasoning chains** instead of repo debug/harden. The *unit* is a
**frontier call**: any point where P1/P2 traversal misses and the model has
to reason in prose to bridge the gap. Every frontier call gets one entry
below, under the stable schema in §1.

A gap is promoted to a "recurring class" — and becomes a P3 mint candidate —
only on its **2nd** occurrence of the same gap-shape. Nothing mints off a
single instance (extract-vs-decide law, datapacket §2 dot 4). A promoted
class proceeds to P4 (a validation formula must actually fire against its
originating entries, composing with `COMPOSITION-VALIDATOR`'s rules) before
it can freeze at P5 as a new `synthesis-rules/`-shaped file with a
`Provenance:` line back to the entry IDs here.

**Frontier-call rate** (the plan's success metric) = count of newly-promoted
classes per N logged entries, read straight off this file. Graduation for a
given area follows the same signal as the Distillation doc's worked
instance: the rate drops when new entries mostly re-instance existing
classes instead of creating new ones.

## 1 · Schema

```
### <ID> — <one-line query/gap>   [LOGGED | PROMOTED | MINTED | FROZEN]
- query          (the P2 query or P1 traversal that missed)
- category       (tool-graph area it touches)
- gap            (what the frozen graph couldn't resolve by lookup)
- root_cause     (which edge/rule was missing)
- reasoning_conclusion  (what got derived in prose to answer it)
- verified_by    (the validation formula that fired — filled in at PROMOTED→MINTED)
- pattern        (the generalizable lesson → candidate synthesis-rule)
```

## 2 · Log (newest on top, append-only)

*(2026-07-14, second organic batch — 26 more queries: recurrence-checks on FCL-007/008/009 plus untested primitives [optimize_for/learn/recommend/compatible_with/debug_tool/explore_smart/roadmap] and fresh scenarios. Purpose: does dogfooding actually behave like the loop's own recurrence gate — do real gap-shapes repeat, and does a 2nd occurrence earn a fix?)*

### FCL-011 — recommend() discards the original goal, acts only on the classified intent label   [LOGGED]
- query: `recommend("I need to find and fix a bug in a large codebase")` → `detected_intents: ['scale']`, `recommendations: ['Allocate Budget According to Complexity']` (a TASK-CLASSIFIER rule about thinking-budget sizing) — nothing about finding or fixing a bug.
- category: P2 primitive coverage — recommend()'s intent-classification path
- gap: `classify_intent()` correctly tagged "large codebase" as `scale`, but `recommend()` then calls `want_to(intent_label)` — i.e. `want_to("scale")` — not `want_to(original_goal)`. The specific, actionable part of the request ("find and fix a bug") is discarded entirely; only the generic intent keyword drives the result.
- root_cause: `recommend()`'s design conflates "classify what kind of concern this is" with "search for tools using only that classification," rather than using intent to *weight* a search over the full goal text (the way `intentgraph_engine.py`'s intent-weight profiles do elsewhere in this codebase).
- reasoning_conclusion: real, but redesigning `recommend()` to blend intent classification with full-goal search is a bigger change than a mechanical fix — same shape as FCL-007/008/009 before their recurrence, i.e. worth watching for a second instance before committing to a specific redesign.
- verified_by: direct output, above.
- pattern: any goal combining a specific action with a generic intent-keyword-triggering phrase will lose the specific part. Single occurrence, not promoted.

### FCL-010 — duplicate tool_requires_tool edge, pre-existing DB content, not introduced this session   [LOGGED]
- query: `compatible_with("Edit")` → `requires: ['Read', 'Read']` (literal duplicate in the output)
- category: base DB data quality (`kgs/reasoning-graph.db`, inherited from `claude_kg_truth/claude-code-tools-kg.db`)
- gap: two distinct edge rows (`edge_id` 703 and 715) both encode `edit_file --tool_requires_tool--> read_file`, with different `properties` payloads (one plain `reason`, one richer `rationale`+`severity: CRITICAL`+`insight: "#62 - Critical Path Edge"`) — never deduplicated, so any consumer that lists `tool_requires_tool` targets without deduping sees it twice.
- root_cause: unknown — predates every action taken in this repo this session (both edge_ids were present in the base DB before the P0 patch ran). Likely two separate ingestion/curation passes wrote the same logical edge with different metadata and neither was reconciled against the other.
- reasoning_conclusion: real, low-severity (doesn't produce a wrong answer, just a cosmetic duplicate), but fixing it means picking which `properties` payload wins (or merging them) — a data-curation call, not something to guess at for one spot-checked pair. Not investigated repo-wide; unknown how many other `tool_requires_tool`/other edge-type pairs have the same duplication.
- verified_by: direct SQL, both edge rows shown with distinct `edge_id`/`properties`.
- pattern: any `compatible_with()`/`_get_connections()`-style caller that doesn't dedupe by `(source, target, edge_type)` will double-count this class of duplicate. Single confirmed instance; scope of the underlying DB issue unknown.

*(2026-07-14, first organic batch — the entries below were not sourced from deliberate P0/P0.5/P2 verification. Ran 22 diverse, realistic queries across all 7 primitives, not selected to fail. 5 real findings surfaced; 2 were mechanical and got fixed, 3 are design judgment calls and were logged, not forced.)*

### FCL-009 — similar_to/alternatives present near-zero-confidence noise as ranked results   [FIXED 2026-07-14]
- query: `similar_to("Task")` → `[NotebookRead 0.088, Glob 0.085, NotebookEdit 0.085]`; `similar_to("TodoWrite")` → `[BashOutput 0.078, Bash 0.067, Glob 0.067]`; `alternatives("WebSearch")` falls back to the same mechanism → `[WebFetch, NotebookRead, NotebookEdit, Grep]`
- category: P2 primitive coverage — similarity ranking confidence
- gap: for tools with structurally unique edge profiles (`task_agent` spawns agents, `todo_write` manages state — neither shares much with file/search tools under Jaccard similarity on connected-node sets), every candidate scores near-zero, but the primitive still returns a top-k as if it were a meaningful ranking. The pairings read as semantically arbitrary (why is NotebookRead "similar to" Task?).
- root_cause: `similar_to()` has no confidence floor — it always returns the top-k highest scores, even when the highest score is statistical noise, not signal.
- reasoning_conclusion: fixable, but the fix is a threshold below which the honest answer is "no meaningfully similar tool" instead of a ranked list — picking that threshold is a calibration/design call (what score is "noise"?), not a mechanical bug fix. Left open rather than guessing a cutoff.
- verified_by: direct output of `similar_to("Task", k=3)` / `similar_to("TodoWrite", k=3)` / `alternatives("WebSearch")`, all above.
- pattern: any tool whose edges are mostly unique to it (rather than shared patterns like `tool_complements`) will trigger this. Single occurrence class, not promoted.
- **Recurred on the 2nd organic batch**: `similar_to("AskUserQuestion")` (max 0.075) and `similar_to("BashOutput")` (max 0.083) showed the identical noise pattern, while `similar_to("NotebookEdit")` (0.2/0.184/0.143) and `similar_to("Grep")` (0.26/0.179/0.13) showed clean, meaningful signal — a sharp empirical gap between "signal" (≥0.143 observed) and "noise" (≤0.088 observed) across 6 tools tested, enough to ground a concrete threshold rather than guess one.
- **FIXED 2026-07-14**: added a confidence floor (`FLOOR = 0.1`, sitting cleanly in the observed gap) to `similar_to()`. Below it, returns the same `{'error': ...}` sentinel already used for "tool not found" — both `main()`'s CLI loop and `alternatives()` already handle that shape, so no caller changes needed. Verified: Task/TodoWrite/AskUserQuestion/BashOutput now correctly report "no strong match" with the strongest candidate named; NotebookEdit/Grep's genuine signal is untouched. Fixture re-run: 20/20, no regressions.

### FCL-008 — want_to's use-case fallback returns generic noise for goals with no real tool coverage   [LOGGED — sharpened on recurrence, still not fixed]
- query: `want_to("safely delete a file")` → `[notebook_edit 0.7, edit_file 0.7, glob_pattern_search 0.7]`; `want_to("compare two files for differences")` → `[notebook_read 0.7, edit_file 0.7, glob_pattern_search 0.7]`
- category: P2 primitive coverage — fallback match quality
- gap: neither result is actually about deleting or comparing — the generic word "file" (present in nearly every tool's use_cases) drives the 0.7-score fallback match (`_search_use_cases`), while the actually-distinguishing word ("delete"/"compare") has zero coverage anywhere in the corpus (there is genuinely no delete tool, and no tool's use_cases mention diffing). The results look like answers but aren't.
- root_cause: `_search_use_cases` matches on any word >2 chars with no weighting for how *distinguishing* that word is — a generic word like "file" produces the same score as a specific one.
- reasoning_conclusion: same shape as FCL-009 — needs either a confidence floor or word-specificity weighting (e.g. IDF-style down-weighting of words that match many tools), both of which are calibration decisions, not mechanical fixes. Also worth noting for P0 separately: there is genuinely no delete-file tool in the 14-tool corpus (Claude Code deletion goes through Bash `rm`, not a dedicated tool) — `want_to("delete")` *should* surface `bash_execute`, and doesn't, because "delete" isn't in `GOAL_TO_TOOLS` either.
- verified_by: direct output, above.
- pattern: any goal phrase whose specific/distinguishing word has zero corpus coverage will fall back to generic-word noise instead of a low-confidence or empty result. Single occurrence class, not promoted.
- **Recurred on the 2nd organic batch, 3 more instances**: `want_to("rename a file")`, `want_to("move a file to another directory")`, `want_to("compress files into an archive")` all returned the same noise pattern, none actually relevant.
- **Sharper diagnosis — this changes the conclusion, not just the evidence.** Checked whether `bash_execute` (the obviously-correct answer for all three — `mv`/`rm`/`tar` via shell) would surface if the generic-word-noise problem were fixed. It wouldn't: `bash_execute`'s own `use_cases` were read directly and **never mention rename, move, or compress at all** — a genuine *content* gap (the corpus doesn't document Bash's general-purpose file-manipulation use), not only a matching-*algorithm* gap. A better matcher would suppress the wrong noise but still couldn't produce the right answer, because the right answer isn't written down anywhere in the corpus.
- **Still not fixed, more firmly now**: suppressing noise (IDF-style down-weighting) is a real improvement worth doing eventually, but wouldn't solve the user-facing problem this recurrence exposed, and adding "rename/move/compress" to `bash_execute`'s use_cases to fill the content gap would be fabricating tool content with no source grounding — exactly what this session has refused to do throughout. Left open on both counts. Recurred 5 total times (2 in batch 1, 3 in batch 2) across the identical shape; still correctly not promoted to a mint candidate, because promoting would require inventing content.

### FCL-007 — compose_for's compound_patterns doesn't compose multi-category goals   [FIXED 2026-07-14]
- query: `compose_for("add a new feature with tests and documentation")` → decomposition `['read', 'run']`, tools `[Read, Bash]`
- category: P2 primitive coverage — goal decomposition (same code area as FCL-003, different failure mode)
- gap: the goal genuinely spans three of `compound_patterns`' categories (`implement`, `test`, `document`) but only `'test'` fires — `_decompose_goal` returns on the *first* substring-matching key it finds (dict iteration order), discarding the goal's other aspects entirely. "Add a new feature" and "documentation" are silently dropped, not decomposed.
- root_cause: `compound_patterns` matching is "first match wins," not "union of all matches" — a design choice inherited from the original port, and FCL-003's fix (adding a `'bug'` key) didn't touch this structural limitation, only added one more single-category entry.
- reasoning_conclusion: real, but fixing it well means deciding how multi-category decomposition should behave — a design question, not a one-line patch, and at the time no fixture/canonical query exercised multi-category goals to validate a fix against. Left open rather than guessing at a broader rewrite.
- verified_by: direct output, above.
- pattern: any goal whose phrasing matches 2+ `compound_patterns` keys will silently collapse to just the first (in dict order), never a composite.
- **Recurred on the 2nd organic batch**: `compose_for("build a new feature, write tests, and deploy it")` → decomposition `['read', 'run']`, tools `[Read, Bash]` — spans `test` and `deploy` categories, only `test` fired. Identical shape, different goal text — clean 2nd occurrence.
- **FIXED 2026-07-14**: `_decompose_goal` now collects steps from *every* matching `compound_patterns` key (deduplicated in first-seen order) instead of returning on the first match. Verified: the same goal now decomposes to `['read', 'run', 'build']` → `[Read, Bash, Bash]`, correctly covering both categories. Regression-checked against the canonical query (`search`→`read`→`fix`, unchanged) and a single-category goal (`refactor`: `find`→`read`→`edit`, unchanged) — union-of-one-match is a no-op for single-category goals, so no prior behavior changed. Fixture re-run: 20/20.

### FCL-006 — want_to's reasoning-node-type list went stale the moment Lane B added a new node type   [FIXED 2026-07-14]
- query: `want_to("cache an expensive operation")` and `want_to("validate json output")` — neither surfaced `hbcap_prompt_caching`/`hbcap_json_mode` despite both having directly relevant `tool_enables_capability`/`tool_enhances_technique` content
- category: P2/P0.5 Lane B boundary — search coverage drift
- root_cause: the FCL-002-era fix hardcoded `node_type = 'synthesis_rule'` in `_search_rule_statements`/`_get_rule_info`, because `handbook_capability` didn't exist yet — it was added later the same session by P0.5 Lane B. The search step went stale relative to its own graph without anyone touching `query.py` again.
- reasoning_conclusion: real, mechanical, safe to fix — widened both helpers to a `REASONING_NODE_TYPES = ('synthesis_rule', 'handbook_capability')` tuple instead of a hardcoded single type, with a comment directing future node-type additions to extend the same list.
- verified_by: `want_to("cache an expensive operation")` now includes `hbcap_prompt_caching`; `want_to("validate json output")` now includes `hbcap_json_mode`. Fixture re-run: 20/20, no regressions.
- pattern: **this is the generalizable lesson** — any future new reasoning-layer node type (P3-minted or otherwise) needs the same registration, or search coverage silently drifts behind the graph again. Documented directly in the code comment, not just here.

### FCL-005 — can_it's intent-keyword matching was phrase-substring-only, unlike every other matcher in the file   [FIXED 2026-07-14]
- query: `can_it("access the internet")` → `can=False, related_tools=[]`; `can_it("access the web")` → same
- category: P2 primitive coverage — can_it correctness (not just weak, actually wrong)
- gap: Claude Code obviously can access the internet (`web_fetch`, `web_search` both exist), but `can_it` returned a hard **false negative** — the most serious class of miss found this session, since it's not "weak ranking," it's a wrong yes/no answer to a basic capability question.
- root_cause: Step 5's intent-keyword check was `capability_lower in kw.lower() or kw.lower() in capability_lower` — whole-phrase substring only. `web_fetch` declares the keyword `"access url"`; neither `"access the internet"` nor `"access url"` is a substring of the other, so it never matched, even though `want_to()`'s equivalent steps (2/3) and `_search_rule_statements` already word-split for exactly this reason.
- reasoning_conclusion: real, mechanical, safe to fix — added a word-overlap check (`len(w) > 3` tokens) alongside the existing substring check, matching the word-splitting convention already used everywhere else in `query.py`. Word-overlap is a superset of substring matching, so this can only add matches the fixture didn't already rely on, never remove ones it does.
- verified_by: `can_it("access the internet")` → `can=True, related_tools=[WebFetch, WebSearch]`; `can_it("access the web")` → `can=True, related_tools=[WebFetch]`. Fixture re-run: 20/20, no regressions.
- pattern: any capability phrase whose keyword overlap is word-level but not phrase-level would have hit this. Not a one-off — the fix generalizes to the whole matcher, not just this query.


### FCL-004 — canonical query 3 fails: TASK-CLASSIFIER rules aren't extracted   [CLOSED 2026-07-14]
- query: "which rules warn against extended-thinking on simple tasks?" (`p2-acceptance-fixture.json` p2-canon-3, v1's 3rd canonical query)
- category: P0.5 Lane A scope boundary
- gap: `want_to()` (even after the FCL-002-era rule-search extension) returns no TASK-CLASSIFIER content — because none exists in the graph. Confirmed: TASK-CLASSIFIER-SYNTHESIS-RULES.md has 0/76 declared `Related Rules`, correctly routed to the P3 mint queue by open call #2, not Lane A's 17-rule scope.
- root_cause: this canonical query was written (v1 plan) assuming TASK-CLASSIFIER content would be reachable; open call #2 (declared after v1) deliberately excluded it from extraction. The gate and the declared scope now disagree.
- reasoning_conclusion: correct to fail, not a bug. Closing it would mean either extracting TASK-CLASSIFIER (expanding Lane A beyond its declared 17-rule scope — a scope call, not mine to make) or fabricating content (never). Left open on purpose.
- verified_by: `p2_fixture_runner.py` — FAIL, ids returned contain no TASK-CLASSIFIER-derived node.
- pattern: any canonical/flagship query should be checked against the *currently declared* extraction scope before being frozen into a fixture — a gate can quietly outlive the scope decision that invalidated it.
- **CLOSED 2026-07-14, on Eyal's explicit instruction ("close FCL-003 and FCL-004").** Extracted TASK-CLASSIFIER's 12 rules + 1 standalone anti-pattern (`anti_004_unconstrained_thinking`, present only in the file's "Anti-Patterns Detected" summary with no fuller `Rule N:` block) as `synthesis_rule` **nodes only** — id/title/statement/threshold-or-condition/formula are directly in the source text (mechanical, zero inference, dot 4). Deliberately minted **zero** `rule_related_to` edges: 0/76 of this file's rules declare `Related Rules`, so edge creation stays exactly within open call #2's declared 17-rule boundary — this closure expands *node* extraction, not the *edge*-scope decision Eyal already made. The file's declared source (`task_classifier.py`) does not exist anywhere in `python/` — recorded as an unresolved external reference in each node's metadata, no `relic_script` node fabricated for it (same discipline as the Lane A "PLAYBOOK-5" references). Live-verified: `want_to("which rules warn against extended-thinking on simple tasks")` now surfaces `extended_thinking_003_simple_tasks_antipattern` ("Don't Use Extended Thinking on Simple Tasks") at rank 4 — an exact semantic match, not incidental overlap. Canonical query 3 now passes.

### FCL-003 — compose_for's canonical query decomposes weakly   [CLOSED 2026-07-14]
- query: "which tools compose to fix a bug found via search?" (`p2-acceptance-fixture.json` p2-canon-1, v1's flagship query)
- category: P2 primitive coverage — goal decomposition
- gap: `compose_for()` returns only `['Edit']` — technically not wrong (Edit does fix things) but ignores "found via search" entirely. `_decompose_goal()`'s `compound_patterns` dict (inherited verbatim from `intent_query.py`) has keys for `refactor`/`migrate`/`debug`/`implement`/`test`/`deploy`/`understand`/`document` — none match "bug" or "search", so the goal never decomposes into a real multi-tool sequence (e.g. Grep→Read→Edit).
- root_cause: `compound_patterns` was authored against the original `intent_query.py` corpus's expected phrasing, not this project's exact canonical query text. Not touched during the port (kept as-is per "port not design").
- reasoning_conclusion: real primitive weakness, but fixing it means picking which keyword→decomposition mappings deserve adding — a judgment call about the primitive's design, not a mechanical extraction. Left as-is rather than editing `compound_patterns` speculatively.
- verified_by: `p2_fixture_runner.py` — technically PASS (`tools_nonempty` check), but flagged PARTIAL in the fixture's own `status` field since it doesn't achieve the query's evident intent.
- pattern: any compose_for canonical query should be spot-checked against `compound_patterns`' actual keys, not assumed to decompose sensibly.
- **CLOSED 2026-07-14.** Two fixes, the second found only by attempting the first: (1) added a `'bug'` key to `compound_patterns` (`['search', 'read', 'fix']` — search-first, matching the query's own "found via search" wording); (2) that alone still resolved the "search" sub-goal to `Edit`, not `Grep` — traced to `_decompose_goal` re-embedding the *entire original goal text* into every sub-goal (`f"{step} for {goal}"`), so "fix" (present in the base goal "fix a bug...") bled into every other sub-goal's `want_to()` call regardless of which step it was building. This is a pre-existing defect in the ported code, not something introduced here — it only stayed invisible because no prior test goal happened to contain two different `GOAL_TO_TOOLS` keywords at once. Fixed by returning bare step words instead of goal-echoing strings. Regression-checked: `compose_for("refactor python files")` still resolves cleanly (`Glob → Read → Edit`, unchanged). Live-verified: canonical query 1 now composes `Grep → Read → Edit`, matching the query's evident intent exactly.



### FCL-001 — path/traversal miss: notebook tools have no reasoning edges   [FROZEN 2026-07-14]
- query: `path read_file notebook_edit` (diagnostic, run during P0-patch nai load verification 2026-07-14, not yet a real P2 query — P2 isn't wired yet)
- category: tool-graph reasoning-edge layer
- gap: no path exists between `notebook_edit`/`notebook_read` and any other tool via `tool_requires_tool` / `tool_similar_to` / `tool_complements` / `tool_alternative_to` / `tool_conflicts_with` / `combines_with` — confirmed zero such edges touch either node (direct SQL)
- root_cause: the 2 notebook tools were patched into the DB purely from `claude-code-tools/*.json` (P0 patch, 2026-07-13). That JSON has no field carrying this edge type. The other 12 tools' reasoning edges are DB-native/hand-curated content, not derivable from the JSON schema at all — confirmed: every tool's `suggested_combinations` field (JSON-sourced) maps only to child `tool_combination` nodes via `tool_has_combination`, notebook tools included; the direct tool-to-tool `tool_requires_tool`/`tool_similar_to`/etc. edges the other 12 have came from somewhere else entirely.
- reasoning_conclusion: real, honest coverage gap, not a bug. The P0 gate ("structural edges complete; loads in nai") is still met — reasoning edges were always P0.5's scope, not P0's. But the 2 notebook tools are graph islands relative to the reasoning layer until P0.5/P3 fills it.
- verified_by: `nai --db kgs/reasoning-graph.db --pipe "path read_file notebook_edit"` → "No path found"; `path read_file glob_pattern_search` (a node with real `tool_similar_to` edges) → `Read -> Glob, length=1, confidence=1.0`, isolating this as a data gap, not a path-command defect.
- pattern: any future JSON-only tool patch (vs. a DB-native tool) will land with zero reasoning edges by construction — worth a standing check whenever `claude-code-tools/*.json` is the sole source for a new tool node.
- **MINTED → VERIFIED → FROZEN 2026-07-14** (same-session, on Eyal's explicit approval — the recurrence gate normally requires a 2nd independent occurrence before promotion, but Eyal directed minting directly here since `notebook_edit` and `notebook_read` are themselves two independent instances of the identical root-cause shape, and both candidate sets shared dual grounding). Formalized as `mint_001_tool_combo_inference` in `synthesis-rules/minted/TOOL-COMBO-INFERENCE-MINTED.md` — 11 reasoning edges written into `kgs/reasoning-graph.db` (`tool_requires_tool`/`tool_similar_to`/`tool_complements`/`tool_conflicts_with`), each grounded in both the tool's own JSON `suggested_combinations` text and an already-frozen anchor edge on the nearest sibling tool. `edges.synthesis_chain` tags every inserted row `"mint_001_tool_combo_inference / FCL-001"`. Live-reverified via `nai`: `path read_file notebook_edit` now resolves (previously "No path found").

*(P1/P2 aren't wired to the combined store for live queries yet, per the plan's sequencing — FCL-001 is diagnostic, from P0 verification, not a P2-driven query. Real P2-driven entries land once the query fixture runs.)*

### FCL-002 — no tool↔rule edges exist; the plan's own P0.5 gate isn't met by Lane A alone   [RESOLVED 2026-07-14 — corrected, not force-closed]
- query: honest post-hoc check after P0.5 Lane A extraction (2026-07-14) — "does any traversal from a tool node reach a synthesis rule?"
- category: P0.5 / P1 boundary — reasoning-layer connectivity
- gap: zero edges connect any of the 14 `tool` nodes to any of the 20 new `synthesis_rule` nodes (confirmed by direct SQL join). The plan's own literal P0.5 gate reads: "a traversal from a tool node reaches its governing rules and their anti-patterns in ≤2 hops, with confidence on every reasoning edge." That is **not met** — Lane A extraction is rule↔rule only, by design (open call #2 scoped it to the 17 rules' *declared* `Related Rules` field, which never references a tool id).
- root_cause: the 17 extracted rules are agent-architecture rules (caching, error handling, session management, iteration limits) — none of their source text names a specific one of the 14 concrete tools (Read/Write/Edit/etc.). A tool→rule edge (e.g. `task_agent` ~ `anti_001_infinite_tool_loops`) would have to be inferred, not extracted — genuinely P3-mint-shaped, not P0.5-shaped, per the same extract-vs-decide law that scoped Lane A in the first place.
- reasoning_conclusion: don't fabricate tool→rule links to make the gate's checkbox look satisfied. Multi-hop rule↔rule composition itself is proven live (`dep_003 → anti_001 → constr_002`, confidence 1.0) — that's real progress — but "governing rules reachable from a tool" needs its own grounded pass, likely a `mint_00N`-style matcher (signature: rule statement mentions a concept a tool's description/use_cases also covers; confirm: dual match, not just keyword overlap; fix: `tool_governed_by_rule` edge).
- verified_by: direct SQL join (`edges` × `nodes` on both endpoints' `node_type`) returned 0 rows.
- pattern: any future Lane A/B extraction pass should check tool↔rule connectivity explicitly, not just rule↔rule — the plan's gate wording conflates two different edge classes. Single occurrence so far — not promoted.
- **RESOLVED 2026-07-14, by correcting the premise, not by minting a forced edge.** Sampled the strongest candidate tools first (`task_agent`, `bash_execute`, `bash_output` — the ones with real execution/reliability semantics in their own description/limitations text) against the 17 rules' statements: no genuine dual-grounded match survived scrutiny (e.g. `task_agent`'s own limitations state it is stateless/one-shot, which argues *against* `anti_005_missing_session_management` applying, not for it — a surface "agent" keyword match, not a real one). Escalated to checking each rule FILE's own header instead of individual rule bodies, and found the real answer: `TOOL-REGISTRY-SYNTHESIS-RULES.md` states "**Source**: Implementation of `tool_registry_builder.py`"; `CODE-REVIEW-GENERATOR-SYNTHESIS-RULES.md` states "**Tool**: `code_review_generator.py`"; `DOCUMENTATION-GENERATOR-SYNTHESIS-RULES.md` states "**Tool**: `documentation_generator.py`". All three are real `python/` relic scripts (confirmed present), but **none of them is one of the 14 `claude-code-tools` `tool` nodes** — they're the general-purpose codegen/analysis relics CLAUDE.md's folder map already separates from the P0–P5 tool-graph path. The plan's P0.5 gate wording ("traversal from a tool node reaches its governing rules") assumed these 17 rules governed the 14 CLI tools; they don't — they govern 3 different scripts entirely. That's a premise correction, not a data gap.
- **Action taken**: added 3 `relic_script` nodes (`tool_registry_builder_py`, `code_review_generator_py`, `documentation_generator_py` — a distinct node_type from `tool`, deliberately, so the two categories never conflate in a query) and 17 `extracted_from` edges (one per Lane A rule → its file-header-declared script) — pure extraction, the header states it verbatim, not inference. Live-verified: `path anti_001_infinite_tool_loops tool_registry_builder_py` → length=1, confidence=1.0. Re-checked after the fix: edges from the 14 `tool` nodes to any rule/script node are still exactly 0 — confirming this closed the *right* thing (the true governing relationship, now captured) without fabricating the wrong thing (a fake tool↔rule link that never existed).
