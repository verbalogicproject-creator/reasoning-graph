from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.repair_instance_db import (
    DEFAULT_INPUT,
    DEFAULT_MANIFEST,
    DEFAULT_OUTPUT,
    REPO_ROOT,
    MigrationError,
    migrate,
)


SOURCE_DB = (
    REPO_ROOT / "instances" / "claude_code_tools" / "source" / "reasoning-graph.db"
)
EXPECTED_SOURCE_SHA256 = (
    "08f651490c6c9e0be7523d8e8054624c1277cadcacaf91b8771d8b93f94d3edb"
)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RepairInstanceDatabaseTests(unittest.TestCase):
    def test_source_database_matches_reviewed_baseline(self) -> None:
        self.assertEqual(file_hash(SOURCE_DB), EXPECTED_SOURCE_SHA256)

    def test_defaults_are_bundled_inside_the_canonical_instance(self) -> None:
        instance_root = REPO_ROOT / "instances" / "claude_code_tools"
        self.assertEqual(DEFAULT_INPUT, instance_root / "source" / "reasoning-graph.db")
        self.assertEqual(
            DEFAULT_OUTPUT, instance_root / "data" / "reasoning-graph.clean.db"
        )
        self.assertEqual(
            DEFAULT_MANIFEST,
            instance_root / "data" / "reasoning-graph.clean.manifest.json",
        )

    def test_migration_repairs_graph_without_changing_source(self) -> None:
        source_hash_before = file_hash(SOURCE_DB)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "clean.db"
            manifest_path = Path(temp_dir) / "manifest.json"
            manifest = migrate(SOURCE_DB, output, manifest_path)

            self.assertEqual(file_hash(SOURCE_DB), source_hash_before)
            self.assertEqual(manifest["input"]["sha256_before"], source_hash_before)
            self.assertEqual(manifest["input"]["sha256_after"], source_hash_before)
            self.assertEqual(
                manifest["output"]["counts"],
                {"nodes": 660, "relationships": 853, "node_kinds": 14},
            )
            self.assertEqual(len(manifest["operations"]["recovered_workflows"]), 21)
            self.assertEqual(
                len(manifest["operations"]["reversed_workflow_edge_ids"]), 44
            )
            self.assertEqual(
                len(manifest["operations"]["merged_typed_relationships"]), 3
            )
            self.assertEqual(json.loads(manifest_path.read_text()), manifest)
            self.assertEqual(manifest["output"]["sha256"], file_hash(output))

            conn = sqlite3.connect(output)
            conn.row_factory = sqlite3.Row
            try:
                self.assertEqual(
                    conn.execute("PRAGMA integrity_check").fetchone()[0], "ok"
                )
                self.assertEqual(list(conn.execute("PRAGMA foreign_key_check")), [])
                wrong = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM edges e
                    JOIN nodes s ON s.node_id = e.source_node_id
                    JOIN nodes t ON t.node_id = e.target_node_id
                    WHERE e.edge_type = 'workflow_includes_tool'
                      AND NOT (s.node_type = 'workflow' AND t.node_type = 'tool')
                    """
                ).fetchone()[0]
                self.assertEqual(wrong, 0)

                merged = conn.execute(
                    """
                    SELECT properties FROM edges
                    WHERE source_node_id = 'edit_file'
                      AND target_node_id = 'read_file'
                      AND edge_type = 'tool_requires_tool'
                    """
                ).fetchall()
                self.assertEqual(len(merged), 1)
                evidence = json.loads(merged[0]["properties"])["evidence"]
                self.assertEqual(
                    [item["original_edge_id"] for item in evidence], [703, 715]
                )
                self.assertEqual(len(evidence), 2)
            finally:
                conn.close()

    def test_refuses_all_path_collisions_without_modifying_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.db"
            output = root / "output.db"
            manifest = root / "manifest.json"
            source.write_bytes(SOURCE_DB.read_bytes())
            output.write_bytes(b"existing output")
            manifest.write_bytes(b"existing manifest")
            cases = (
                (source, source, manifest),
                (source, output, source),
                (source, output, output),
            )
            for paths in cases:
                source.write_bytes(SOURCE_DB.read_bytes())
                output.write_bytes(b"existing output")
                manifest.write_bytes(b"existing manifest")
                before = {
                    path: path.read_bytes() for path in {source, output, manifest}
                }
                with self.assertRaisesRegex(MigrationError, "pairwise distinct"):
                    migrate(*paths)
                self.assertEqual(
                    {path: path.read_bytes() for path in before},
                    before,
                )


if __name__ == "__main__":
    unittest.main()
