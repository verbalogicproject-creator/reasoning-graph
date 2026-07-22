"""Mint + verify — staging carries the machine block; verify requires provenance."""
from __future__ import annotations
from pathlib import Path
from reasoning_graph.schema import load_instance
from reasoning_graph.loop import mint, verify
from _loopmatcher import MATCHER


def test_stage_writes_matcher_v2_with_machine_block(tiny_instance):
    inst = load_instance(tiny_instance)
    r = mint.stage(inst, "FIX-005", MATCHER)
    text = Path(r["staged_path"]).read_text()
    assert "```yaml" in text and "mint_t_test" in text and "FIX-003" in text


def test_verify_requires_provenance_fired(tiny_instance):
    inst = load_instance(tiny_instance)
    r = mint.stage(inst, "FIX-005", MATCHER)
    v = verify.verify(inst, Path(r["staged_path"]))
    assert v["ok"] is True and v["provenance_fired"] is True
    assert "spindle_b" in v["confirmed"]


def test_verify_rejects_on_failed_confirm(tiny_instance):
    inst = load_instance(tiny_instance)
    m = dict(MATCHER, mint_id="mint_t_bad",
             confirm=[{"kind": "sql_exists", "sql": "SELECT 1 FROM ties WHERE tie_kind='nonexistent'"}])
    r = mint.stage(inst, "FIX-005", m)
    v = verify.verify(inst, Path(r["staged_path"]))
    assert v["ok"] is False and v["confirmed"] == []
