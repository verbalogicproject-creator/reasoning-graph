from __future__ import annotations

import json
from pathlib import Path

from reasoning_graph.resolver import resolve
from reasoning_graph.schema import load_instance
from reasoning_graph.store import inspect_integrity

REPO = Path(__file__).resolve().parents[1]
INSTANCE = REPO / "instances" / "claude_code_tools" / "instance.json"


def test_bundled_descriptor_is_relative_and_self_contained():
    raw = json.loads(INSTANCE.read_text())
    for key in ("db_path", "fcl_path", "rules_dir", "staged_dir",
                "observations_path", "gap_shape_history", "graphschema"):
        assert not Path(raw[key]).is_absolute(), key
    assert not Path(raw["adapter"]["cwd"]).is_absolute()
    assert raw["_notes"]["role"].startswith("Canonical bundled")

    instance = load_instance(INSTANCE)
    instance_root = INSTANCE.parent
    assert instance.db_path == instance_root / "data" / "reasoning-graph.clean.db"
    assert instance.fcl_path == REPO / "frontier-call-log.ngf.md"
    assert instance.rules_dir == REPO / "synthesis-rules"
    assert instance.observations_path == instance_root / "data" / "observations.jsonl"
    assert instance.adapter["cwd"] == str(REPO)
    assert instance.db_path.is_file()
    assert (instance_root / "source" / "reasoning-graph.db").is_file()


def test_bundled_descriptor_integrity_and_known_path():
    instance = load_instance(INSTANCE)
    report = inspect_integrity(instance)
    assert report["ok"] is True
    assert report["counts"] == {"nodes": 660, "edges": 853}
    assert report["missing_endpoints"] == []
    assert report["invalid_endpoint_kinds"] == []
    assert report["duplicate_typed_relationships"] == []
    assert report["foreign_key_violations"] == []

    answer = resolve(
        instance,
        start="dep_003_tool_execution_requires_error_handling",
        end="constr_002_max_iterations_safety",
    )
    assert answer["status"] == "ANSWER"
    assert abs(answer["confidence"] - 0.9118) < 1e-12
    assert answer["support_kind"] == "derived"


def test_legacy_query_default_uses_the_bundled_clean_database():
    from query import DB_PATH, IntentDrivenQuery

    assert DB_PATH == INSTANCE.parent / "data" / "reasoning-graph.clean.db"
    query = IntentDrivenQuery()
    try:
        result = query.compose_for("fix a bug found via search")
    finally:
        query.close()

    assert [item["tool"] for item in result["tools"]] == ["Grep", "Read", "Edit"]
