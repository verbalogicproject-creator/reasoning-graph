"""Second corpus (stretch, gate G7): the lowering-ladder domain. A NEW GraphSchema,
ZERO core edits — the whole point. Node/edge kinds differ entirely from instance 0."""
from reasoning_graph.schema import ConfidenceRule, EdgeKind, GraphSchema, Profile

_S = ConfidenceRule("declared:structural_extraction", 1.0)
_V = ConfidenceRule("declared:verbatim_extraction", 1.0)
_H = ConfidenceRule("declared:initial_guess", 0.20)
_C = ConfidenceRule("declared:initial_guess", 0.85)

SCHEMA = GraphSchema(
    name="lowering_ladder",
    node_kinds=("rung", "skill", "concept"),
    edge_kinds=(
        EdgeKind("lowers_to", _S),
        EdgeKind("sits_on", _V),
        EdgeKind("needs", _S),
        EdgeKind("hunch", _H),
        EdgeKind("contradicts", _C, cycle_class="contradiction"),
    ),
    profile=Profile(),   # default table/column names — the DB was built to match
    floor=0.30,
)
