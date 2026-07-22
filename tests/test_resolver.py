"""Resolver invariant 4 — path_product_score, exact product."""
from __future__ import annotations
import math
from reasoning_graph.schema import load_instance
from reasoning_graph.resolver import resolve


def test_inv_path_product_exact(tiny_instance):
    inst = load_instance(tiny_instance)
    a = resolve(inst, start="loom_1", end="dye_bath_2")
    assert a["status"] == "ANSWER"
    assert a["confidence_kind"] == "path_product_score"
    product = 1.0
    for e in a["path"]:
        product *= e["confidence"]
    assert abs(a["confidence"] - product) < 1e-9
    assert abs(a["confidence"] - 0.95) < 1e-9      # 1.0 * 0.95


def test_weighted_prefers_higher_confidence_route(tiny_instance):
    inst = load_instance(tiny_instance)
    # only one route loom_1 -> spindle_b (via rivals); confidence 0.90
    a = resolve(inst, start="loom_1", end="spindle_b")
    assert a["status"] == "ANSWER" and abs(a["confidence"] - 0.90) < 1e-9


def test_below_floor_is_weak_answer(tiny_instance):
    inst = load_instance(tiny_instance)
    a = resolve(inst, start="loom_1", end="pattern_card_1")
    assert a["status"] == "WEAK_ANSWER" and abs(a["confidence"] - 0.20) < 1e-9
    # hard mode refuses instead
    a2 = resolve(inst, start="loom_1", end="pattern_card_1", hard=True)
    assert a2["status"] == "REFUSE" and a2["refusal"]["reason"] == "below_floor"
