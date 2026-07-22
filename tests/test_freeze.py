"""Freeze invariant 8 — idempotent on synthesis_chain."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from reasoning_graph.schema import load_instance
from reasoning_graph.loop import mint, freeze
from _loopmatcher import MATCHER


def _minted(db):
    con = sqlite3.connect(db)
    n = con.execute("SELECT COUNT(*) FROM ties WHERE chain_tag LIKE 'mint_t_test%'").fetchone()[0]
    con.close()
    return n


def test_inv_freeze_idempotent(tiny_instance):
    inst = load_instance(tiny_instance)
    staged = mint.stage(inst, "FIX-005", MATCHER)["staged_path"]
    r1 = freeze.freeze(inst, staged)
    assert r1["edges_inserted"] == 1 and r1["already_frozen"] is False
    r2 = freeze.freeze(inst, staged)
    assert r2["already_frozen"] is True and _minted(inst.db_path) == 1


def test_freeze_writes_fact_loop_rows_and_counters(tiny_instance):
    inst = load_instance(tiny_instance)
    staged = mint.stage(inst, "FIX-005", MATCHER)["staged_path"]
    r = freeze.freeze(inst, staged)
    assert r["rows"]["rule_status"] == 1 and r["rows"]["evolution_log"] == 1
    con = sqlite3.connect(inst.db_path)
    conf, basis = con.execute("SELECT trust, extra_json FROM ties WHERE chain_tag LIKE 'mint_t_test%'").fetchone()
    con.close()
    import json
    assert abs(conf - 0.75) < 1e-9
    assert json.loads(basis)["confidence_basis"] == "declared:matcher:mint_t_test"


def test_freeze_requires_approve_on_non_self_approve(tiny_instance):
    import pytest, json
    p = Path(tiny_instance)
    data = json.loads(p.read_text()); data["self_approve"] = False; p.write_text(json.dumps(data))
    inst = load_instance(p)
    staged = mint.stage(inst, "FIX-005", MATCHER)["staged_path"]
    with pytest.raises(PermissionError):
        freeze.freeze(inst, staged)
