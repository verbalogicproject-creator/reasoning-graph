"""Store — SQLite substrate with a schema-profile-driven contract.

Contract, frozen by this docstring + gates G1/G2:

class MissingConfidence(Exception): raised whenever an edge's confidence is
    NULL/absent. NEVER default to 1.0 — the original nai edge_weight() defaults
    to 1.0; that behavior is the bug this framework exists to kill. The resolver
    converts MissingConfidence into REFUSE(reason="missing_confidence").

class Store:
    @classmethod open(instance: Instance) -> Store
        Opens read-only by default. Validates DB reality against the declared
        GraphSchema: any node kind or edge kind present in the DB but not
        declared → raise ValueError (list the offenders). Unknown-kind = error,
        never coercion.
    nodes(kind: str | None = None) -> iterator of {"id","kind","name","description","metadata"}
    edges(kind: str | None = None) -> iterator of
        {"source","target","kind","confidence","basis","properties","synthesis_chain"}
        basis is read from properties JSON key "confidence_basis";
        missing/NULL confidence or basis → MissingConfidence (unless
        include_unweighted=True, used only by `migrate --dry-run` reporting).
    edge_confidence(source, target, kind) -> (float, str)   # (value, basis)
    neighbors(node_id, direction="both") -> list of edge dicts (traversal
        primitive: confidence may be None on an unweighted edge; the resolver
        turns a None on the chosen path into REFUSE(missing_confidence)).
    write access exists ONLY for migrations.py and loop/freeze.py + loop/retire.py
        (writer(instance) context manager that takes an exclusive connection,
        journal-safe). Everything else is read-only by construction.

Every SQL identifier comes from instance.schema.profile — zero literal table or
column names in this module (gate G1 greps; the tiny fixture's non-default
names prove it).
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager

from .schema import Instance, is_valid_basis


class MissingConfidence(Exception):
    """An edge without a confidence value/basis was consulted (refusal-grade)."""


def _basis_of(properties_json: str | None) -> str | None:
    try:
        basis = (json.loads(properties_json or "{}") or {}).get("confidence_basis")
        return basis if isinstance(basis, str) else None
    except (json.JSONDecodeError, TypeError):
        return None


def inspect_integrity(instance: Instance) -> dict:
    """Return a complete, non-mutating integrity report for an instance.

    Inspection bypasses Store.open so a damaged graph remains diagnosable.
    Exact typed duplicates fail strict integrity until their evidence is merged;
    distinct relationship kinds between the same nodes remain lossless.
    """
    p = instance.schema.profile
    conn = sqlite3.connect(f"file:{instance.db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        node_rows = list(conn.execute(
            f"SELECT {p.node_id} AS id, {p.node_kind} AS kind FROM {p.nodes_table}"))
        nodes = {r["id"]: r["kind"] for r in node_rows}
        has_conf = any(r[1] == p.edge_confidence
                       for r in conn.execute(f"PRAGMA table_info({p.edges_table})"))
        conf = p.edge_confidence if has_conf else "NULL"
        edge_rows = list(conn.execute(
            f"SELECT {p.edge_source} AS source, {p.edge_target} AS target, "
            f"{p.edge_kind} AS kind, {conf} AS confidence, "
            f"{p.edge_properties} AS properties FROM {p.edges_table}"))

        declared_nodes = set(instance.schema.node_kinds)
        declared_edges = {e.name for e in instance.schema.edge_kinds}
        unknown_node_kinds = sorted({r["kind"] for r in node_rows
                                     if r["kind"] not in declared_nodes})
        unknown_edge_kinds = sorted({r["kind"] for r in edge_rows
                                     if r["kind"] not in declared_edges})
        missing_endpoints = []
        invalid_endpoint_kinds = []
        missing_confidence = []
        for index, row in enumerate(edge_rows):
            edge_id = {"row": index, "source": row["source"], "target": row["target"],
                       "kind": row["kind"]}
            missing = [side for side, value in (("source", row["source"]),
                                                 ("target", row["target"])) if value not in nodes]
            if missing:
                missing_endpoints.append({**edge_id, "missing": missing})
            if row["confidence"] is None:
                missing_confidence.append({**edge_id, "problem": "confidence"})
            else:
                basis = _basis_of(row["properties"])
                if basis is None or not is_valid_basis(basis):
                    missing_confidence.append({**edge_id, "problem": "confidence_basis",
                                               "basis": basis})
            if row["kind"] in declared_edges and not missing:
                edge_kind = instance.schema.edge_kind(row["kind"])
                source_kind, target_kind = nodes[row["source"]], nodes[row["target"]]
                if not edge_kind.permits(source_kind, target_kind):
                    invalid_endpoint_kinds.append({
                        **edge_id, "source_kind": source_kind, "target_kind": target_kind,
                        "allowed_source_kinds": edge_kind.source_kinds,
                        "allowed_target_kinds": edge_kind.target_kinds})

        duplicate_typed_relationships = [dict(r) for r in conn.execute(
            f"SELECT {p.edge_source} AS source, {p.edge_target} AS target, "
            f"{p.edge_kind} AS kind, COUNT(*) AS count FROM {p.edges_table} "
            f"GROUP BY {p.edge_source}, {p.edge_target}, {p.edge_kind} HAVING COUNT(*) > 1")]
        foreign_key_violations = [
            {"table": r[0], "rowid": r[1], "parent": r[2], "fkid": r[3]}
            for r in conn.execute("PRAGMA foreign_key_check")
        ]
        report = {
            "instance": instance.name,
            "db_path": str(instance.db_path),
            "counts": {"nodes": len(node_rows), "edges": len(edge_rows)},
            "unknown_node_kinds": unknown_node_kinds,
            "unknown_edge_kinds": unknown_edge_kinds,
            "missing_endpoints": missing_endpoints,
            "invalid_endpoint_kinds": invalid_endpoint_kinds,
            "missing_confidence": missing_confidence,
            "duplicate_typed_relationships": duplicate_typed_relationships,
            "foreign_key_violations": foreign_key_violations,
        }
        report["ok"] = not any(report[k] for k in (
            "unknown_node_kinds", "unknown_edge_kinds", "missing_endpoints",
            "invalid_endpoint_kinds", "missing_confidence",
            "duplicate_typed_relationships", "foreign_key_violations"))
        return report
    finally:
        conn.close()


class Store:
    """Profile-driven read layer over one instance's sqlite DB. All identifiers
    resolve through instance.schema.profile — nothing corpus-specific here."""

    def __init__(self, instance: Instance, conn: sqlite3.Connection, read_only: bool):
        self.instance = instance
        self.schema = instance.schema
        self.profile = instance.schema.profile
        self.conn = conn
        self.read_only = read_only
        self._has_conf = self._column_exists(self.profile.edges_table, self.profile.edge_confidence)

    # ---- lifecycle -----------------------------------------------------------
    @classmethod
    def open(cls, instance: Instance, read_only: bool = True) -> "Store":
        if read_only:
            conn = sqlite3.connect(f"file:{instance.db_path}?mode=ro", uri=True)
        else:
            conn = sqlite3.connect(str(instance.db_path))
            conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        store = cls(instance, conn, read_only)
        store._validate_reality()
        return store

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ---- introspection -------------------------------------------------------
    def _column_exists(self, table: str, column: str) -> bool:
        rows = self.conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r[1] == column for r in rows)

    def _validate_reality(self) -> None:
        """Every node/edge kind in the DB must be declared. Raise (never coerce)
        listing the offenders — EcoCorpusKG discipline; G1 plants an undeclared
        kind and requires this to name it."""
        p = self.profile
        declared_nodes = set(self.schema.node_kinds)
        seen_nodes = {r[0] for r in self.conn.execute(
            f"SELECT DISTINCT {p.node_kind} FROM {p.nodes_table}") if r[0] is not None}
        unknown_n = sorted(seen_nodes - declared_nodes)
        declared_edges = {e.name for e in self.schema.edge_kinds}
        seen_edges = {r[0] for r in self.conn.execute(
            f"SELECT DISTINCT {p.edge_kind} FROM {p.edges_table}") if r[0] is not None}
        unknown_e = sorted(seen_edges - declared_edges)
        if unknown_n or unknown_e:
            parts = []
            if unknown_n:
                parts.append(f"node kind(s) {unknown_n}")
            if unknown_e:
                parts.append(f"edge kind(s) {unknown_e}")
            raise ValueError(
                f"DB {self.instance.db_path.name} contains undeclared "
                f"{'; '.join(parts)} — not in GraphSchema {self.schema.name!r}")

    # ---- nodes ---------------------------------------------------------------
    def _node_row(self, row) -> dict:
        p = self.profile
        return {"id": row[p.node_id], "kind": row[p.node_kind], "name": row[p.node_name],
                "description": row[p.node_description], "metadata": row[p.node_metadata]}

    def nodes(self, kind: str | None = None):
        p = self.profile
        sql = (f"SELECT {p.node_id}, {p.node_kind}, {p.node_name}, "
               f"{p.node_description}, {p.node_metadata} FROM {p.nodes_table}")
        params: tuple = ()
        if kind is not None:
            if kind not in self.schema.node_kinds:
                raise KeyError(f"node kind {kind!r} is not declared in {self.schema.name!r}")
            sql += f" WHERE {p.node_kind} = ?"
            params = (kind,)
        for row in self.conn.execute(sql, params):
            yield self._node_row(row)

    def node(self, node_id: str) -> dict | None:
        p = self.profile
        row = self.conn.execute(
            f"SELECT {p.node_id}, {p.node_kind}, {p.node_name}, {p.node_description}, "
            f"{p.node_metadata} FROM {p.nodes_table} WHERE {p.node_id} = ?", (node_id,)).fetchone()
        return self._node_row(row) if row else None

    def node_kind(self, node_id: str) -> str | None:
        p = self.profile
        row = self.conn.execute(
            f"SELECT {p.node_kind} FROM {p.nodes_table} WHERE {p.node_id} = ?", (node_id,)).fetchone()
        return row[0] if row else None

    # ---- edges ---------------------------------------------------------------
    def _edge_row(self, row) -> dict:
        p = self.profile
        conf = row[p.edge_confidence] if self._has_conf else None
        props = row[p.edge_properties]
        return {"source": row[p.edge_source], "target": row[p.edge_target],
                "kind": row[p.edge_kind],
                "confidence": (float(conf) if conf is not None else None),
                "basis": _basis_of(props), "properties": props,
                "synthesis_chain": row[p.edge_synthesis_chain]}

    def _edge_select(self) -> str:
        p = self.profile
        conf = p.edge_confidence if self._has_conf else "NULL AS " + p.edge_confidence
        return (f"SELECT {p.edge_source}, {p.edge_target}, {p.edge_kind}, {conf}, "
                f"{p.edge_properties}, {p.edge_synthesis_chain} FROM {p.edges_table}")

    def edges(self, kind: str | None = None, include_unweighted: bool = False):
        p = self.profile
        sql = self._edge_select()
        params: tuple = ()
        if kind is not None:
            self.schema.edge_kind(kind)  # raises KeyError on undeclared
            sql += f" WHERE {p.edge_kind} = ?"
            params = (kind,)
        for row in self.conn.execute(sql, params):
            e = self._edge_row(row)
            if not include_unweighted and (e["confidence"] is None or e["basis"] is None):
                raise MissingConfidence(
                    f"edge {e['source']}->{e['target']} ({e['kind']}) has no "
                    f"confidence/basis (confidence={e['confidence']}, basis={e['basis']})")
            yield e

    def edge_confidence(self, source: str, target: str, kind: str) -> tuple[float, str]:
        p = self.profile
        self.schema.edge_kind(kind)
        row = self.conn.execute(
            self._edge_select() + f" WHERE {p.edge_source}=? AND {p.edge_target}=? AND {p.edge_kind}=?",
            (source, target, kind)).fetchone()
        if row is None:
            raise KeyError(f"no {kind} edge {source}->{target}")
        e = self._edge_row(row)
        if e["confidence"] is None or e["basis"] is None:
            raise MissingConfidence(f"edge {source}->{target} ({kind}) has no confidence/basis")
        return e["confidence"], e["basis"]

    def neighbors(self, node_id: str, direction: str = "both"):
        """Traversal primitive. Returns outgoing/incoming edge dicts (confidence
        may be None — traversal sees structure; the resolver decides whether a
        None on the chosen path is REFUSE(missing_confidence))."""
        p = self.profile
        out = []
        if direction in ("out", "both"):
            for row in self.conn.execute(
                    self._edge_select() + f" WHERE {p.edge_source} = ?", (node_id,)):
                e = self._edge_row(row)
                e["direction"] = "out"
                out.append(e)
        if direction in ("in", "both"):
            for row in self.conn.execute(
                    self._edge_select() + f" WHERE {p.edge_target} = ?", (node_id,)):
                e = self._edge_row(row)
                e["direction"] = "in"
                out.append(e)
        return out

    # ---- write access (migrations / freeze / retire only) --------------------
    @contextmanager
    def writer(self):
        """Yield an exclusive read-write connection. Commits on clean exit,
        rolls back on exception, always closes. The read-only Store connection
        stays untouched."""
        wconn = sqlite3.connect(str(self.instance.db_path), isolation_level="DEFERRED")
        wconn.row_factory = sqlite3.Row
        wconn.execute("PRAGMA foreign_keys=ON")
        if not wconn.execute("PRAGMA foreign_keys").fetchone()[0]:
            wconn.close()
            raise sqlite3.IntegrityError("SQLite foreign-key enforcement could not be enabled")
        try:
            yield wconn
            wconn.commit()
        except Exception:
            wconn.rollback()
            raise
        finally:
            wconn.close()
