#!/usr/bin/env python3
"""Build a referentially clean instance database without changing the source.

The migration is intentionally instance-specific and evidence preserving:

* workflow node IDs come from the existing dangling relationships and must also
  be declared by a checked-in Claude Code tool source record;
* ``workflow_includes_tool`` is normalized to workflow -> tool;
* duplicate (source, target, edge_type) claims are represented by one edge whose
  properties retain each original row as evidence.

The derived database is written to a temporary sibling and atomically published
only after SQLite and graph-contract validation succeeds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "kgs" / "reasoning-graph.db"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "derived" / "reasoning-graph.clean.db"
DEFAULT_MANIFEST = (
    REPO_ROOT / "data" / "derived" / "reasoning-graph.clean.manifest.json"
)
SOURCE_GLOBS = (
    "claude-code-tools/*.json",
    "kgs/claude_kg_truth/templates/claude-code-tools/*tool.json",
)


class MigrationError(RuntimeError):
    """Raised when source evidence or the derived graph violates the contract."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_json_object(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MigrationError(f"edge properties are not valid JSON: {raw!r}") from exc
    if not isinstance(parsed, dict):
        raise MigrationError(f"edge properties must be a JSON object: {raw!r}")
    return parsed


def _records(document: Any, source: Path) -> Iterable[dict[str, Any]]:
    if isinstance(document, dict):
        yield document
        return
    if isinstance(document, list):
        for item in document:
            if not isinstance(item, dict):
                raise MigrationError(f"non-object tool record in {source}")
            yield item
        return
    raise MigrationError(f"tool source must contain an object or array: {source}")


def load_workflow_sources(repo_root: Path) -> dict[str, list[dict[str, str]]]:
    declarations: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for pattern in SOURCE_GLOBS:
        for source in sorted(repo_root.glob(pattern)):
            try:
                document = json.loads(source.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise MigrationError(f"cannot read tool source {source}: {exc}") from exc
            for record in _records(document, source):
                tool_id = record.get("tool_id")
                tool_name = record.get("name")
                workflows = record.get("workflow_ids", [])
                if not isinstance(tool_id, str) or not isinstance(workflows, list):
                    continue
                relative_source = source.relative_to(repo_root).as_posix()
                for workflow_id in workflows:
                    if not isinstance(workflow_id, str) or not workflow_id:
                        raise MigrationError(f"invalid workflow ID in {relative_source}")
                    key = (workflow_id, tool_id, relative_source)
                    if key not in seen:
                        declarations[workflow_id].append(
                            {
                                "source_tool_id": tool_id,
                                "source_tool_name": tool_name if isinstance(tool_name, str) else "",
                                "source_file": relative_source,
                            }
                        )
                        seen.add(key)
    return dict(declarations)


def table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    node_count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    edge_count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    node_kind_count = conn.execute(
        "SELECT COUNT(DISTINCT node_type) FROM nodes"
    ).fetchone()[0]
    return {
        "nodes": node_count,
        "relationships": edge_count,
        "node_kinds": node_kind_count,
    }


def recover_workflows(
    conn: sqlite3.Connection, declarations: dict[str, list[dict[str, str]]]
) -> tuple[list[dict[str, Any]], list[int]]:
    rows = conn.execute(
        """
        SELECT e.edge_id, e.source_node_id AS tool_id,
               e.target_node_id AS workflow_id, e.created_at
        FROM edges e
        LEFT JOIN nodes target ON target.node_id = e.target_node_id
        WHERE e.edge_type = 'workflow_includes_tool'
          AND target.node_id IS NULL
        ORDER BY e.target_node_id, e.edge_id
        """
    ).fetchall()
    if not rows:
        return [], []

    by_workflow: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        by_workflow[row["workflow_id"]].append(row)

    missing_evidence = sorted(set(by_workflow) - set(declarations))
    if missing_evidence:
        raise MigrationError(
            "dangling workflow IDs lack checked-in source declarations: "
            + ", ".join(missing_evidence)
        )

    tool_rows = conn.execute(
        "SELECT node_id, name, metadata FROM nodes WHERE node_type = 'tool'"
    ).fetchall()
    tool_names: dict[str, str] = {}
    tool_ids = {row["node_id"] for row in tool_rows}
    for tool_row in tool_rows:
        metadata = read_json_object(tool_row["metadata"])
        for name in (tool_row["name"], metadata.get("tool_call_name")):
            if isinstance(name, str) and name:
                tool_names[name.casefold()] = tool_row["node_id"]

    recovered: list[dict[str, Any]] = []
    reversed_edge_ids: list[int] = []
    for workflow_id, workflow_rows in sorted(by_workflow.items()):
        referenced_tools = sorted({row["tool_id"] for row in workflow_rows})
        evidence = []
        declared_tools = set()
        for declaration in declarations[workflow_id]:
            source_tool_id = declaration["source_tool_id"]
            source_tool_name = declaration["source_tool_name"]
            resolved_tool_id = None
            if source_tool_id in tool_ids:
                resolved_tool_id = source_tool_id
            elif source_tool_name:
                resolved_tool_id = tool_names.get(source_tool_name.casefold())
            evidence_item = dict(declaration)
            evidence_item["resolved_tool_id"] = resolved_tool_id
            evidence.append(evidence_item)
            if resolved_tool_id:
                declared_tools.add(resolved_tool_id)
        undeclared_edges = sorted(set(referenced_tools) - set(declared_tools))
        if undeclared_edges:
            raise MigrationError(
                f"workflow {workflow_id!r} has edges not supported by sources: "
                + ", ".join(undeclared_edges)
            )

        evidence = sorted(
            evidence,
            key=lambda item: (item["resolved_tool_id"] or "", item["source_file"]),
        )
        title = workflow_id.replace("_", " ").title()
        created_at = min(row["created_at"] for row in workflow_rows)
        metadata = {
            "confidence_basis": "declared:structural_extraction",
            "provenance": evidence,
            "recovered_by": "repair-instance-v1",
        }
        conn.execute(
            """
            INSERT INTO nodes (
                node_id, node_type, name, title, description, category,
                source_url, metadata, created_at
            ) VALUES (?, 'workflow', ?, ?, ?, 'tool_workflow', NULL, ?, ?)
            """,
            (
                workflow_id,
                title,
                title,
                "Workflow concept declared by Claude Code tool source records.",
                canonical_json(metadata),
                created_at,
            ),
        )
        edge_ids = sorted(row["edge_id"] for row in workflow_rows)
        placeholders = ",".join("?" for _ in edge_ids)
        conn.execute(
            f"""
            UPDATE edges
            SET source_node_id = target_node_id,
                target_node_id = source_node_id
            WHERE edge_id IN ({placeholders})
            """,
            edge_ids,
        )
        reversed_edge_ids.extend(edge_ids)
        recovered.append(
            {
                "workflow_id": workflow_id,
                "title": title,
                "tool_ids": referenced_tools,
                "source_evidence": evidence,
                "reversed_edge_ids": edge_ids,
            }
        )
    return recovered, reversed_edge_ids


def merge_duplicate_typed_relationships(
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    groups = conn.execute(
        """
        SELECT source_node_id, target_node_id, edge_type, COUNT(*) AS row_count
        FROM edges
        GROUP BY source_node_id, target_node_id, edge_type
        HAVING COUNT(*) > 1
        ORDER BY source_node_id, target_node_id, edge_type
        """
    ).fetchall()
    merges: list[dict[str, Any]] = []
    for group in groups:
        rows = conn.execute(
            """
            SELECT edge_id, confidence, properties, created_at, synthesis_chain
            FROM edges
            WHERE source_node_id = ? AND target_node_id = ? AND edge_type = ?
            ORDER BY edge_id
            """,
            (
                group["source_node_id"],
                group["target_node_id"],
                group["edge_type"],
            ),
        ).fetchall()
        confidences = {row["confidence"] for row in rows}
        if len(confidences) != 1:
            raise MigrationError(
                "cannot merge duplicate typed claims with different confidence: "
                f"{group['source_node_id']} -> {group['target_node_id']} "
                f"({group['edge_type']})"
            )

        kept = rows[0]
        evidence = [
            {
                "original_edge_id": row["edge_id"],
                "confidence": row["confidence"],
                "created_at": row["created_at"],
                "properties": read_json_object(row["properties"]),
                "synthesis_chain": row["synthesis_chain"],
            }
            for row in rows
        ]
        merged_properties = {
            "confidence_basis": "declared:inherited_curation_default",
            "evidence": evidence,
            "merge_policy": "same_source_target_type_preserve_all_evidence",
        }
        conn.execute(
            "UPDATE edges SET properties = ? WHERE edge_id = ?",
            (canonical_json(merged_properties), kept["edge_id"]),
        )
        removed_ids = [row["edge_id"] for row in rows[1:]]
        conn.executemany(
            "DELETE FROM edges WHERE edge_id = ?",
            [(edge_id,) for edge_id in removed_ids],
        )
        merges.append(
            {
                "source_node_id": group["source_node_id"],
                "target_node_id": group["target_node_id"],
                "edge_type": group["edge_type"],
                "kept_edge_id": kept["edge_id"],
                "removed_edge_ids": removed_ids,
                "evidence": evidence,
            }
        )
    return merges


def validate(conn: sqlite3.Connection) -> dict[str, Any]:
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_keys = [list(row) for row in conn.execute("PRAGMA foreign_key_check")]
    wrong_direction = conn.execute(
        """
        SELECT COUNT(*)
        FROM edges e
        JOIN nodes source ON source.node_id = e.source_node_id
        JOIN nodes target ON target.node_id = e.target_node_id
        WHERE e.edge_type = 'workflow_includes_tool'
          AND NOT (source.node_type = 'workflow' AND target.node_type = 'tool')
        """
    ).fetchone()[0]
    duplicate_typed_relationships = conn.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT 1 FROM edges
            GROUP BY source_node_id, target_node_id, edge_type
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]
    checks = {
        "integrity_check": integrity,
        "foreign_key_violations": foreign_keys,
        "wrong_direction_workflow_relationships": wrong_direction,
        "duplicate_typed_relationship_groups": duplicate_typed_relationships,
    }
    if integrity != "ok" or foreign_keys or wrong_direction or duplicate_typed_relationships:
        raise MigrationError(f"derived database validation failed: {checks}")
    return checks


def migrate(input_path: Path, output_path: Path, manifest_path: Path) -> dict[str, Any]:
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    manifest_path = manifest_path.resolve()
    if input_path == output_path:
        raise MigrationError("output path must differ from the immutable input path")
    if not input_path.is_file():
        raise MigrationError(f"input database does not exist: {input_path}")

    input_hash_before = sha256(input_path)
    declarations = load_workflow_sources(REPO_ROOT)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    temp_handle = tempfile.NamedTemporaryFile(
        prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent, delete=False
    )
    temp_path = Path(temp_handle.name)
    temp_handle.close()
    try:
        shutil.copy2(input_path, temp_path)
        conn = sqlite3.connect(temp_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                raise MigrationError("SQLite foreign-key enforcement could not be enabled")
            before = table_counts(conn)
            conn.execute("BEGIN IMMEDIATE")
            recovered, reversed_edge_ids = recover_workflows(conn, declarations)
            merges = merge_duplicate_typed_relationships(conn)
            conn.commit()
            checks = validate(conn)
            after = table_counts(conn)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        os.replace(temp_path, output_path)
        output_hash = sha256(output_path)
        input_hash_after = sha256(input_path)
        if input_hash_after != input_hash_before:
            raise MigrationError("immutable input database changed during migration")

        manifest = {
            "migration": "repair-instance-v1",
            "input": {
                "path": input_path.relative_to(REPO_ROOT).as_posix()
                if input_path.is_relative_to(REPO_ROOT)
                else str(input_path),
                "sha256_before": input_hash_before,
                "sha256_after": input_hash_after,
                "counts": before,
            },
            "output": {
                "path": output_path.relative_to(REPO_ROOT).as_posix()
                if output_path.is_relative_to(REPO_ROOT)
                else str(output_path),
                "sha256": output_hash,
                "counts": after,
            },
            "operations": {
                "recovered_workflows": recovered,
                "reversed_workflow_edge_ids": sorted(reversed_edge_ids),
                "merged_typed_relationships": merges,
                "rejected_records": [],
            },
            "validation": checks,
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return manifest
    finally:
        temp_path.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        manifest = migrate(args.input, args.output, args.manifest)
    except (MigrationError, OSError, sqlite3.Error) as exc:
        print(f"repair failed: {exc}")
        return 1
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

