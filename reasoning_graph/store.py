"""Store — sqlite substrate, profile-driven. Vendor-adapt of nai's KGManager
(VENDORED.json entry 1; source /root/reasoning-graph/systems/nai/kg_manager.py).

OPUS-FILLS (Phase 1). Contract, frozen by this docstring + gates G1/G2:

class MissingConfidence(Exception): raised whenever an edge's confidence is
    NULL/absent. NEVER default to 1.0 — the original nai edge_weight() defaults
    to 1.0; that behavior is the bug this framework exists to kill. The resolver
    converts MissingConfidence into REFUSE(reason="missing_confidence").

class Store:
    @classmethod open(instance: Instance) -> Store
        Opens read-only by default. Validates DB reality against the declared
        GraphSchema: any node kind or edge kind present in the DB but not
        declared → raise ValueError (list the offenders). Unknown-kind = error,
        never coercion.
    nodes(kind: str | None = None) -> iterator of {"id","kind","name","description","metadata"}
    edges(kind: str | None = None) -> iterator of
        {"source","target","kind","confidence","basis","properties","synthesis_chain"}
        basis is read from properties JSON key "confidence_basis";
        missing/NULL confidence or basis → MissingConfidence (unless
        include_unweighted=True, used only by `migrate --dry-run` reporting).
    edge_confidence(source, target, kind) -> (float, str)   # (value, basis)
    neighbors(node_id, direction="both") -> list of edge dicts
    write access exists ONLY for migrations.py and loop/freeze.py + loop/retire.py
        (writer(instance) context manager that takes an exclusive connection,
        journal-safe). Everything else is read-only by construction.

Every SQL identifier comes from instance.schema.profile — zero literal table or
column names in this module (gate G1 greps; the tiny fixture's non-default
names prove it).
"""
from __future__ import annotations


class MissingConfidence(Exception):
    """An edge without a confidence value/basis was consulted (refusal-grade)."""


class Store:  # OPUS-FILLS per module docstring contract
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("OPUS-FILLS: Phase 1 — see module docstring + SoT")
