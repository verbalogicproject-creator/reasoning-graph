"""FCL parser — parses live + fixture logs; append refuses dupes; status advances."""
from __future__ import annotations
from pathlib import Path
import pytest
from reasoning_graph.schema import load_instance
from reasoning_graph.loop import fcl


def test_parses_fixture_log_6_entries(tiny_instance):
    entries = fcl.parse_log(load_instance(tiny_instance))
    assert len(entries) == 6
    assert all(e["gap_shape"] for e in entries)


def test_parses_live_log_11_entries():
    root = Path(__file__).resolve().parents[1]
    inst = load_instance(root / "instances" / "claude_code_tools" / "instance.json")
    entries = fcl.parse_log(inst)
    assert len(entries) == 11
    assert {e["id"] for e in entries} == {f"FCL-{i:03d}" for i in range(1, 12)}


def test_append_refuses_duplicate_id(tiny_instance):
    inst = load_instance(tiny_instance)
    with pytest.raises(ValueError, match="already exists"):
        fcl.append_entry(inst, "### FIX-003 — dupe   [LOGGED]\n- query: x\n")


def test_advance_status_legal_transitions_only(tiny_instance):
    inst = load_instance(tiny_instance)
    fcl.advance_status(inst, "FIX-005", "PROMOTED")           # logged -> promoted OK
    with pytest.raises(ValueError):
        fcl.advance_status(inst, "FIX-005", "LOGGED")         # backward illegal
