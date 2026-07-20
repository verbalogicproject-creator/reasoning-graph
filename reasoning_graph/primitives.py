"""Primitive adapters — how typed NLKE-style queries reach a graph.

Instance 0's proven primitive engine is /root/reasoning-graph/query.py (P2,
fixture 20/20). It stays FROZEN at instance level and is reached via subprocess;
this package never imports, copies, or edits it (G0 hash-guards it).

Contract, frozen by this docstring + gate G3:

PrimitiveAdapter protocol: run(primitive, args) -> dict; available() -> tuple.

class SubprocessAdapter:
    Built from instance.adapter: {"kind":"subprocess","cwd","argv","json_flag",
    "primitives"?}. Invokes the declared argv with the primitive's CLI flag
    (--<primitive-with-dashes>) followed by the arg values, plus json_flag.
    Parses the JSON, returns it untouched + provenance keys _adapter/_argv only.
    Timeout 120s; non-zero exit or bad JSON → AdapterError (the resolver
    surfaces it, never fabricates a result).

class GenericAdapter:
    Thin, corpus-agnostic implementations over Store for graphs with no instance
    engine (tiny fixture; corpus 2). Ships want_to / can_it / trace / why_not
    only — deliberately smaller than query.py; parity is a ROADMAP item, not
    silently faked.

adapter_for(instance) -> PrimitiveAdapter: SubprocessAdapter if the instance
    declares a subprocess adapter, else GenericAdapter.
"""
from __future__ import annotations

import json
import subprocess

_DEFAULT_PRIMITIVES = ("want_to", "can_it", "trace", "why_not", "similar_to",
                       "compose_for", "alternatives")
_GENERIC_PRIMITIVES = ("want_to", "can_it", "trace", "why_not")


class AdapterError(Exception):
    pass


class SubprocessAdapter:
    def __init__(self, instance):
        cfg = instance.adapter or {}
        self.cwd = cfg.get("cwd")
        self.argv = list(cfg.get("argv", []))
        self.json_flag = cfg.get("json_flag", "--json")
        self._primitives = tuple(cfg.get("primitives", _DEFAULT_PRIMITIVES))

    def available(self) -> tuple:
        return self._primitives

    def run(self, primitive: str, args: dict) -> dict:
        flag = "--" + primitive.replace("_", "-")
        argv = self.argv + [flag] + [str(v) for v in args.values()] + [self.json_flag]
        try:
            cp = subprocess.run(argv, cwd=self.cwd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired as exc:
            raise AdapterError(f"adapter timeout: {' '.join(argv)}") from exc
        except FileNotFoundError as exc:
            raise AdapterError(str(exc)) from exc
        if cp.returncode != 0:
            raise AdapterError(f"adapter exit {cp.returncode}: {(cp.stderr or cp.stdout)[-300:]}")
        try:
            data = json.loads(cp.stdout)
        except json.JSONDecodeError as exc:
            raise AdapterError(f"adapter produced non-JSON: {cp.stdout[:200]}") from exc
        prov = {"_adapter": "subprocess", "_argv": argv}
        return {**data, **prov} if isinstance(data, dict) else {"result": data, **prov}


class GenericAdapter:
    """Corpus-agnostic primitives over Store — honestly smaller than a tuned
    instance engine. Every result carries _adapter='generic'."""

    def __init__(self, instance):
        self.instance = instance

    def available(self) -> tuple:
        return _GENERIC_PRIMITIVES

    def _store(self):
        from .store import Store
        return Store.open(self.instance)

    @staticmethod
    def _matches(text, goal) -> bool:
        words = [w for w in goal.lower().split() if len(w) > 2]
        blob = (text or "").lower()
        return any(w in blob for w in words)

    def run(self, primitive: str, args: dict) -> dict:
        if primitive not in _GENERIC_PRIMITIVES:
            raise AdapterError(f"GenericAdapter does not implement {primitive!r} "
                               f"(available: {_GENERIC_PRIMITIVES}) — parity is a ROADMAP item")
        method = getattr(self, f"_{primitive}")
        return {"_adapter": "generic", "primitive": primitive, **method(args)}

    def _want_to(self, args) -> dict:
        goal = args.get("goal", "")
        with self._store() as s:
            hits = [{"id": n["id"], "name": n["name"]} for n in s.nodes()
                    if self._matches(n["name"], goal) or self._matches(n["description"], goal)]
        return {"goal": goal, "results": hits[:10]}

    def _can_it(self, args) -> dict:
        cap = args.get("capability", "")
        r = self._want_to({"goal": cap})
        return {"capability": cap, "can": bool(r["results"]), "related": r["results"][:5]}

    def _trace(self, args) -> dict:
        from .resolver import resolve
        a = resolve(self.instance, start=args.get("from"), end=args.get("to"))
        return {"from": args.get("from"), "to": args.get("to"),
                "status": a["status"], "path": a["path"], "confidence": a["confidence"]}

    def _why_not(self, args) -> dict:
        node = args.get("node") or args.get("tool")
        with self._store() as s:
            outs = [{"target": e["target"], "edge_type": e["kind"]}
                    for e in s.neighbors(node, "out")]
        return {"node": node, "outgoing": outs}


def adapter_for(instance):
    cfg = instance.adapter or {}
    if cfg.get("kind") == "subprocess":
        return SubprocessAdapter(instance)
    return GenericAdapter(instance)
