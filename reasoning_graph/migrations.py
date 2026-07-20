"""Migrations. One exists: m001_edge_confidence.

CORE RULE: this module is corpus-agnostic — it never names an edge kind, node
kind, or corpus id (gate G1 greps). The derivation table lives in the INSTANCE
GraphSchema: every EdgeKind carries its ConfidenceRule (basis + declared value
or derivation), and the instance-0 concrete table is spelled out in the SoT's
edge-confidence section + instances/claude_code_tools/graphschema.py.

Contract, frozen by this docstring + gate G2:

m001_edge_confidence(instance, dry_run=False, backup=True) -> dict
  1. If the profile's confidence column is absent:
     ALTER TABLE <profile.edges_table> ADD COLUMN <profile.edge_confidence> REAL
     (additive — existing columns and any name-based external SELECTs unaffected;
     query.py verified to use zero SELECT *).
  2. Backfill every edge with NULL confidence, per edge kind:
     a. synthesis-chain non-NULL: confidence = the minting matcher's declared
        confidence (read from the matcher file the chain's mint_id names),
        basis = "declared:matcher:<mint_id>". PRECEDES the kind default.
     b. else per the kind's ConfidenceRule:
        - basis == "derived:source_rule_confidence": read the source node's
          metadata confidence; present → that value, basis unchanged; absent →
          the rule's declared fallback value with basis "derived:corpus_min(<v>)".
        - value is not None → write value, basis = rule.basis.
        - neither → raise (cannot fabricate a confidence; fail loud).
     basis is written into the properties JSON under "confidence_basis".
  3. Idempotent: only NULLs are backfilled; a second run reports backfilled=0.
  4. backup=True copies the DB to <db>.bak-m001 BEFORE any write.
  5. dry_run=True writes nothing; reports would-backfill counts.

Return shape (CLI `reasoning-graph migrate --json` prints exactly this):
  {"migration","applied","dry_run","edges_total","backfilled","by_basis",
   "null_remaining","backup"}
null_remaining MUST be 0 after a real run on a fully-declared instance — G2 fails otherwise.
"""
from __future__ import annotations

import json
import re
import shutil
import sqlite3

from .schema import Instance

_RULE_ID_RE = re.compile(r"\*\*Rule ID\*\*:\s*(\S+)")
_CONF_RE = re.compile(r"\*\*Confidence\*\*:\s*([01](?:\.\d+)?)")


def _load_matcher_confidences(instance: Instance) -> dict[str, float]:
    """Map mint_id -> declared confidence, parsed from the instance's matcher
    files (rules_dir/**/*.md). Format-generic: pairs each `**Rule ID**` with the
    next `**Confidence**` in the same file. Only mint_ids are ever looked up, so
    parsing frozen extracted-rule files alongside is harmless."""
    out: dict[str, float] = {}
    if not instance.rules_dir or not instance.rules_dir.exists():
        return out
    for md in instance.rules_dir.rglob("*.md"):
        current: str | None = None
        for line in md.read_text().splitlines():
            m = _RULE_ID_RE.search(line)
            if m:
                current = m.group(1)
                continue
            c = _CONF_RE.search(line)
            if c and current is not None:
                out[current] = float(c.group(1))
                current = None
    return out


def _node_confidences(conn: sqlite3.Connection, instance: Instance) -> dict[str, float]:
    p = instance.schema.profile
    out: dict[str, float] = {}
    for nid, meta in conn.execute(f"SELECT {p.node_id}, {p.node_metadata} FROM {p.nodes_table}"):
        try:
            c = (json.loads(meta or "{}") or {}).get("confidence")
        except (json.JSONDecodeError, TypeError):
            c = None
        if c is not None:
            out[str(nid)] = float(c)
    return out


def _fmt(v: float) -> str:
    return f"{v:g}"


def m001_edge_confidence(instance: Instance, dry_run: bool = False, backup: bool = True) -> dict:
    p = instance.schema.profile
    rules = {e.name: e.confidence_rule for e in instance.schema.edge_kinds}
    matcher = _load_matcher_confidences(instance)

    con = sqlite3.connect(str(instance.db_path))
    try:
        cols = {r[1] for r in con.execute(f"PRAGMA table_info({p.edges_table})")}
        has_col = p.edge_confidence in cols
        node_conf = _node_confidences(con, instance)

        def confidence_for(kind: str, source_id, chain) -> tuple[float, str]:
            if chain:
                mint_id = str(chain).split("/")[0].strip()
                if mint_id not in matcher:
                    raise ValueError(f"synthesis_chain names mint_id {mint_id!r} but no "
                                     f"matcher file in {instance.rules_dir} declares its confidence")
                return matcher[mint_id], f"declared:matcher:{mint_id}"
            rule = rules[kind]  # KeyError impossible: DB reality validated at Store.open
            if rule.basis == "derived:source_rule_confidence":
                src = node_conf.get(str(source_id))
                if src is not None:
                    return src, "derived:source_rule_confidence"
                if rule.value is not None:
                    return rule.value, f"derived:corpus_min({_fmt(rule.value)})"
                raise ValueError(f"edge kind {kind!r}: source rule declares no confidence "
                                 "and no fallback value is declared on its ConfidenceRule")
            if rule.value is not None:
                return rule.value, rule.basis
            raise ValueError(f"edge kind {kind!r} has no derivable confidence "
                             f"(value=None, basis={rule.basis})")

        # Rows needing backfill (all of them if the column doesn't exist yet).
        conf_sel = p.edge_confidence if has_col else "NULL"
        rows = con.execute(
            f"SELECT rowid, {p.edge_kind}, {p.edge_source}, {p.edge_synthesis_chain}, "
            f"{p.edge_properties}, {conf_sel} FROM {p.edges_table}").fetchall()
        edges_total = len(rows)
        pending = [r for r in rows if r[5] is None]

        by_basis: dict[str, int] = {}
        updates = []
        for rowid, kind, source_id, chain, props, _conf in pending:
            conf, basis = confidence_for(kind, source_id, chain)
            by_basis[basis] = by_basis.get(basis, 0) + 1
            merged = json.loads(props or "{}") or {}
            merged["confidence_basis"] = basis
            updates.append((conf, json.dumps(merged), rowid))

        if dry_run:
            return {"migration": "m001_edge_confidence", "applied": False, "dry_run": True,
                    "edges_total": edges_total, "backfilled": 0,
                    "would_backfill": len(pending), "by_basis": by_basis,
                    "null_remaining": len(pending), "backup": None}

        backup_path = None
        if backup:
            backup_path = str(instance.db_path) + ".bak-m001"
            shutil.copy2(instance.db_path, backup_path)

        if not has_col:
            con.execute(f"ALTER TABLE {p.edges_table} ADD COLUMN {p.edge_confidence} REAL")
        con.executemany(
            f"UPDATE {p.edges_table} SET {p.edge_confidence}=?, {p.edge_properties}=? WHERE rowid=?",
            updates)
        con.commit()

        null_remaining = con.execute(
            f"SELECT COUNT(*) FROM {p.edges_table} WHERE {p.edge_confidence} IS NULL").fetchone()[0]
        return {"migration": "m001_edge_confidence", "applied": True, "dry_run": False,
                "edges_total": edges_total, "backfilled": len(updates),
                "by_basis": by_basis, "null_remaining": null_remaining, "backup": backup_path}
    finally:
        con.close()
