---
id: fcl-fixture
kind: log
audience: test-harness
status: fixture — synthetic, weaving domain; schema-identical to the real frontier-call-log.ngf.md, with the inline `- gap_shape:` field new entries carry
---

# Frontier-call log — tiny_weaving fixture

## 1 · Schema

Same as the real log (§1 there), plus the inline declared field:

```
### <ID> — <one-line query/gap>   [LOGGED | PROMOTED | MINTED | FROZEN]
- query / category / gap / root_cause / reasoning_conclusion / verified_by / pattern
- gap_shape: <declared-kebab-or-snake-shape>
```

## 2 · Log (newest on top, append-only)

### FIX-006 — trace(loom_2, dye_bath_2) crosses the rivals cycle and double-counts   [LOGGED]
- query: trace("loom_2", "dye_bath_2")
- category: traversal
- gap: BFS revisits the spindle_a/spindle_b rivals pair
- root_cause: reciprocal rivals edges form a benign cycle the walker re-enters
- reasoning_conclusion: cycle handling, not new content; not a mint candidate shape
- verified_by: direct output
- pattern: benign reciprocal cycles need visited-set discipline, not edges
- gap_shape: benign_cycle_revisit_in_walker

### FIX-005 — want_to("spin fine thread fast") finds no spindle tension edge (2nd)   [LOGGED]
- query: want_to("spin fine thread fast")
- category: spindle reasoning layer
- gap: no tension edge connects spindle_b to any loom capability
- root_cause: tension edges were never declared for spindles added after the first extraction pass
- reasoning_conclusion: same shape as FIX-003 — the 2nd occurrence; promotable per the recurrence gate
- verified_by: direct output
- pattern: late-added spindle nodes land without tension edges by construction
- gap_shape: missing_tension_edge_for_new_spindle

### FIX-004 — why_not(loom_1, "dye wool blue") gives no limitation   [LOGGED]
- query: why_not("loom_1", "dye wool blue")
- category: limitation coverage
- gap: dye_bath_3 (woad) is an island; no limitation/edge explains the miss
- root_cause: woad bath was catalogued but never tied to any loom or spindle
- reasoning_conclusion: content gap in the corpus — nothing states the woad bath's relations; inventing one would be fabrication
- verified_by: direct output
- pattern: catalogued-but-untied nodes produce unexplainable misses
- gap_shape: island_node_catalogued_without_ties

### FIX-003 — want_to("spin coarse yarn") finds no spindle tension edge (1st)   [LOGGED]
- query: want_to("spin coarse yarn")
- category: spindle reasoning layer
- gap: no tension edge connects spindle_a to loom_1's capability set
- root_cause: tension edges were never declared for spindles added after the first extraction pass
- reasoning_conclusion: derived in prose that whorl weight implies tension class; candidate edge shape recorded
- verified_by: direct output
- pattern: late-added spindle nodes land without tension edges by construction
- gap_shape: missing_tension_edge_for_new_spindle

### FIX-002 — resolve crossing guild_rule_x/guild_rule_y refused (correctly)   [LOGGED]
- query: resolve --start loom_2 --end pattern_card_2
- category: refusal boundary
- gap: none — the refusal is the correct behavior; logged to record the contradiction's reach
- root_cause: guild_rule_x contradicts guild_rule_y by declaration
- reasoning_conclusion: not a gap to fix; contradiction is content, not error
- verified_by: REFUSE(contradiction) output listing the cycle
- pattern: refusals are results; only repeated WRONG refusals are frontier calls
- gap_shape: correct_refusal_logged_for_reach

### FIX-001 — weak_link provenance below floor   [LOGGED]
- query: resolve --start loom_1 --end pattern_card_1
- category: confidence floor
- gap: only path is the 0.20 weak_link — WEAK_ANSWER
- root_cause: pattern_card_1's provenance was declared initial_guess at 0.20
- reasoning_conclusion: correct honest weak answer; watching whether stronger provenance ever gets declared
- verified_by: WEAK_ANSWER output, confidence 0.20 < floor 0.30
- pattern: sub-floor single-path targets stay weak until new evidence edges land
- gap_shape: single_subfloor_path_to_target
