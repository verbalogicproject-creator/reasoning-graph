"""Promotion detector — the recurrence gate, mechanized. Contract (gate G4):

detect(instance) -> {"recurring", "promotable", "already_disposed"}
  recurring  = entries whose DECLARED occurrences >= schema.promotion_threshold
               (never NLP-inferred; RecMem arXiv:2605.16045 — fixed threshold,
               non-adaptivity is a ROADMAP item).
  promotable = recurring MINUS disposed (disposition or terminal status).
  Live instance-0 ground truth: recurring == {FCL-001,007,008,009}; promotable
  == {} (all disposed — incl. FCL-008's rejection, respected not re-proposed).
promote(instance, entry_id) -> None  — advance to PROMOTED; refuse if not promotable.
"""
from __future__ import annotations

from . import fcl

_DISPOSED_PREFIXES = ("minted", "closed", "resolved", "rejected", "frozen")


def _is_disposed(entry) -> bool:
    disp = (entry.get("disposition") or "").lower()
    if disp.startswith(_DISPOSED_PREFIXES):
        return True
    # fixture path: no sidecar disposition — use the mapped status tag
    return entry.get("status") in ("minted", "frozen", "closed", "resolved")


def detect(instance) -> dict:
    entries = fcl.parse_log(instance)
    threshold = instance.schema.promotion_threshold
    recurring, disposed = [], {}
    for e in entries:
        if e["occurrences"] >= threshold:
            recurring.append(e["id"])
            if _is_disposed(e):
                disposed[e["id"]] = e.get("disposition") or e.get("status")
    promotable = [eid for eid in recurring if eid not in disposed]
    return {"recurring": recurring, "promotable": promotable, "already_disposed": disposed}


def promote(instance, entry_id: str) -> None:
    d = detect(instance)
    if entry_id not in d["promotable"]:
        raise ValueError(f"{entry_id} is not promotable "
                         f"(recurring={entry_id in d['recurring']}, "
                         f"disposed={entry_id in d['already_disposed']})")
    fcl.advance_status(instance, entry_id, "PROMOTED")
