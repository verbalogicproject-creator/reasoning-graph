"""Frontier-call rate. Contract (gate G5):

compute(instance) -> {entries_total, series[], batches[], baseline, reading, basis}
  series: log order oldest-first; each {entry_id, entry_index, cumulative_classes,
    is_new_class}. Classes = DECLARED gap_shapes (sidecar + inline). The gate
    recomputes the series independently and requires equality.
  batches: from the log's own organic-batch markers (>= 2).
  reading: ONE honest sentence computed from the numbers — never pre-claimed.
  basis: "derived:fcl_log_parse" (every number derived from declared inputs).
"""
from __future__ import annotations

import re

from ..loop import fcl

_BATCH_MARKER = re.compile(r"(first|second|third|fourth)\s+organic\s+batch\b.*?(\d+)\s+"
                           r"(?:more\s+)?(?:diverse,?\s+realistic\s+)?queries", re.I)
_HEADING = re.compile(r"^###\s+(FCL-\d+)\b")


def compute(instance) -> dict:
    entries = fcl.parse_log(instance)                 # file order (newest first)
    chronological = list(reversed(entries))           # oldest first — matches the gate
    seen: set = set()
    series = []
    for i, e in enumerate(chronological):
        shape = e["gap_shape"]
        is_new = shape not in seen
        seen.add(shape)
        series.append({"entry_id": e["id"], "entry_index": i,
                       "cumulative_classes": len(seen), "is_new_class": is_new})

    batches = _batches(instance, series)
    reading = _reading(series, batches)
    return {"entries_total": len(entries), "series": series, "batches": batches,
            "baseline": {"organic_batches": batches,
                         "note": "the 2 historical organic batches, computed as shipped"},
            "reading": reading, "basis": "derived:fcl_log_parse"}


def _batches(instance, series):
    """Assign FCL entries to the log's declared organic batches by file position,
    then count new gap_shape classes each contributed (chronological)."""
    lines = instance.fcl_path.read_text().splitlines()
    entry_batch: dict[str, str] = {}
    batch_meta: dict[str, int] = {}
    current, order = None, []
    for line in lines:
        bm = _BATCH_MARKER.search(line)
        if bm:
            current = f"{bm.group(1).lower()} organic batch"
            batch_meta[current] = int(bm.group(2))
            if current not in order:
                order.append(current)
            continue
        h = _HEADING.match(line)
        if h and current:
            entry_batch[h.group(1)] = current
    new_flag = {s["entry_id"]: s["is_new_class"] for s in series}
    out = []
    for label in reversed(order):   # markers are newest-first → reverse to chronological
        members = [eid for eid, b in entry_batch.items() if b == label]
        new_classes = sum(1 for eid in members if new_flag.get(eid))
        n = batch_meta.get(label, len(members))
        out.append({"label": label, "queries": n, "logged_entries": len(members),
                    "new_classes": new_classes,
                    "new_class_rate": round(new_classes / n, 4) if n else 0.0})
    return out


def _reading(series, batches) -> str:
    if len(series) < 6:
        return (f"Too few entries ({len(series)}) to read a trend honestly; "
                "the series is reported, not interpreted.")
    if len(batches) >= 2:
        r1, r2 = batches[0]["new_class_rate"], batches[-1]["new_class_rate"]
        trend = "falling" if r2 < r1 else "rising" if r2 > r1 else "flat"
        return (f"New-class rate went {r1} -> {r2} across the two organic batches "
                f"({trend}); at this N (2 batches / {len(series)} entries) this is "
                "a direction, not a proven trend.")
    return (f"{series[-1]['cumulative_classes']} distinct gap-shape classes across "
            f"{len(series)} entries; too few batches to compute a rate trend.")
