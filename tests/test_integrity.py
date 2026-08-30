from __future__ import annotations

import json
import sqlite3
from dataclasses import replace

from reasoning_graph.schema import load_instance
from reasoning_graph.store import Store, inspect_integrity


def _with_endpoint_contract(inst):
    edges = []
    for edge in inst.schema.edge_kinds:
        if edge.name == "tunes":
            edge = replace(edge, source_kinds=("spindle",), target_kinds=("dye_bath",))
        edges.append(edge)
    return replace(inst, schema=replace(inst.schema, edge_kinds=tuple(edges)))


def test_integrity_report_clean_and_writer_enables_foreign_keys(tiny_instance):
    inst = _with_endpoint_contract(load_instance(tiny_instance))
    report = inspect_integrity(inst)
    assert report["ok"] is True
    assert report["counts"] == {"nodes": 10, "edges": 9}
    assert report["duplicate_typed_relationships"] == []
    with Store.open(inst).writer() as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_integrity_detects_all_contract_failures(tiny_instance):
    inst = _with_endpoint_contract(load_instance(tiny_instance))
    p = inst.schema.profile
    con = sqlite3.connect(inst.db_path)
    basis = json.dumps({"confidence_basis": "declared:initial_guess"})
    rows = [
        ("spindle_a", "dye_bath_2", "tunes", 0.95, basis, None),
        ("loom_1", "dye_bath_2", "tunes", 0.5, basis, None),
        ("loom_1", "missing_node", "feeds", 0.5, basis, None),
        ("loom_1", "spindle_a", "feeds", None, "{}", None),
        ("loom_1", "spindle_a", "unknown_edge", 0.5, basis, None),
    ]
    con.executemany(f"INSERT INTO {p.edges_table} VALUES (?,?,?,?,?,?)", rows)
    con.execute(f"INSERT INTO {p.nodes_table} VALUES (?,?,?,?,?)",
                ("alien_1", "alien_kind", "Alien", "", "{}"))
    con.commit()
    con.close()

    report = inspect_integrity(inst)
    assert report["ok"] is False
    assert report["unknown_node_kinds"] == ["alien_kind"]
    assert report["unknown_edge_kinds"] == ["unknown_edge"]
    assert any(item["target"] == "missing_node" for item in report["missing_endpoints"])
    assert any(item["kind"] == "tunes" and item["source_kind"] == "loom"
               for item in report["invalid_endpoint_kinds"])
    assert any(item["problem"] == "confidence" for item in report["missing_confidence"])
    assert any(item["kind"] == "tunes" and item["count"] == 2
               for item in report["duplicate_typed_relationships"])
