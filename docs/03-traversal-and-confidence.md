# 03 — Traversal and confidence math

`resolve(instance, start=, end=)` finds the highest-confidence path via Dijkstra over `-log(confidence)` (weighted, the default) or fewest-hop (unweighted), composing confidence as the **product** of edge confidences. The result carries `confidence_kind: "path_product_score"` — a ranking score, **not a calibrated probability** (arXiv:2601.11956).

`path_class` discloses the product's asymmetry: a path whose every edge is an extraction-fidelity 1.0 edge is `structural_only` (a fact walk), otherwise `reasoning` (it crosses an inferential edge). This keeps a fact-walk from being presented as reasoning composition.

`pagerank` is pure-python power iteration (numpy accelerates large graphs with identically-rounded output, so results are byte-identical with or without numpy at any tested scale). `cycles` classifies each cycle per `EdgeKind.cycle_class` — cycles are **not** contradictions by default (benign reciprocal pairs are data).
