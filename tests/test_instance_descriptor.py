from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR = REPO_ROOT / "instance" / "instance.json"

try:
    from reasoning_graph.primitives import adapter_for
    from reasoning_graph.resolver import resolve
    from reasoning_graph.schema import load_instance
    from reasoning_graph.store import inspect_integrity
except ImportError as exc:  # The instance repo deliberately does not vendor the engine.
    adapter_for = resolve = load_instance = inspect_integrity = None
    ENGINE_IMPORT_ERROR = str(exc)
else:
    ENGINE_IMPORT_ERROR = ""


class InstanceDescriptorStaticTests(unittest.TestCase):
    def test_descriptor_has_only_relative_runtime_paths(self) -> None:
        document = json.loads(DESCRIPTOR.read_text(encoding="utf-8"))
        for field in (
            "db_path",
            "fcl_path",
            "rules_dir",
            "staged_dir",
            "observations_path",
            "graphschema",
        ):
            self.assertFalse(Path(document[field]).is_absolute(), field)
        self.assertFalse(Path(document["adapter"]["cwd"]).is_absolute())
        self.assertEqual(document["adapter"]["argv"], ["python3", "query.py"])


@unittest.skipIf(
    load_instance is None,
    f"canonical reasoning_graph package unavailable: {ENGINE_IMPORT_ERROR}",
)
class CanonicalEngineIntegrationTests(unittest.TestCase):
    def test_descriptor_schema_and_database_integrity(self) -> None:
        instance = load_instance(DESCRIPTOR)
        self.assertEqual(instance.db_path, REPO_ROOT / "data" / "derived" / "reasoning-graph.clean.db")
        self.assertEqual(instance.observations_path, REPO_ROOT / "data" / "observations.jsonl")
        self.assertIsNotNone(instance.adapter)
        self.assertEqual(Path(instance.adapter["cwd"]), REPO_ROOT)
        self.assertEqual(len(instance.schema.node_kinds), 14)
        self.assertEqual(len(instance.schema.edge_kinds), 24)
        workflow_edge = instance.schema.edge_kind("workflow_includes_tool")
        self.assertEqual(workflow_edge.source_kinds, ("workflow",))
        self.assertEqual(workflow_edge.target_kinds, ("tool",))

        report = inspect_integrity(instance)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["counts"], {"nodes": 660, "edges": 853})

    def test_known_weighted_rule_path(self) -> None:
        instance = load_instance(DESCRIPTOR)
        answer = resolve(
            instance,
            start="dep_003_tool_execution_requires_error_handling",
            end="constr_002_max_iterations_safety",
        )
        self.assertEqual(answer["status"], "ANSWER")
        self.assertAlmostEqual(answer["confidence"], 0.9118, places=8)

    def test_compatibility_adapter_resolves_from_descriptor_root(self) -> None:
        instance = load_instance(DESCRIPTOR)
        answer = adapter_for(instance).run(
            "compose_for", {"goal": "fix a bug found via search"}
        )
        self.assertEqual([item["tool"] for item in answer["tools"]], ["Grep", "Read", "Edit"])


if __name__ == "__main__":
    unittest.main()

