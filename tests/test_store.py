"""Store invariants — 2 (missing confidence refuses) and 11 (unknown kind raises)."""
from __future__ import annotations

import sqlite3

import pytest

from reasoning_graph.schema import load_instance
from reasoning_graph.store import MissingConfidence, Store


def test_inv_null_confidence_refuses(tiny_instance_bare):
    """Invariant 2: an edge with NULL confidence raises MissingConfidence — never
    a silent 1.0 (the bug this framework exists to kill)."""
    store = Store.open(load_instance(tiny_instance_bare))
    with pytest.raises(MissingConfidence):
        list(store.edges())                       # bare fixture: all trust NULL
    assert all(e["confidence"] is None for e in store.neighbors("loom_1", "out"))
    store.close()


def test_inv_unknown_kind_raises(tiny_instance):
    """Invariant 11: an undeclared edge kind in the DB raises at open, naming it."""
    inst = load_instance(tiny_instance)
    con = sqlite3.connect(inst.db_path)
    con.execute("INSERT INTO ties VALUES ('loom_1','spindle_a','sorcery',0.5,'{}',NULL)")
    con.commit()
    con.close()
    with pytest.raises(ValueError, match="sorcery"):
        Store.open(inst)


def test_reads_are_profile_driven(tiny_instance):
    """The store reads a non-default-named schema purely through the profile."""
    store = Store.open(load_instance(tiny_instance))
    ids = {n["id"] for n in store.nodes()}
    assert "loom_1" in ids and len(ids) == 10
    assert store.edge_confidence("spindle_a", "dye_bath_2", "tunes") == (0.95, "declared:verbatim_extraction")
    assert {n["kind"] for n in store.nodes()} == {"loom", "spindle", "dye_bath", "pattern_card", "guild_rule"}
    store.close()
