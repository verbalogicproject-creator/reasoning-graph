#!/usr/bin/env python3
"""Self-verifying example: declare a 4-node reasoning graph, migrate confidence,
resolve a 2-hop path, assert the exact confidence product. Ends with the house
verification line. Run: python3 examples/01_hello_traversal.py
"""
import sqlite3
import tempfile
from pathlib import Path

from reasoning_graph.schema import ConfidenceRule, EdgeKind, GraphSchema, Instance, Profile
from reasoning_graph.migrations import m001_edge_confidence
from reasoning_graph.resolver import resolve

tmp = Path(tempfile.mkdtemp(prefix="rg-ex1-"))
db = tmp / "g.db"
con = sqlite3.connect(db)
con.executescript(
    "CREATE TABLE nodes(node_id TEXT PRIMARY KEY, node_type TEXT, name TEXT, description TEXT, metadata TEXT);"
    "CREATE TABLE edges(source_node_id TEXT, target_node_id TEXT, edge_type TEXT, properties TEXT, synthesis_chain TEXT);")
for n in ("bug", "search", "fix"):
    con.execute("INSERT INTO nodes VALUES (?,?,?,?,?)", (n, "concept", n, n, "{}"))
con.execute("INSERT INTO edges (source_node_id,target_node_id,edge_type,properties,synthesis_chain) VALUES ('bug','search','implies','{}',NULL)")
con.execute("INSERT INTO edges (source_node_id,target_node_id,edge_type,properties,synthesis_chain) VALUES ('search','fix','enables','{}',NULL)")
con.commit(); con.close()

schema = GraphSchema(
    name="hello", node_kinds=("concept",),
    edge_kinds=(EdgeKind("implies", ConfidenceRule("declared:inherited_curation_default", 0.9)),
                EdgeKind("enables", ConfidenceRule("declared:inherited_curation_default", 0.8))),
    profile=Profile())
schema.validate()
inst = Instance("hello", tmp, db, None, None, None, None, None, schema)

m001_edge_confidence(inst, backup=False)
ans = resolve(inst, start="bug", end="fix")

assert ans["status"] == "ANSWER", ans
assert abs(ans["confidence"] - 0.72) < 1e-9, ans["confidence"]     # 0.9 * 0.8
assert ans["confidence_kind"] == "path_product_score"
assert ans["path_class"] == "reasoning"                            # inferential edges
print(f"bug -> search -> fix  |  confidence {ans['confidence']} ({ans['path_class']})")
print("Verify your build: ok")
