"""Retirement invariant 9 — demote not delete; ratio before cap."""
from __future__ import annotations
import json
from pathlib import Path
from reasoning_graph.schema import load_instance
from reasoning_graph.loop import retire


def test_inv_demote_not_delete(tiny_instance):
    inst = load_instance(tiny_instance)
    fx = Path(__file__).resolve().parent / "fixtures" / "retire-fixture.json"
    expected = json.loads(fx.read_text())["expected"]
    r = retire.retire_pass(inst, fixture=str(fx))
    assert [d["mint_id"] for d in r["demoted"]] == expected["demoted"]
    assert r["deleted"] == [] and all(d.get("evidence") for d in r["demoted"])


def test_ratio_demotion_before_cap_enforcement(tiny_instance):
    inst = load_instance(tiny_instance)
    fx = Path(__file__).resolve().parent / "fixtures" / "retire-fixture.json"
    r = retire.retire_pass(inst, fixture=str(fx))
    # f02 demoted by ratio; f01 + f03 remain active within cap=2 (ratio applies first)
    assert r["active"] == 2 and r["dormant"] == 1


def test_dormant_rules_edges_excluded_from_resolve(tiny_instance):
    from reasoning_graph.resolver import dormant_mint_ids
    inst = load_instance(tiny_instance)
    fx = Path(__file__).resolve().parent / "fixtures" / "retire-fixture.json"
    retire.retire_pass(inst, fixture=str(fx))
    assert "mint_f02_whorl_speed" in dormant_mint_ids(inst)
