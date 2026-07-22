"""Promotion invariant 7 — recurrence gate reproduces live history + dispositions."""
from __future__ import annotations
from pathlib import Path
from reasoning_graph.schema import load_instance
from reasoning_graph.loop import promote


def test_inv_recurrence_gate_and_dispositions():
    root = Path(__file__).resolve().parents[1]
    inst = load_instance(root / "instances" / "claude_code_tools" / "instance.json")
    d = promote.detect(inst)
    assert set(d["recurring"]) == {"FCL-001", "FCL-007", "FCL-008", "FCL-009"}
    assert d["promotable"] == []                     # all disposed; FCL-008 rejection respected
    assert "FCL-008" in d["already_disposed"]


def test_fixture_pair_promotable(tiny_instance):
    inst = load_instance(tiny_instance)
    d = promote.detect(inst)
    assert set(d["promotable"]) == {"FIX-003", "FIX-005"}
