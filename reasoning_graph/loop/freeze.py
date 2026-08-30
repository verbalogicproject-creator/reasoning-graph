"""Freeze — P5: a VERIFIED matcher becomes graph content + provenance rows.
Contract (gate G4):

freeze(instance, staged_path, approve=False) -> {"mint_id","edges_inserted",
    "rows","already_frozen"}
  approve=True required for a real instance DB; fixtures set self_approve.
  Writes in one transaction: confirmed edges (edge_kind from the machine block,
  confidence = matcher's, basis declared:matcher:<mint_id>, synthesis_chain);
  fact-loop rows (synthesis_facts/fact_validations/evolution_log/insights —
  created IF NOT EXISTS for corpora that lack them); rule_status (counters,
  status='active'); moves staged -> minted; advances the FCL provenance entries.
  IDEMPOTENT on synthesis_chain: a re-run inserts 0 and reports already_frozen.
"""
from __future__ import annotations

import json
import time

from ..store import Store
from . import fcl
from .mint import parse_machine_block

_CREATE = {
    "rule_status": """CREATE TABLE IF NOT EXISTS rule_status (
        mint_id TEXT PRIMARY KEY, status TEXT, times_used INTEGER DEFAULT 0,
        times_confirmed INTEGER DEFAULT 0, times_contradicted INTEGER DEFAULT 0,
        retired_reason TEXT, retired_at TEXT, evidence TEXT)""",
    "synthesis_facts": """CREATE TABLE IF NOT EXISTS synthesis_facts (
        synthesis_id TEXT PRIMARY KEY, fact_a TEXT, fact_b TEXT, synthesized_fact TEXT,
        synthesis_type TEXT, confidence REAL, session_id TEXT, created_at TEXT)""",
    "fact_validations": """CREATE TABLE IF NOT EXISTS fact_validations (
        validation_id TEXT PRIMARY KEY, statement TEXT, is_fact INTEGER, confidence REAL,
        evidence TEXT, domain TEXT, created_at TEXT)""",
    "evolution_log": """CREATE TABLE IF NOT EXISTS evolution_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, component TEXT, change_type TEXT,
        description TEXT, triggered_by TEXT, insight_refs TEXT, timestamp REAL)""",
    "insights": """CREATE TABLE IF NOT EXISTS insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT, number INTEGER, content TEXT, builds_on TEXT,
        depth INTEGER, tags TEXT, document_source TEXT, timestamp REAL, session_id TEXT)""",
}


def freeze(instance, staged_path, approve: bool = False) -> dict:
    from pathlib import Path
    staged_path = Path(staged_path)
    m = parse_machine_block(staged_path)
    mint_id = m["mint_id"]
    provenance = m.get("provenance", [])
    fix = m["fix"]
    edge_kind = fix["edge_kind"]

    self_approve = _self_approve(instance)
    if not (approve or self_approve):
        raise PermissionError(f"freeze on {instance.name} requires --approve "
                              "(instance is not self_approve)")

    store = Store.open(instance)  # validates reality; raises on undeclared kinds
    try:
        edge_decl = instance.schema.edge_kind(edge_kind)  # minted kind must be declared
        p = store.profile
        # idempotency: already-frozen edges for this mint_id?
        existing = store.conn.execute(
            f"SELECT COUNT(*) FROM {p.edges_table} WHERE {p.edge_synthesis_chain} LIKE ?",
            (f"{mint_id}%",)).fetchone()[0]
        if existing:
            return {"mint_id": mint_id, "edges_inserted": 0, "rows": {},
                    "already_frozen": True}
        pairs = list(store.conn.execute(fix["pairs_sql"]))
        for src, tgt in pairs:
            source_kind, target_kind = store.node_kind(src), store.node_kind(tgt)
            if source_kind is None or target_kind is None:
                raise ValueError(f"mint {mint_id} references missing endpoint: {src}->{tgt}")
            if not edge_decl.permits(source_kind, target_kind):
                raise ValueError(
                    f"mint {mint_id} violates {edge_kind} endpoint contract: "
                    f"{src} ({source_kind}) -> {tgt} ({target_kind})")

        chain = f"{mint_id} / {' '.join(provenance)}"
        basis = f"declared:matcher:{mint_id}"
        conf = m["confidence"]
        props_tmpl = fix.get("properties_template", {})
        rows = {}
        cols = (f"{p.edge_source},{p.edge_target},{p.edge_kind},{p.edge_confidence},"
                f"{p.edge_properties},{p.edge_synthesis_chain}")
        with store.writer() as w:
            for _t, ddl in _CREATE.items():
                w.execute(ddl)
            for src, tgt in pairs:
                props = json.dumps({**props_tmpl, "confidence_basis": basis})
                w.execute(f"INSERT INTO {p.edges_table} ({cols}) VALUES (?,?,?,?,?,?)",
                          (src, tgt, edge_kind, conf, props, chain))
            edges_inserted = len(pairs)

            now = time.time()
            w.execute("INSERT INTO synthesis_facts (synthesis_id,fact_a,fact_b,synthesized_fact,"
                      "synthesis_type,confidence,session_id,created_at) VALUES (?,?,?,?,?,?,?,?)",
                      (mint_id, f"provenance:{','.join(provenance)}",
                       f"signature:{m.get('signature_sql','')[:80]}",
                       m.get("statement", ""), "composition", conf, "loop-freeze", str(now)))
            rows["synthesis_facts"] = 1
            w.execute("INSERT INTO fact_validations (validation_id,statement,is_fact,confidence,"
                      "evidence,domain,created_at) VALUES (?,?,?,?,?,?,?)",
                      (f"{mint_id}-val", m.get("statement", ""), 1, conf,
                       f"verify: {edges_inserted} edges confirmed", "reasoning-chains", str(now)))
            rows["fact_validations"] = 1
            w.execute("INSERT INTO evolution_log (component,change_type,description,triggered_by,"
                      "insight_refs,timestamp) VALUES (?,?,?,?,?,?)",
                      (f"rule:{mint_id}", "addition",
                       f"froze {edges_inserted} {edge_kind} edges (approve={approve or self_approve})",
                       f"FCL:{','.join(provenance)}", json.dumps([]), now))
            rows["evolution_log"] = 1
            maxnum = w.execute("SELECT COALESCE(MAX(number),0) FROM insights").fetchone()[0]
            w.execute("INSERT INTO insights (number,content,builds_on,depth,tags,document_source,"
                      "timestamp,session_id) VALUES (?,?,?,?,?,?,?,?)",
                      (maxnum + 1, m.get("statement", ""), json.dumps([]), 1,
                       json.dumps(["minted", mint_id]), staged_path.name, now, "loop-freeze"))
            rows["insights"] = 1
            w.execute("INSERT OR REPLACE INTO rule_status (mint_id,status,times_used,"
                      "times_confirmed,times_contradicted) VALUES (?,?,0,0,0)", (mint_id, "active"))
            rows["rule_status"] = 1
    finally:
        store.close()

    _move_to_minted(instance, staged_path, mint_id, provenance)
    for pid in provenance:
        try:
            fcl.advance_status(instance, pid, "MINTED")
        except (KeyError, ValueError):
            pass
    return {"mint_id": mint_id, "edges_inserted": edges_inserted, "rows": rows,
            "already_frozen": False}


def _self_approve(instance) -> bool:
    import json as _json
    root = instance.root
    for name in ("instance.json",):
        p = root / name
        if p.exists():
            return bool(_json.loads(p.read_text()).get("self_approve"))
    return False


def _move_to_minted(instance, staged_path, mint_id, provenance):
    """Copy the staged matcher into the minted dir with a Provenance line. The
    staged file is DELIBERATELY kept (not unlinked): freeze must be re-runnable
    from the same --staged path so the idempotency check (G4 runs freeze twice)
    can read the mint_id and report already_frozen."""
    minted_dir = (instance.rules_dir or staged_path.parent.parent) / "minted"
    minted_dir.mkdir(parents=True, exist_ok=True)
    if staged_path.exists():
        content = staged_path.read_text()
        prov_line = f"\n**Provenance**: frozen from {', '.join(provenance)} (loop freeze)\n"
        (minted_dir / f"{mint_id}-MINTED.md").write_text(content + prov_line)
