"""reasoning-graph — declared, confidence-weighted reasoning graphs.

Reasoning retrieved by traversal instead of re-derived in prose; misses feed a
mechanized mint→verify→freeze→retire loop. Rung-0 lowering applied to reasoning.

Public surface (kept 1:1 with docs/08-api-reference.md):
  GraphSchema, NodeKind-free by design (kinds are strings validated by schema),
  EdgeKind, ConfidenceRule, Profile, RetirementPolicy, Instance, load_instance,
  CLOSED_BASIS_EXACT, CLOSED_BASIS_PREFIXES, is_valid_basis.
Implementation modules (store/resolver/refusal/loop/measure) are filled by the
Opus build session against the SoT contract; their import here is deliberate so
`import reasoning_graph` fails loudly if a module is syntactically broken.
"""
__version__ = "0.1.0"

from .schema import (  # noqa: F401
    CLOSED_BASIS_EXACT,
    CLOSED_BASIS_PREFIXES,
    ConfidenceRule,
    EdgeKind,
    GraphSchema,
    Instance,
    Profile,
    RetirementPolicy,
    is_valid_basis,
    load_instance,
)
