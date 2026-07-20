"""Resolver — traversal, path composition, analytics. Vendor-adapt of nai's
weighted-path + pure-numpy pagerank/cycles (VENDORED.json entries 2-3).

OPUS-FILLS (Phase 3). Contract, frozen by this docstring + gates G3/G8:

resolve(instance, *, start=None, end=None, text=None, weighted=True,
        include_dormant=False) -> Answer
  Exactly one mode: path mode (start+end) or query mode (text → routed through
  primitives adapter, falling back to direct graph search).
  Path mode composes confidence as the product of edge confidences; weighted=True
  finds the highest-confidence route (Dijkstra over -log(confidence)).
  Edges minted by a rule whose status is 'dormant' are EXCLUDED unless
  include_dormant=True (retirement contract, loop/retire.py).

Answer JSON (the shape every gate asserts; CLI prints it verbatim):
  {"status": "ANSWER" | "WEAK_ANSWER" | "REFUSE",
   "answer": str | dict | None,
   "path": [{"source": str, "edge_type": str, "target": str,
             "confidence": float, "basis": str}],
   "confidence": float | None,
   "confidence_kind": "path_product_score",   # a ranking score, NOT a calibrated
                                              # probability (arXiv:2601.11956);
                                              # never rename, never omit
   "path_class": "reasoning" | "structural_only" | null,
                 # DISCLOSED ASYMMETRY (council 2026-07-20): the product mixes
                 # extraction-fidelity 1.0s with inferential-trust <1.0s, so an
                 # all-1.0 structural walk always outranks any inferential path.
                 # A path whose every edge carries a declared 1.0 (structural/
                 # verbatim basis) is labeled structural_only — "a fact walk,
                 # not reasoning composition" — visible in every Answer, never
                 # absorbed into one float.
   "refusal": null | {"reason": str, "detail": str, "fcl_stub": str}}
Status rules (refusal.py owns the decision):
  ANSWER       — path/result found, composed confidence >= schema.floor
  WEAK_ANSWER  — found but composed confidence < floor (honest, never hidden)
  REFUSE       — see refusal.py reasons enum

pagerank(instance, top=20) -> list[{"id", "score"}]
  Pure-python power iteration; numpy [analytics] extra is a speed booster ONLY —
  ranked output must be byte-identical with and without numpy
  (tests/test_numpy_absent_byte_identical.py; gate G8 runs both in subprocesses).
cycles(instance) -> {"cycles": [...], "by_class": {"benign_reciprocal": n,
  "contradiction": n, "unclassified": n}}
  Classification per EdgeKind.cycle_class — cycles are NOT contradictions by
  default (TOKI arXiv:2606.06240 + instance-0 field notes).
"""
from __future__ import annotations


def resolve(instance, *, start=None, end=None, text=None, weighted: bool = True,
            include_dormant: bool = False) -> dict:
    raise NotImplementedError("OPUS-FILLS: Phase 3 — see module docstring + SoT")


def pagerank(instance, top: int = 20) -> list:
    raise NotImplementedError("OPUS-FILLS: Phase 3 — see module docstring + SoT")


def cycles(instance) -> dict:
    raise NotImplementedError("OPUS-FILLS: Phase 3 — see module docstring + SoT")
