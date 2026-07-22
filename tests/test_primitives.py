"""Primitive adapters — subprocess provenance; generic honest smaller surface."""
from __future__ import annotations
from reasoning_graph.schema import load_instance
from reasoning_graph.primitives import adapter_for, GenericAdapter, SubprocessAdapter


def test_generic_adapter_smaller_surface_honest(tiny_instance):
    inst = load_instance(tiny_instance)
    ad = adapter_for(inst)
    assert isinstance(ad, GenericAdapter)
    assert ad.available() == ("want_to", "can_it", "trace", "why_not")
    import pytest
    from reasoning_graph.primitives import AdapterError
    with pytest.raises(AdapterError):
        ad.run("compose_for", {"goal": "x"})     # honestly unimplemented, not faked


def test_generic_trace_uses_resolver(tiny_instance):
    inst = load_instance(tiny_instance)
    r = adapter_for(inst).run("trace", {"from": "loom_1", "to": "dye_bath_2"})
    assert r["status"] == "ANSWER" and r["_adapter"] == "generic"


def test_subprocess_adapter_provenance():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    inst = load_instance(root / "instances" / "claude_code_tools" / "instance.json")
    ad = adapter_for(inst)
    assert isinstance(ad, SubprocessAdapter)
    out = ad.run("want_to", {"goal": "read a file"})
    assert out["_adapter"] == "subprocess" and out["_argv"][0:2][-1].endswith("query.py")
