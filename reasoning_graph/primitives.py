"""Primitive adapters — how typed NLKE-style queries reach a graph.

Instance 0's proven primitive engine is /root/reasoning-graph/query.py (P2,
fixture 20/20). It stays FROZEN at instance level and is reached via subprocess;
this package never imports, copies, or edits it (G0 hash-guards it).

OPUS-FILLS (Phase 3). Contract, frozen by this docstring + gate G3:

class PrimitiveAdapter(Protocol):
    def run(self, primitive: str, args: dict) -> dict: ...
    def available(self) -> tuple[str, ...]: ...

class SubprocessAdapter(PrimitiveAdapter):
    Built from instance.adapter: {"kind": "subprocess", "cwd": str,
    "argv": [...], "json_flag": "--json"}. Invokes the declared argv with the
    primitive's CLI flags, parses the JSON, returns it untouched (provenance:
    the adapter adds {"_adapter": "subprocess", "_argv": [...]} only).
    Timeout 120s; non-zero exit or bad JSON → raise AdapterError (the resolver
    surfaces it, never fabricates a result).

class GenericAdapter(PrimitiveAdapter):
    Thin, corpus-agnostic implementations over Store/resolver for graphs with no
    instance engine (the tiny fixture; corpus 2). Ships want_to / can_it /
    trace / why_not only — deliberately smaller than query.py; parity is a
    ROADMAP item, not silently faked.
"""
from __future__ import annotations


class AdapterError(Exception):
    pass


class SubprocessAdapter:  # OPUS-FILLS per module docstring contract
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("OPUS-FILLS: Phase 3 — see module docstring + SoT")


class GenericAdapter:  # OPUS-FILLS per module docstring contract
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("OPUS-FILLS: Phase 3 — see module docstring + SoT")
