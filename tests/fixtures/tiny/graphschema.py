"""Tiny fixture GraphSchema — the anti-hardcoding proof.

Alien domain (weaving), alien vocabulary, NON-DEFAULT name for every Profile
field. active_cap=2 on purpose: small enough that the retirement fixture's
over-cap path is exercisable.
"""
from reasoning_graph.schema import (
    ConfidenceRule,
    EdgeKind,
    GraphSchema,
    Profile,
    RetirementPolicy,
)

_S = ConfidenceRule(basis="declared:structural_extraction", value=1.0)
_V = ConfidenceRule(basis="declared:verbatim_extraction", value=1.0)
_I = ConfidenceRule(basis="declared:inherited_curation_default", value=0.90)
_G = ConfidenceRule(basis="declared:initial_guess")

SCHEMA = GraphSchema(
    name="tiny_weaving",
    node_kinds=("loom", "spindle", "dye_bath", "pattern_card", "guild_rule"),
    edge_kinds=(
        EdgeKind("feeds", _S),
        EdgeKind("tunes", _V),
        EdgeKind("governed_by", _S),
        EdgeKind("weak_link", _G),
        EdgeKind("rivals", _I, symmetric=True, cycle_class="benign_reciprocal"),
        EdgeKind("contradicts", _G, cycle_class="contradiction"),
    ),
    profile=Profile(
        nodes_table="strands",
        node_id="strand_id",
        node_kind="strand_kind",
        node_name="label",
        node_description="blurb",
        node_metadata="extra",
        edges_table="ties",
        edge_source="tie_from",
        edge_target="tie_to",
        edge_kind="tie_kind",
        edge_confidence="trust",
        edge_properties="extra_json",
        edge_synthesis_chain="chain_tag",
    ),
    floor=0.30,
    promotion_threshold=2,
    retirement=RetirementPolicy(active_cap=2, min_uses=5, contradiction_ratio=0.5),
)
