"""Canonical declaration for the bundled Claude Code tools instance.

The endpoint contracts are a direct declaration of the relationships observed
in ``data/derived/reasoning-graph.clean.db`` after repair-instance-v1. They make
direction errors and cross-kind corruption refusal-grade integrity failures.
"""

from reasoning_graph.schema import (
    ConfidenceRule,
    EdgeKind,
    GraphSchema,
    Profile,
    RetirementPolicy,
)


_STRUCTURAL = ConfidenceRule(
    basis="declared:structural_extraction",
    value=1.0,
    formula_note="P0 relationship loaded directly from checked-in source structure",
)
_VERBATIM = ConfidenceRule(
    basis="declared:verbatim_extraction",
    value=1.0,
    formula_note="quote- or source-record-traceable extraction",
)
_INHERITED = ConfidenceRule(
    basis="declared:inherited_curation_default",
    value=0.90,
    formula_note="pre-existing curated reasoning relationship; declared ranking weight",
)
_RULE_DERIVED = ConfidenceRule(
    basis="derived:source_rule_confidence",
    value=0.70,
    formula_note="source rule confidence, falling back to the observed corpus minimum",
)
_CONTRADICTS = ConfidenceRule(
    basis="declared:initial_guess",
    formula_note="future contradiction claims must carry their minter's declared value",
)


def _edge(
    name,
    confidence_rule,
    source,
    target,
    *,
    symmetric=False,
    cycle_class="unclassified",
):
    return EdgeKind(
        name,
        confidence_rule,
        source_kinds=(source,),
        target_kinds=(target,),
        symmetric=symmetric,
        cycle_class=cycle_class,
    )


SCHEMA = GraphSchema(
    name="claude_code_tools",
    node_kinds=(
        "tool",
        "use_case",
        "limitation",
        "tool_combination",
        "example",
        "prerequisite",
        "configuration_setting",
        "workaround",
        "workaround_needed",
        "synthesis_rule",
        "handbook_capability",
        "handbook_tool_note",
        "relic_script",
        "workflow",
    ),
    edge_kinds=(
        _edge("tool_has_use_case", _STRUCTURAL, "tool", "use_case"),
        _edge("tool_has_limitation", _STRUCTURAL, "tool", "limitation"),
        _edge("tool_has_combination", _STRUCTURAL, "tool", "tool_combination"),
        _edge("tool_has_example", _STRUCTURAL, "tool", "example"),
        _edge("tool_has_prerequisite", _STRUCTURAL, "tool", "prerequisite"),
        _edge("tool_has_configuration", _STRUCTURAL, "tool", "configuration_setting"),
        _edge("workflow_includes_tool", _STRUCTURAL, "workflow", "tool"),
        _edge("has_workaround", _STRUCTURAL, "tool", "workaround"),
        _edge("limitation_needs_workaround", _STRUCTURAL, "limitation", "workaround_needed"),
        _edge("limitation_has_workaround", _STRUCTURAL, "limitation", "workaround"),
        _edge("combines_with", _STRUCTURAL, "tool_combination", "tool", cycle_class="benign_reciprocal"),
        _edge("rule_related_to", _RULE_DERIVED, "synthesis_rule", "synthesis_rule", cycle_class="benign_reciprocal"),
        _edge("extracted_from", _VERBATIM, "synthesis_rule", "relic_script"),
        _edge("same_as", _VERBATIM, "tool", "handbook_tool_note", symmetric=True, cycle_class="benign_reciprocal"),
        _edge("tool_enables_capability", _VERBATIM, "tool", "handbook_capability"),
        _edge("tool_enhances_technique", _VERBATIM, "tool", "handbook_capability"),
        _edge("tool_primary_for_capability", _VERBATIM, "tool", "handbook_capability"),
        _edge("tool_supports_capability", _VERBATIM, "tool", "handbook_capability"),
        _edge("tool_requires_tool", _INHERITED, "tool", "tool"),
        _edge("tool_similar_to", _INHERITED, "tool", "tool", symmetric=True, cycle_class="benign_reciprocal"),
        _edge("tool_complements", _INHERITED, "tool", "tool", cycle_class="benign_reciprocal"),
        _edge("tool_alternative_to", _INHERITED, "tool", "tool", symmetric=True, cycle_class="benign_reciprocal"),
        _edge("tool_conflicts_with", _INHERITED, "tool", "tool"),
        EdgeKind("contradicts", _CONTRADICTS, cycle_class="contradiction"),
    ),
    profile=Profile(),
    floor=0.30,
    promotion_threshold=2,
    retirement=RetirementPolicy(
        active_cap=50,
        min_uses=5,
        contradiction_ratio=0.5,
    ),
)
