"""Deterministic demo (gate G8). Builds a small declared graph in a temp dir,
then runs schema-validate -> migrate -> three resolves (ANSWER / WEAK_ANSWER /
REFUSE(contradiction)) over it, printing each step's one-line result. Fully
deterministic (no wall-clock in output, no RNG, no network). MUST end with:

Verify your build: ok
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

from .migrations import m001_edge_confidence
from .resolver import resolve
from .schema import ConfidenceRule, EdgeKind, GraphSchema, Instance, Profile


def _build(db: Path) -> None:
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE nodes (node_id TEXT PRIMARY KEY, node_type TEXT, name TEXT,
                            description TEXT, metadata TEXT);
        CREATE TABLE edges (source_node_id TEXT, target_node_id TEXT, edge_type TEXT,
                            properties TEXT, synthesis_chain TEXT);
    """)
    pts = ["a", "b", "c", "d", "e", "f", "g"]
    con.executemany("INSERT INTO nodes VALUES (?,?,?,?,?)",
                    [(p, "point", p.upper(), f"point {p}", "{}") for p in pts])
    # bare edges (NULL confidence) — m001 backfills from the declared rules
    edges = [("a", "b", "leads"), ("b", "c", "leads"), ("a", "d", "hunch"),
             ("a", "e", "leads"), ("e", "f", "contradicts"), ("f", "g", "leads")]
    con.executemany("INSERT INTO edges (source_node_id,target_node_id,edge_type,properties,"
                    "synthesis_chain) VALUES (?,?,?,'{}',NULL)", edges)
    con.commit()
    con.close()


def _instance(root: Path) -> Instance:
    schema = GraphSchema(
        name="demo_points",
        node_kinds=("point",),
        edge_kinds=(
            EdgeKind("leads", ConfidenceRule("declared:structural_extraction", 1.0)),
            EdgeKind("hunch", ConfidenceRule("declared:initial_guess", 0.20)),
            EdgeKind("contradicts", ConfidenceRule("declared:initial_guess", 0.85),
                     cycle_class="contradiction"),
        ),
        profile=Profile(),   # defaults match the nodes/edges tables built above
    )
    schema.validate()
    return Instance(name="demo", root=root, db_path=root / "demo.db", fcl_path=None,
                    rules_dir=None, staged_dir=None, gap_shape_history=None,
                    adapter=None, schema=schema)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="rg-demo-"))
    db = tmp / "demo.db"
    _build(db)
    inst = _instance(tmp)

    inst.schema.validate()
    print(f"[1] schema '{inst.schema.name}' validates: "
          f"{len(inst.schema.node_kinds)} node kind(s), {len(inst.schema.edge_kinds)} edge kind(s)")

    rep = m001_edge_confidence(inst, backup=False)
    print(f"[2] migrate m001: backfilled {rep['backfilled']} edges, "
          f"null_remaining={rep['null_remaining']}")

    ans = resolve(inst, start="a", end="c")
    print(f"[3] resolve a->c : {ans['status']} confidence={ans['confidence']} "
          f"class={ans['path_class']} (a fact walk composes to certainty)")

    weak = resolve(inst, start="a", end="d")
    print(f"[4] resolve a->d : {weak['status']} confidence={weak['confidence']} "
          f"(below floor {inst.schema.floor} — honest, not hidden)")

    ref = resolve(inst, start="a", end="g")
    print(f"[5] resolve a->g : {ref['status']} "
          f"reason={ref['refusal']['reason']} (the only route crosses a contradiction)")

    ok = (ans["status"] == "ANSWER" and abs(ans["confidence"] - 1.0) < 1e-9
          and weak["status"] == "WEAK_ANSWER" and abs(weak["confidence"] - 0.20) < 1e-9
          and ref["status"] == "REFUSE" and ref["refusal"]["reason"] == "contradiction")
    if not ok:
        print("demo self-check FAILED")
        return 1
    print("Verify your build: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
