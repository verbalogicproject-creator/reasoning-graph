"""Instance 0 — the claude-code-tools reasoning graph (kgs/reasoning-graph.db).

Every kind below was enumerated from the LIVE DB on 2026-07-19 (13 node kinds,
23 edge kinds; sqlite GROUP BY probes recorded in the SoT). The `contradicts`
edge kind is declared with zero current rows — it is the typed contradiction
channel future mints use; cycles are NOT contradictions (see EdgeKind.cycle_class).

Confidence rules implement the SoT's edge-confidence derivation table. Precedence
note for the migration: an edge with a non-NULL synthesis_chain takes
declared:matcher:<mint_id> at the matcher's declared confidence REGARDLESS of its
kind's default rule below (mint_001 = 0.85 governs the 11 notebook edges even
though their kinds default to inherited_curation_default).
"""
from reasoning_graph.schema import (
    ConfidenceRule,
    EdgeKind,
    GraphSchema,
    Profile,
    RetirementPolicy,
)

_STRUCTURAL = ConfidenceRule(
    basis="declared:structural_extraction", value=1.0,
    formula_note="P0 structural edge, loaded 1:1 from source JSON/DB structure")
_VERBATIM = ConfidenceRule(
    basis="declared:verbatim_extraction", value=1.0,
    formula_note="extraction with a quoted/verbatim source line (Lane A headers, Lane B source_quote)")
_INHERITED = ConfidenceRule(
    basis="declared:inherited_curation_default", value=0.90,
    formula_note="pre-existing DB-native curated reasoning edge; 0.90 is a DECLARED default flagged for Eyal's confirmation")
_RULE_DERIVED = ConfidenceRule(
    basis="derived:source_rule_confidence",
    value=0.70,   # DECLARED corpus-min fallback (SoT lock #22): used ONLY when a source
                  # rule declares no confidence (m001 tries source-node derivation first).
                  # 0.70 = min confidence across this corpus's rule files (Data-Grounding
                  # verified 2026-07-20). Machine-readable here, not buried in prose.
    formula_note="= source rule node metadata confidence; fallback = value (0.70, observed corpus-file minimum) when the rule declares none (TASK-CLASSIFIER's 12)")
_CONTRADICTS = ConfidenceRule(
    basis="declared:initial_guess",
    formula_note="no instances yet; any future contradicts edge carries its minter's declared value")

SCHEMA = GraphSchema(
    name="claude_code_tools",
    node_kinds=(
        "tool", "use_case", "limitation", "tool_combination", "example",
        "prerequisite", "configuration_setting", "workaround", "workaround_needed",
        "synthesis_rule", "handbook_capability", "handbook_tool_note", "relic_script",
    ),
    edge_kinds=(
        # --- structural (P0) ---
        EdgeKind("tool_has_use_case", _STRUCTURAL),
        EdgeKind("tool_has_limitation", _STRUCTURAL),
        EdgeKind("tool_has_combination", _STRUCTURAL),
        EdgeKind("tool_has_example", _STRUCTURAL),
        EdgeKind("tool_has_prerequisite", _STRUCTURAL),
        EdgeKind("tool_has_configuration", _STRUCTURAL),
        EdgeKind("workflow_includes_tool", _STRUCTURAL),
        EdgeKind("has_workaround", _STRUCTURAL),
        EdgeKind("limitation_needs_workaround", _STRUCTURAL),
        EdgeKind("limitation_has_workaround", _STRUCTURAL),
        EdgeKind("combines_with", _STRUCTURAL, cycle_class="benign_reciprocal"),
        # --- frozen reasoning: rule layer (P0.5 Lane A) ---
        EdgeKind("rule_related_to", _RULE_DERIVED, cycle_class="benign_reciprocal"),
        EdgeKind("extracted_from", _VERBATIM),
        # --- frozen reasoning: handbook layer (P0.5 Lane B, quote-traceable) ---
        EdgeKind("same_as", _VERBATIM, symmetric=True, cycle_class="benign_reciprocal"),
        EdgeKind("tool_enables_capability", _VERBATIM),
        EdgeKind("tool_enhances_technique", _VERBATIM),
        EdgeKind("tool_primary_for_capability", _VERBATIM),
        EdgeKind("tool_supports_capability", _VERBATIM),
        # --- inherited curated reasoning edges (DB-native; minted rows override via synthesis_chain) ---
        EdgeKind("tool_requires_tool", _INHERITED),
        EdgeKind("tool_similar_to", _INHERITED, symmetric=True, cycle_class="benign_reciprocal"),
        EdgeKind("tool_complements", _INHERITED, cycle_class="benign_reciprocal"),
        EdgeKind("tool_alternative_to", _INHERITED, symmetric=True, cycle_class="benign_reciprocal"),
        EdgeKind("tool_conflicts_with", _INHERITED),
        # --- typed contradiction channel (0 rows today; the refusal boundary's trigger) ---
        EdgeKind("contradicts", _CONTRADICTS, cycle_class="contradiction"),
    ),
    profile=Profile(),          # defaults ARE this DB's schema (claude-code-tools-kg.db shape)
    floor=0.30,
    promotion_threshold=2,
    retirement=RetirementPolicy(active_cap=50, min_uses=5, contradiction_ratio=0.5),
)
