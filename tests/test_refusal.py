"""Refusal invariants — 5 (no-support drafts FCL stub) and 6 (cycle classes)."""
from __future__ import annotations
from reasoning_graph.schema import load_instance
from reasoning_graph.resolver import resolve


def test_inv_no_support_refuses_with_stub(tiny_instance):
    inst = load_instance(tiny_instance)
    a = resolve(inst, start="loom_1", end="dye_bath_3")     # island
    assert a["status"] == "REFUSE"
    assert a["refusal"]["reason"] == "no_frozen_support"
    stub = a["refusal"]["fcl_stub"]
    assert "[LOGGED]" in stub and "gap_shape" in stub


def test_inv_cycle_classes(tiny_instance):
    inst = load_instance(tiny_instance)
    # contradiction-class edge on the only route -> REFUSE naming the pair
    a = resolve(inst, start="loom_2", end="pattern_card_2")
    assert a["status"] == "REFUSE" and a["refusal"]["reason"] == "contradiction"
    assert "guild_rule_x" in a["refusal"]["detail"] and "guild_rule_y" in a["refusal"]["detail"]
    # benign reciprocal cycle (rivals) NEVER refuses
    b = resolve(inst, start="loom_1", end="spindle_b")
    assert b["status"] == "ANSWER"


def test_missing_confidence_refuses(tiny_instance_bare):
    inst = load_instance(tiny_instance_bare)
    a = resolve(inst, start="loom_1", end="dye_bath_2")
    assert a["status"] == "REFUSE" and a["refusal"]["reason"] == "missing_confidence"
