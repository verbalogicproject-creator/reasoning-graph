"""Schema-layer tests — LIVE NOW (schema.py is implemented this session).
Invariants 1 (declaration half), 3, 12."""
from __future__ import annotations

import json
import pytest

from reasoning_graph.schema import (
    ConfidenceRule,
    EdgeKind,
    GraphSchema,
    is_valid_basis,
    load_instance,
)


def test_inv_closed_basis_vocabulary():
    assert is_valid_basis("declared:structural_extraction")
    assert is_valid_basis("declared:matcher:mint_001_tool_combo_inference")
    assert is_valid_basis("derived:corpus_min(0.70)")
    assert not is_valid_basis("measured:api_usage")      # valid ONLY in ab artifacts, never on edges
    assert not is_valid_basis("inferred:vibes")
    with pytest.raises(ValueError):
        ConfidenceRule(basis="inferred:vibes")
    with pytest.raises(ValueError):
        ConfidenceRule(basis="declared:initial_guess", value=1.5)


def test_inv_structural_validation():
    ck = ConfidenceRule(basis="declared:structural_extraction", value=1.0)
    good = GraphSchema(name="g", node_kinds=("a", "b"),
                       edge_kinds=(EdgeKind("e1", ck),))
    good.validate()
    with pytest.raises(ValueError):
        GraphSchema(name="g", node_kinds=("a", "a"),
                    edge_kinds=(EdgeKind("e1", ck),)).validate()
    with pytest.raises(ValueError):
        GraphSchema(name="g", node_kinds=("a",), edge_kinds=(EdgeKind("e1", ck),),
                    floor=1.5).validate()
    with pytest.raises(ValueError):
        GraphSchema(name="g", node_kinds=("a",), edge_kinds=(EdgeKind("e1", ck),),
                    promotion_threshold=1).validate()
    # the FCL-001 human-approval escape hatch must be explicit
    GraphSchema(name="g", node_kinds=("a",), edge_kinds=(EdgeKind("e1", ck),),
                promotion_threshold=1, allow_single_occurrence_promotion=True).validate()
    with pytest.raises(KeyError):
        good.edge_kind("nope")

    constrained = EdgeKind("typed", ck, source_kinds=("a",), target_kinds=("b",))
    assert constrained.permits("a", "b")
    assert not constrained.permits("b", "a")
    GraphSchema(name="typed", node_kinds=("a", "b"),
                edge_kinds=(constrained,)).validate()
    with pytest.raises(ValueError, match="undeclared node kind"):
        GraphSchema(
            name="bad", node_kinds=("a", "b"),
            edge_kinds=(EdgeKind("bad", ck, source_kinds=("missing",)),)).validate()
    with pytest.raises(ValueError, match="non-empty and unique"):
        EdgeKind("empty", ck, source_kinds=())


def test_inv_tiny_profile_roundtrip(tiny_instance):
    """Declaration half of invariant 1: the tiny instance (non-default names,
    alien domain) loads and validates. The store/resolver half is covered in
    test_store/test_resolver."""
    inst = load_instance(tiny_instance)
    assert inst.schema.name == "tiny_weaving"
    assert inst.schema.profile.nodes_table == "strands"
    assert inst.schema.profile.edge_confidence == "trust"
    assert inst.db_path.name == "tiny.db" and inst.db_path.exists()
    assert inst.schema.edge_kind("contradicts").cycle_class == "contradiction"
    assert inst.schema.edge_kind("rivals").cycle_class == "benign_reciprocal"


def test_instance0_descriptor_loads():
    """The real instance-0 declaration must always load and validate."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    inst = load_instance(root / "instances" / "claude_code_tools" / "instance.json")
    assert inst.name == "claude_code_tools"
    assert len(inst.schema.node_kinds) == 14
    assert len(inst.schema.edge_kinds) == 24     # 23 live + contradicts
    assert inst.schema.floor == 0.30
    assert inst.db_path.is_file()
    workflow = inst.schema.edge_kind("workflow_includes_tool")
    assert workflow.source_kinds == ("workflow",)
    assert workflow.target_kinds == ("tool",)
    assert inst.db_path.name == "reasoning-graph.clean.db"
    assert inst.fcl_path is not None and inst.fcl_path.is_file()


def test_adapter_cwd_is_descriptor_relative_not_process_relative(tiny_instance, monkeypatch,
                                                                 tmp_path):
    data = json.loads(tiny_instance.read_text())
    adapter_dir = tiny_instance.parent / "adapter-work"
    adapter_dir.mkdir()
    data["adapter"] = {"kind": "subprocess", "cwd": "adapter-work",
                       "argv": ["python3", "query.py"]}
    tiny_instance.write_text(json.dumps(data))

    monkeypatch.chdir(tmp_path)
    inst = load_instance(tiny_instance)
    assert inst.adapter["cwd"] == str(adapter_dir.resolve())
