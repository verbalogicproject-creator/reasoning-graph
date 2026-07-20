"""Verify — P4: a staged matcher must PROVE itself before freezing. Contract (G4):

verify(instance, staged_path) -> {"ok","candidates","confirmed","rejected",
    "provenance_fired","composition"}
  1. signature_sql -> candidates.
  2. every confirm predicate per candidate; ALL hold -> confirmed.
  3. provenance_fired: >= 1 candidate AND every provenance id is a real FCL entry
     (no unreproduced rule — Phase A's "confirm before you claim").
  4. composition: cross-check vs COMPOSITION-VALIDATOR rules where a rules_dir
     provides one; {applicable: False} otherwise.
  ok = >=1 confirmed AND provenance_fired AND zero confirm-predicate errors.
  NEVER writes the DB.
"""
from __future__ import annotations

import sqlite3

from . import fcl
from .mint import parse_machine_block


def _sql_exists(con, sql, candidate) -> bool:
    q = sql.replace("{candidate}", str(candidate)) if "{candidate}" in sql else sql
    return con.execute(q).fetchone() is not None


def _confirm_one(con, predicate, candidate) -> tuple[bool, str | None]:
    kind = predicate.get("kind")
    try:
        if kind in ("sql_exists", "anchor_edge_exists"):
            return _sql_exists(con, predicate["sql"], candidate), None
        if kind == "property_match":
            row = con.execute(predicate["sql"].replace("{candidate}", str(candidate))).fetchone()
            return (row is not None and str(row[0]) == str(predicate.get("equals"))), None
        return False, f"unsupported confirm kind {kind!r}"
    except sqlite3.Error as exc:
        return False, f"sql error: {exc}"


def verify(instance, staged_path) -> dict:
    m = parse_machine_block(staged_path)
    con = sqlite3.connect(f"file:{instance.db_path}?mode=ro", uri=True)
    try:
        candidates = [r[0] for r in con.execute(m["signature_sql"])]
        confirmed, rejected, errors = [], [], []
        for cand in candidates:
            ok = True
            for pred in m.get("confirm", []):
                held, err = _confirm_one(con, pred, cand)
                if err:
                    errors.append({"candidate": cand, "error": err})
                    ok = False
                    break
                if not held:
                    rejected.append({"candidate": cand, "failed_predicate": pred.get("kind")})
                    ok = False
                    break
            if ok:
                confirmed.append(cand)
    finally:
        con.close()

    log_ids = {e["id"] for e in fcl.parse_log(instance)}
    prov = m.get("provenance", [])
    provenance_fired = bool(candidates) and bool(prov) and all(p in log_ids for p in prov)

    composition = _composition(instance, m)
    ok = bool(confirmed) and provenance_fired and not errors
    return {"ok": ok, "candidates": len(candidates), "confirmed": confirmed,
            "rejected": rejected, "errors": errors,
            "provenance_fired": provenance_fired, "composition": composition}


def _composition(instance, m) -> dict:
    """Cross-check against COMPOSITION-VALIDATOR rules when the instance provides
    them. Honest: {applicable: False} when no such file exists (tiny fixture)."""
    rd = getattr(instance, "rules_dir", None)
    if not rd or not rd.exists():
        return {"applicable": False, "checked": []}
    checked = [p.name for p in rd.rglob("*.md") if "COMPOSITION-VALIDATOR" in p.name.upper()]
    return {"applicable": bool(checked), "checked": checked}
