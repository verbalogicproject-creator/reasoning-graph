"""Reasoning Graph — governed, confidence-weighted reasoning memory.

The package retrieves inspectable graph paths, exposes weak/refusal outcomes,
records bounded observations, and keeps memory activation human-gated.

Core public surface:
  GraphSchema, NodeKind-free by design (kinds are strings validated by schema),
  EdgeKind, ConfidenceRule, Profile, RetirementPolicy, Instance, load_instance,
  CLOSED_BASIS_EXACT, CLOSED_BASIS_PREFIXES, is_valid_basis.
"""
__version__ = "0.2.0"

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
