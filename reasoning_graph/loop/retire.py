"""Retire — outcome-driven demotion. The SkillOps gap (arXiv:2605.13716), closed:
unmanaged rule libraries degrade below their no-rule baseline at scale; this
module DEMOTES to 'dormant' with evidence — it NEVER deletes (house append-only
discipline). Contract (gate G4):

record_outcome(instance, mint_id, outcome) -> None  — increment a counter.
retire_pass(instance, approve=False, fixture=None) -> {"demoted","active",
    "dormant","deleted"}
  fixture (test/gate only): declared counter-state JSON loaded into rule_status
  BEFORE the pass (self_approve instances only — real counters are never faked).
  Ratio-demote first (times_used >= min_uses AND contradicted/used >= ratio),
  THEN cap (over active_cap → demote lowest utility = confirmed - contradicted).
  Demotion records reason + evidence in evolution_log; counters never reset.
"""
from __future__ import annotations

import json
import time

from ..store import Store

_RULE_STATUS_DDL = """CREATE TABLE IF NOT EXISTS rule_status (
    mint_id TEXT PRIMARY KEY, status TEXT, times_used INTEGER DEFAULT 0,
    times_confirmed INTEGER DEFAULT 0, times_contradicted INTEGER DEFAULT 0,
    retired_reason TEXT, retired_at TEXT, evidence TEXT)"""
# RG-4: retire must be self-sufficient — evolution_log may not exist yet if retire
# runs before any freeze created it (freeze also creates it IF NOT EXISTS).
_EVOLUTION_DDL = """CREATE TABLE IF NOT EXISTS evolution_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT, component TEXT, change_type TEXT,
    description TEXT, triggered_by TEXT, insight_refs TEXT, timestamp REAL)"""
_OUTCOME_COL = {"used": "times_used", "confirmed": "times_confirmed",
                "contradicted": "times_contradicted"}


def record_outcome(instance, mint_id: str, outcome: str) -> None:
    if outcome not in _OUTCOME_COL:
        raise ValueError(f"outcome must be one of {tuple(_OUTCOME_COL)}, got {outcome!r}")
    col = _OUTCOME_COL[outcome]
    with Store.open(instance).writer() as w:
        w.execute(_RULE_STATUS_DDL)
        w.execute(f"UPDATE rule_status SET {col} = {col} + 1 WHERE mint_id = ?", (mint_id,))


def _self_approve(instance) -> bool:
    p = instance.root / "instance.json"
    return bool(json.loads(p.read_text()).get("self_approve")) if p.exists() else False


def retire_pass(instance, approve: bool = False, fixture: str | None = None) -> dict:
    self_approve = _self_approve(instance)
    if fixture and not self_approve:
        raise PermissionError("retire --fixture is legal only on a self_approve instance "
                              "(declared counters must never be faked on a real corpus)")
    if not (approve or self_approve):
        raise PermissionError(f"retire on {instance.name} requires --approve")

    pol = instance.schema.retirement
    with Store.open(instance).writer() as w:
        w.execute(_RULE_STATUS_DDL)
        w.execute(_EVOLUTION_DDL)
        if fixture:
            # deterministic fixture scope: exactly the declared rules
            declared = json.loads(open(fixture).read())["minted_rules"]
            w.execute("DELETE FROM rule_status")
            for mint_id, c in declared.items():
                w.execute("INSERT INTO rule_status (mint_id,status,times_used,times_confirmed,"
                          "times_contradicted) VALUES (?,?,?,?,?)",
                          (mint_id, c.get("status", "active"), c["times_used"],
                           c["times_confirmed"], c["times_contradicted"]))

        active = [dict(r) for r in w.execute(
            "SELECT mint_id,times_used,times_confirmed,times_contradicted "
            "FROM rule_status WHERE status='active'").fetchall()]
        for a in active:
            a["utility"] = a["times_confirmed"] - a["times_contradicted"]

        demoted = []

        def _demote(rule, reason):
            evidence = {"times_used": rule["times_used"], "times_confirmed": rule["times_confirmed"],
                        "times_contradicted": rule["times_contradicted"], "utility": rule["utility"]}
            now = time.time()
            w.execute("UPDATE rule_status SET status='dormant', retired_reason=?, retired_at=?, "
                      "evidence=? WHERE mint_id=?",
                      (reason, str(now), json.dumps(evidence), rule["mint_id"]))
            w.execute("INSERT INTO evolution_log (component,change_type,description,triggered_by,"
                      "insight_refs,timestamp) VALUES (?,?,?,?,?,?)",
                      (f"rule:{rule['mint_id']}", "removal", f"demoted to dormant: {reason}",
                       "retire_pass", json.dumps([]), now))
            demoted.append({"mint_id": rule["mint_id"], "reason": reason, "evidence": evidence})

        # 1. ratio-demotions FIRST
        still_active = []
        for a in active:
            if (a["times_used"] >= pol.min_uses
                    and a["times_used"] > 0
                    and a["times_contradicted"] / a["times_used"] >= pol.contradiction_ratio):
                _demote(a, f"contradiction ratio {a['times_contradicted']}/{a['times_used']} "
                           f">= {pol.contradiction_ratio}")
            else:
                still_active.append(a)

        # 2. cap enforcement — lowest utility first
        over = len(still_active) - pol.active_cap
        if over > 0:
            for a in sorted(still_active, key=lambda r: (r["utility"], r["mint_id"]))[:over]:
                _demote(a, f"over active_cap {pol.active_cap} (lowest utility {a['utility']})")

        counts = dict(w.execute(
            "SELECT status, COUNT(*) FROM rule_status GROUP BY status").fetchall())
    return {"demoted": demoted, "active": counts.get("active", 0),
            "dormant": counts.get("dormant", 0), "deleted": []}
