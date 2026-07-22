"""m001 — backfills a bare tiny copy; idempotent; dry-run writes nothing."""
from __future__ import annotations
import sqlite3
from reasoning_graph.schema import load_instance
from reasoning_graph.migrations import m001_edge_confidence


def _nulls(db):
    con = sqlite3.connect(db); n = con.execute("SELECT COUNT(*) FROM ties WHERE trust IS NULL").fetchone()[0]; con.close()
    return n


def test_m001_backfills_bare_tiny(tiny_instance_bare):
    inst = load_instance(tiny_instance_bare)
    assert _nulls(inst.db_path) == 9
    rep = m001_edge_confidence(inst, backup=False)
    assert rep["null_remaining"] == 0 and rep["backfilled"] == 9


def test_m001_idempotent_second_run_zero(tiny_instance_bare):
    inst = load_instance(tiny_instance_bare)
    m001_edge_confidence(inst, backup=False)
    rep2 = m001_edge_confidence(inst, backup=False)
    assert rep2["backfilled"] == 0 and rep2["null_remaining"] == 0


def test_m001_dry_run_writes_nothing(tiny_instance_bare):
    inst = load_instance(tiny_instance_bare)
    rep = m001_edge_confidence(inst, dry_run=True)
    assert rep["applied"] is False and _nulls(inst.db_path) == 9
