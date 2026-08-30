"""The one declaration object: GraphSchema. Everything else is derived from it.

House law (declared_core lineage): if you are typing a table, column, node-kind,
or edge-kind name anywhere in `reasoning_graph/` core, stop — thread it through
this schema. The tiny test fixture uses non-default names for every one of these
to prove nothing is hardcoded (gate G1).

IMPLEMENTED THIS SESSION (contract layer): dataclasses, closed basis vocabulary,
structural validate(), instance loading. OPUS-FILLS: nothing here — DB-side
validation lives in store.py; do not widen this module's scope.

Estimate-honesty boundary (lowering-ladder docs 00/04): every confidence number
in the system is exactly one of
  declared:*  — a value a human/matcher declared, carried verbatim, or
  derived:*   — computed by a stated formula from declared inputs.
Nothing is ever presented as measured, with ONE exception: API-usage token
counts in the A/B harness, labeled `measured:api_usage`. That label is valid
ONLY inside measure/ab_* artifacts, never on a graph edge — is_valid_basis()
therefore rejects it.
"""
from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------- basis vocab
# Closed vocabulary. Exact labels:
CLOSED_BASIS_EXACT = frozenset({
    "declared:structural_extraction",    # P0 structural edges from source JSON — 1.0
    "declared:verbatim_extraction",      # quote-traceable extraction edges — 1.0
    "declared:inherited_curation_default",  # pre-existing DB-native reasoning edges — 0.90 (flagged for Eyal)
    "declared:initial_guess",            # explicit human seed value, awaiting evidence
    "derived:source_rule_confidence",    # edge inherits its declaring rule node's confidence
})
# Parameterized labels, validated by prefix:
CLOSED_BASIS_PREFIXES = (
    "declared:matcher:",   # declared:matcher:<mint_id> — minted edge carries its matcher's confidence
    "derived:corpus_min(", # derived:corpus_min(0.70) — fallback for rules with no declared confidence
)


def is_valid_basis(label: str) -> bool:
    """True iff `label` is in the closed confidence-basis vocabulary."""
    return label in CLOSED_BASIS_EXACT or label.startswith(CLOSED_BASIS_PREFIXES)


# ---------------------------------------------------------------- declarations
@dataclass(frozen=True)
class ConfidenceRule:
    """How edges of one kind get their confidence at load/backfill/freeze time.

    basis          — a closed-vocabulary label (is_valid_basis must pass).
    value          — the declared constant, when the basis is a declared constant
                     (e.g. 1.0 for structural extraction). None when the value is
                     derived per-edge (e.g. from the source rule node).
    formula_note   — human-readable statement of the derivation, recorded so the
                     number is always traceable ("= source rule node metadata
                     confidence", "= 0.70, min observed rule confidence").
    """
    basis: str
    value: float | None = None
    formula_note: str = ""

    def __post_init__(self) -> None:
        if not is_valid_basis(self.basis):
            raise ValueError(f"basis {self.basis!r} not in closed vocabulary")
        if self.value is not None and not (0.0 < self.value <= 1.0):
            raise ValueError(f"confidence value {self.value} outside (0, 1]")


@dataclass(frozen=True)
class EdgeKind:
    """One declared edge kind.

    cycle_class routes contradiction handling (docs/04): cycles are NOT
    contradictions by default (TOKI arXiv:2606.06240 + instance-0 field notes —
    reciprocal similarity pairs are benign). A cycle triggers
    REFUSE(contradiction) only if it contains an edge whose kind declares
    cycle_class='contradiction'.
      'benign_reciprocal' — symmetric-ish kinds where A↔B cycles are expected
      'contradiction'     — kinds like `contradicts`; any cycle through them refuses
      'unclassified'      — cycles reported in analytics, never auto-refused
    """
    name: str
    confidence_rule: ConfidenceRule
    symmetric: bool = False
    cycle_class: str = "unclassified"
    source_kinds: tuple[str, ...] | None = None
    target_kinds: tuple[str, ...] | None = None

    _CYCLE_CLASSES = ("benign_reciprocal", "contradiction", "unclassified")

    def __post_init__(self) -> None:
        if self.cycle_class not in self._CYCLE_CLASSES:
            raise ValueError(f"cycle_class {self.cycle_class!r} not one of {self._CYCLE_CLASSES}")
        for label, kinds in (("source_kinds", self.source_kinds),
                             ("target_kinds", self.target_kinds)):
            if kinds is not None and (not kinds or len(set(kinds)) != len(kinds)):
                raise ValueError(f"{self.name}.{label} must be non-empty and unique when declared")

    def permits(self, source_kind: str, target_kind: str) -> bool:
        """Whether an edge between these endpoint kinds satisfies the contract."""
        return ((self.source_kinds is None or source_kind in self.source_kinds)
                and (self.target_kinds is None or target_kind in self.target_kinds))


@dataclass(frozen=True)
class Profile:
    """Table/column mapping declared by the instance.

    `claude-code-tools-kg.db` schema; the tiny fixture overrides every field."""
    nodes_table: str = "nodes"
    node_id: str = "node_id"
    node_kind: str = "node_type"
    node_name: str = "name"
    node_description: str = "description"
    node_metadata: str = "metadata"
    edges_table: str = "edges"
    edge_source: str = "source_node_id"
    edge_target: str = "target_node_id"
    edge_kind: str = "edge_type"
    edge_confidence: str = "confidence"       # added by m001; NULL after migration is refusal-grade
    edge_properties: str = "properties"       # JSON; carries confidence_basis
    edge_synthesis_chain: str = "synthesis_chain"


@dataclass(frozen=True)
class RetirementPolicy:
    """Outcome-driven retirement (SkillOps, arXiv:2605.13716): minted rules carry
    counters (times_used / times_confirmed / times_contradicted, initialized at
    freeze); retirement DEMOTES to status='dormant' with evidence recorded —
    never deletes (house append-only/supersede discipline).

    demote when: times_used >= min_uses AND
                 times_contradicted / times_used >= contradiction_ratio
    over active_cap: demote lowest utility first, utility = confirmed - contradicted.
    All values declared:planning_estimate — tunable per instance."""
    active_cap: int = 50
    min_uses: int = 5
    contradiction_ratio: float = 0.5
    utility_formula: str = "times_confirmed - times_contradicted"


@dataclass(frozen=True)
class GraphSchema:
    """The declaration. validate() is structural (pure-python, no DB): kinds
    non-empty and unique, every basis in the closed vocabulary, floor in (0,1),
    promotion_threshold >= 2 unless explicitly overridden with
    allow_single_occurrence_promotion=True (the FCL-001 human-approval path).
    Store-side validation (do declared kinds match DB reality) lives in store.py."""
    name: str
    node_kinds: tuple[str, ...]
    edge_kinds: tuple[EdgeKind, ...]
    profile: Profile = field(default_factory=Profile)
    floor: float = 0.30
    promotion_threshold: int = 2
    allow_single_occurrence_promotion: bool = False
    retirement: RetirementPolicy = field(default_factory=RetirementPolicy)

    def validate(self) -> None:
        if not self.name:
            raise ValueError("GraphSchema.name is required")
        if not self.node_kinds or len(set(self.node_kinds)) != len(self.node_kinds):
            raise ValueError("node_kinds must be non-empty and unique")
        names = [e.name for e in self.edge_kinds]
        if not names or len(set(names)) != len(names):
            raise ValueError("edge_kinds must be non-empty and unique")
        if not (0.0 < self.floor < 1.0):
            raise ValueError(f"floor {self.floor} outside (0, 1)")
        if self.promotion_threshold < 2 and not self.allow_single_occurrence_promotion:
            raise ValueError("promotion_threshold < 2 requires allow_single_occurrence_promotion=True")
        declared = set(self.node_kinds)
        for edge in self.edge_kinds:
            for label, kinds in (("source_kinds", edge.source_kinds),
                                 ("target_kinds", edge.target_kinds)):
                unknown = sorted(set(kinds or ()) - declared)
                if unknown:
                    raise ValueError(
                        f"edge kind {edge.name!r} {label} contains undeclared node kind(s) {unknown}")

    def edge_kind(self, name: str) -> EdgeKind:
        """Lookup that REFUSES on unknown kinds (EcoCorpusKG discipline): raise,
        never coerce — silent mis-typing is worse than an error."""
        for e in self.edge_kinds:
            if e.name == name:
                return e
        raise KeyError(f"edge kind {name!r} is not declared in GraphSchema {self.name!r}")

    def is_node_kind(self, kind: str) -> bool:
        return kind in self.node_kinds


# ---------------------------------------------------------------- instances
@dataclass(frozen=True)
class Instance:
    """A bound corpus: descriptor JSON + its GraphSchema module. All paths absolute."""
    name: str
    root: Path                 # directory containing instance.json
    db_path: Path
    fcl_path: Path | None
    rules_dir: Path | None
    staged_dir: Path | None
    gap_shape_history: Path | None
    adapter: dict | None       # {"kind": "subprocess", "cwd": ..., "argv": [...], "json_flag": "--json"}
    schema: GraphSchema
    observations_path: Path | None = None


def load_instance(instance_json: str | Path) -> Instance:
    """Load an instance descriptor and its graphschema.py (module-level SCHEMA).

    Relative paths in instance.json resolve against the descriptor's directory;
    descriptor paths may be absolute, but bundled instances use relative paths.
    Raises FileNotFoundError / ValueError loudly — never a silent default."""
    path = Path(instance_json).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"instance descriptor not found: {path}")
    root = path.parent
    data = json.loads(path.read_text())

    def _p(key: str, required: bool = False) -> Path | None:
        raw = data.get(key)
        if raw is None:
            if required:
                raise ValueError(f"instance.json missing required key {key!r}")
            return None
        p = Path(raw)
        return p if p.is_absolute() else (root / p).resolve()

    schema_path = _p("graphschema", required=True)
    spec = importlib.util.spec_from_file_location(f"graphschema_{data.get('name', 'x')}", schema_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    schema = getattr(mod, "SCHEMA", None)
    if not isinstance(schema, GraphSchema):
        raise ValueError(f"{schema_path} must define a module-level SCHEMA: GraphSchema")
    schema.validate()
    adapter = data.get("adapter")
    if adapter is not None:
        adapter = dict(adapter)
        raw_cwd = adapter.get("cwd")
        if raw_cwd:
            adapter_cwd = Path(raw_cwd)
            if not adapter_cwd.is_absolute():
                adapter_cwd = (root / adapter_cwd).resolve()
            adapter["cwd"] = str(adapter_cwd)

    return Instance(
        name=data.get("name") or schema.name,
        root=root,
        db_path=_p("db_path", required=True),  # type: ignore[arg-type]
        fcl_path=_p("fcl_path"),
        rules_dir=_p("rules_dir"),
        staged_dir=_p("staged_dir"),
        gap_shape_history=_p("gap_shape_history"),
        observations_path=_p("observations_path") or (root / "observations.jsonl"),
        adapter=adapter,
        schema=schema,
    )
