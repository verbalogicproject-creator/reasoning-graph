#!/usr/bin/env python3
"""Build the second-corpus DB (lowering-ladder domain) — a genuinely different
domain from claude-code-tools, with confidence already populated. Run:
    python3 instances/lowering_ladder/build_ll.py
"""
import json, sqlite3, sys
from pathlib import Path

DB = Path(__file__).parent / "ll.db"
NODES = [
    ("rung_3_prose", "rung", "Rung 3: Prose"), ("rung_2_code", "rung", "Rung 2: Code"),
    ("rung_1_data", "rung", "Rung 1: Data/Declared"), ("rung_0_precomputed", "rung", "Rung 0: Precomputed"),
    ("skill_deploy", "skill", "Deploy skill"), ("concept_orphan", "concept", "Uncatalogued concept"),
    ("goal_x", "concept", "A goal"), ("claim_a", "concept", "Claim A"),
    ("claim_b", "concept", "Claim B (conflicts with A)"), ("hunch_target", "concept", "A hunch"),
]
# (source, target, kind, confidence, basis)
EDGES = [
    ("rung_3_prose", "rung_2_code", "lowers_to", 1.0, "declared:structural_extraction"),
    ("rung_2_code", "rung_1_data", "lowers_to", 1.0, "declared:structural_extraction"),
    ("rung_1_data", "rung_0_precomputed", "lowers_to", 1.0, "declared:structural_extraction"),
    ("skill_deploy", "rung_2_code", "sits_on", 1.0, "declared:verbatim_extraction"),
    ("rung_3_prose", "hunch_target", "hunch", 0.2, "declared:initial_guess"),
    ("goal_x", "claim_a", "needs", 1.0, "declared:structural_extraction"),
    ("claim_a", "claim_b", "contradicts", 0.85, "declared:initial_guess"),
]

def build():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(
        "CREATE TABLE nodes(node_id TEXT PRIMARY KEY, node_type TEXT, name TEXT, description TEXT, metadata TEXT);"
        "CREATE TABLE edges(source_node_id TEXT, target_node_id TEXT, edge_type TEXT, confidence REAL, properties TEXT, synthesis_chain TEXT);")
    con.executemany("INSERT INTO nodes VALUES (?,?,?,?,'{}')",
                    [(nid, kind, name, name) for nid, kind, name in NODES])
    con.executemany("INSERT INTO edges VALUES (?,?,?,?,?,NULL)",
                    [(s, t, k, c, json.dumps({"confidence_basis": b})) for s, t, k, c, b in EDGES])
    con.commit(); con.close()
    print(f"ll.db built: {len(NODES)} nodes, {len(EDGES)} edges")

if __name__ == "__main__":
    build()
