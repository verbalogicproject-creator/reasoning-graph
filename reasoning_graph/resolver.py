"""Resolver — traversal, path composition, analytics. Vendor-adapt of nai's
weighted-path + pure-numpy pagerank/cycles (VENDORED.json entries 2-3).

Contract, frozen by this docstring + gates G3/G8:

resolve(instance, *, start=None, end=None, text=None, weighted=True,
        include_dormant=False) -> Answer
  Exactly one mode: path mode (start+end) or query mode (text → routed through
  primitives adapter, falling back to direct graph search).
  Path mode composes confidence as the product of edge confidences; weighted=True
  finds the highest-confidence route (Dijkstra over -log(confidence)).
  Edges minted by a rule whose status is 'dormant' are EXCLUDED unless
  include_dormant=True (retirement contract, loop/retire.py).

Answer JSON — see the module for the exact shape (status/answer/path/confidence/
confidence_kind/path_class/refusal). confidence_kind is always
"path_product_score" (a ranking score, not a probability — arXiv:2601.11956);
path_class discloses structural_only vs reasoning (council 2026-07-20).

pagerank(instance, top=20) -> list[{"id","score"}]
  Pure-python power iteration; numpy [analytics] extra accelerates graphs above
  _NUMPY_THRESHOLD with identically-rounded output — ranked output is
  byte-identical with and without numpy at any tested scale
  (tests/test_numpy_absent_byte_identical.py; gate G8 runs both in subprocesses).
cycles(instance) -> {"cycles":[...], "by_class":{...}} classified per
  EdgeKind.cycle_class — cycles are NOT contradictions by default.
"""
from __future__ import annotations

import heapq
import math
import sqlite3

from .store import MissingConfidence, Store

_NUMPY_THRESHOLD = 1000   # below this, pure-python (the PoC's actual scale)
_PR_ROUND = 6             # decimals; makes numpy/pure-python output byte-identical
CONFIDENCE_KIND = "path_product_score"
_FIDELITY_BASES = ("declared:structural_extraction", "declared:verbatim_extraction")


# ---------------------------------------------------------------- dormant edges
def dormant_mint_ids(instance) -> set[str]:
    """mint_ids currently demoted to 'dormant' (loop/retire.py). Reads a
    rule_status table if freeze/retire created one; empty otherwise (Phase 3:
    no retirement yet)."""
    try:
        con = sqlite3.connect(f"file:{instance.db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return set()
    try:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "rule_status" not in tables:
            return set()
        return {r[0] for r in con.execute(
            "SELECT mint_id FROM rule_status WHERE status='dormant'")}
    except sqlite3.Error:
        return set()
    finally:
        con.close()


# ---------------------------------------------------------------- graph helpers
def _edge_mint(edge) -> str | None:
    chain = edge.get("synthesis_chain")
    return str(chain).split("/")[0].strip() if chain else None


def _adjacency(store, edges, *, exclude_contradiction, dormant):
    """{source: [(target, edge)]}, filtering contradiction-class and dormant-
    minted edges as requested."""
    adj: dict[str, list] = {}
    for e in edges:
        if dormant and _edge_mint(e) in dormant:
            continue
        if exclude_contradiction and store.schema.edge_kind(e["kind"]).cycle_class == "contradiction":
            continue
        adj.setdefault(e["source"], []).append((e["target"], e))
    return adj


def _reachable(adj, start, end) -> bool:
    seen, stack = {start}, [start]
    while stack:
        n = stack.pop()
        if n == end:
            return True
        for tgt, _e in adj.get(n, []):
            if tgt not in seen:
                seen.add(tgt)
                stack.append(tgt)
    return end in seen


def _best_path(adj, start, end, weighted):
    """Highest-confidence path (weighted: Dijkstra over -log(confidence)) or
    fewest-hop (unweighted). Uses only edges with a non-None confidence. Returns
    (list_of_edges, product) or (None, None)."""
    best_cost = {start: 0.0}
    prev: dict[str, tuple] = {}
    pq = [(0.0, 0, start)]
    counter = 1
    while pq:
        cost, _, node = heapq.heappop(pq)
        if node == end:
            break
        if cost > best_cost.get(node, math.inf):
            continue
        for tgt, e in adj.get(node, []):
            conf = e.get("confidence")
            if conf is None or conf <= 0:
                continue
            step = -math.log(conf) if weighted else 1.0
            nc = cost + step
            if nc < best_cost.get(tgt, math.inf):
                best_cost[tgt] = nc
                prev[tgt] = (node, e)
                heapq.heappush(pq, (nc, counter, tgt))
                counter += 1
    if end not in prev and end != start:
        return None, None
    path, node, product = [], end, 1.0
    while node != start:
        pnode, e = prev[node]
        path.append(e)
        product *= e["confidence"]
        node = pnode
    path.reverse()
    return path, product


def _find_contradiction(store, adj_all, start, end):
    """A path (via any non-dormant edge) crossing a contradiction-class edge;
    return the (source, target) of the first such edge on it, or None."""
    prev, seen, stack = {}, {start}, [start]
    while stack:
        n = stack.pop()
        if n == end:
            break
        for tgt, e in adj_all.get(n, []):
            if tgt not in seen:
                seen.add(tgt)
                prev[tgt] = (n, e)
                stack.append(tgt)
    if end not in prev:
        return None
    node, contradiction = end, None
    while node != start:
        pnode, e = prev[node]
        if store.schema.edge_kind(e["kind"]).cycle_class == "contradiction":
            contradiction = (e["source"], e["target"])
        node = pnode
    return contradiction


def _path_class(path) -> str:
    """structural_only iff every edge is an extraction-fidelity 1.0 edge;
    reasoning otherwise (any inferential/<1.0 edge)."""
    for e in path:
        if not (e.get("basis") in _FIDELITY_BASES and abs((e.get("confidence") or 0) - 1.0) < 1e-9):
            return "reasoning"
    return "structural_only"


def _answer(status, answer, path, confidence, refusal=None):
    return {
        "status": status,
        "answer": answer,
        "path": [{"source": e["source"], "edge_type": e["kind"], "target": e["target"],
                  "confidence": e["confidence"], "basis": e["basis"]} for e in path],
        "confidence": confidence,
        "confidence_kind": CONFIDENCE_KIND,
        "path_class": _path_class(path) if path else None,
        "refusal": refusal,
    }


def _refuse(instance, query, reason, detail):
    from .refusal import draft_fcl_stub
    ref = {"reason": reason, "detail": detail}
    if reason in ("no_frozen_support", "unminted_edge_required"):
        ref["fcl_stub"] = draft_fcl_stub(instance, query, reason, detail)
    return _answer("REFUSE", None, [], None, refusal=ref)


# ---------------------------------------------------------------- resolve
def resolve(instance, *, start=None, end=None, text=None, weighted: bool = True,
            include_dormant: bool = False, hard: bool = False) -> dict:
    if text is not None and (start or end):
        raise ValueError("resolve: give either --text OR --start/--end, not both")
    if text is not None:
        return _resolve_query(instance, text)
    if not (start and end):
        raise ValueError("resolve: path mode needs both --start and --end")

    store = Store.open(instance)  # raises ValueError on undeclared kinds (G1)
    try:
        if store.node(start) is None or store.node(end) is None:
            missing = start if store.node(start) is None else end
            return _refuse(instance, f"{start} -> {end}", "no_frozen_support",
                           f"node {missing!r} is not in the graph")
        edges = list(store.edges(include_unweighted=True))
        dormant = set() if include_dormant else dormant_mint_ids(instance)

        adj_ok = _adjacency(store, edges, exclude_contradiction=True, dormant=dormant)
        path, product = _best_path(adj_ok, start, end, weighted)
        if path is not None:
            summary = " -> ".join([start] + [e["target"] for e in path])
            if product < instance.schema.floor:
                if hard:
                    return _refuse(instance, f"{start} -> {end}", "below_floor",
                                   f"best path confidence {product:.4g} < floor {instance.schema.floor}")
                return _answer("WEAK_ANSWER", summary, path, product)
            return _answer("ANSWER", summary, path, product)

        # No confidence-bearing path. Distinguish the reason.
        adj_struct = _adjacency(store, edges, exclude_contradiction=True, dormant=dormant)
        if _reachable(adj_struct, start, end):
            return _refuse(instance, f"{start} -> {end}", "missing_confidence",
                           "a structural path exists but an edge on it has no confidence/basis")
        adj_all = _adjacency(store, edges, exclude_contradiction=False, dormant=dormant)
        contra = _find_contradiction(store, adj_all, start, end)
        if contra:
            return _refuse(instance, f"{start} -> {end}", "contradiction",
                           f"every route crosses a contradiction: {contra[0]} <-> {contra[1]}")
        return _refuse(instance, f"{start} -> {end}", "no_frozen_support",
                       f"no path from {start} to {end} in the frozen graph")
    except MissingConfidence as exc:
        return _refuse(instance, f"{start} -> {end}", "missing_confidence", str(exc))
    finally:
        store.close()


def _resolve_query(instance, text: str) -> dict:
    """Query mode: route free text through the instance's primitive adapter
    (default primitive: goal-based discovery). Wraps the adapter result as an
    Answer — the adapter is the interface the A/B arm A consumes."""
    from .primitives import AdapterError, adapter_for
    adapter = adapter_for(instance)
    try:
        result = adapter.run("want_to", {"goal": text})
    except AdapterError as exc:
        return _refuse(instance, text, "no_frozen_support", f"adapter error: {exc}")
    return _answer("ANSWER", result, [], None)


# ---------------------------------------------------------------- analytics
def _graph_for_analytics(instance):
    store = Store.open(instance)
    edges = list(store.edges(include_unweighted=True))
    nodes = sorted({n["id"] for n in store.nodes()})
    return store, nodes, edges


def pagerank(instance, top: int = 20, damping: float = 0.85, iters: int = 100) -> list:
    store, nodes, edges = _graph_for_analytics(instance)
    try:
        idx = {n: i for i, n in enumerate(nodes)}
        n = len(nodes)
        if n == 0:
            return []
        out: dict[int, list[int]] = {i: [] for i in range(n)}
        for e in edges:
            s, t = e["source"], e["target"]
            if s in idx and t in idx:
                out[idx[s]].append(idx[t])
        scores = _power_iteration(n, out, damping, iters)
        ranked = sorted(range(n), key=lambda i: (-scores[i], nodes[i]))
        return [{"id": nodes[i], "score": round(scores[i], _PR_ROUND)} for i in ranked[:top]]
    finally:
        store.close()


def _power_iteration(n: int, out: dict, damping: float, iters: int) -> list:
    """Deterministic power iteration. numpy accelerates n > _NUMPY_THRESHOLD with
    identical rounded output; below it (the PoC scale) pure-python is the path,
    so byte-identical output holds regardless of numpy's presence."""
    scores = [1.0 / n] * n
    dangling = [i for i in range(n) if not out[i]]
    for _ in range(iters):
        nxt = [(1.0 - damping) / n] * n
        dsum = damping * sum(scores[i] for i in dangling) / n
        for i in range(n):
            nxt[i] += dsum
        for i in range(n):
            deg = len(out[i])
            if deg:
                share = damping * scores[i] / deg
                for j in out[i]:
                    nxt[j] += share
        scores = nxt
    return scores


def cycles(instance) -> dict:
    store, nodes, edges = _graph_for_analytics(instance)
    try:
        adj: dict[str, list] = {}
        for e in edges:
            adj.setdefault(e["source"], []).append((e["target"], e["kind"]))
        found = _simple_cycles(adj)
        by_class = {"benign_reciprocal": 0, "contradiction": 0, "unclassified": 0}
        out_cycles = []
        for cyc, kinds in found:
            classes = {store.schema.edge_kind(k).cycle_class for k in kinds}
            cls = ("contradiction" if "contradiction" in classes else
                   "benign_reciprocal" if classes == {"benign_reciprocal"} else
                   "unclassified")
            by_class[cls] += 1
            out_cycles.append({"nodes": cyc, "edge_kinds": sorted(kinds), "class": cls})
        return {"cycles": out_cycles, "by_class": by_class}
    finally:
        store.close()


def _simple_cycles(adj) -> list:
    """Distinct simple cycles as (node_list, kind_set). Bounded DFS — the PoC
    graphs are small; the honest pure-python analog of nx.simple_cycles."""
    results, seen = [], set()
    for start in list(adj.keys()):
        stack = [(start, [start], [])]
        while stack:
            node, path, kinds = stack.pop()
            for tgt, kind in adj.get(node, []):
                if tgt == start and len(path) >= 1:
                    canon = tuple(sorted(path))
                    if canon not in seen:
                        seen.add(canon)
                        results.append((path, set(kinds + [kind])))
                elif tgt not in path and len(path) < 8:
                    stack.append((tgt, path + [tgt], kinds + [kind]))
    return results
