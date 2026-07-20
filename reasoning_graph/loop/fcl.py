"""Frontier-call-log parser. Contract (gate G4):

parse_log(instance) -> list[Entry]  — parses the FCL §1 schema, tolerant of the
  compound historical status tags on the 11 live entries. gap_shape + occurrences
  come from the DECLARED sidecar (instance.gap_shape_history) when present, else
  from the inline `- gap_shape:` field (occurrences = count of entries sharing
  the shape). Never inferred from text similarity (lock #20).
append_entry(instance, entry_text) -> None — appends under §2, newest on top,
  never rewrites; refuses a duplicate id.
advance_status(instance, entry_id, new_status) -> None — rewrites ONLY the tag
  in the entry's ### heading; forward transitions only (or ->closed/resolved).
"""
from __future__ import annotations

import json
import re

_HEADING = re.compile(r"^###\s+(\S+)\s+.+?\[([^\]]+)\]\s*$")
_FIELD = re.compile(r"^-\s+([a-z_]+):\s*(.*)$")
_STATUS_MAP = {"FROZEN": "frozen", "MINTED": "minted", "PROMOTED": "promoted",
               "FIXED": "closed", "CLOSED": "closed", "RESOLVED": "resolved",
               "LOGGED": "logged", "HARDENED": "closed", "VERIFIED-CLOSED": "closed"}
_ORDER = ["logged", "promoted", "minted", "frozen"]
_TERMINAL = {"closed", "resolved"}


def _map_status(raw: str) -> str:
    first = raw.strip().split()[0] if raw.strip() else "LOGGED"
    return _STATUS_MAP.get(first.upper(), "logged")


def _load_sidecar(instance) -> dict:
    p = getattr(instance, "gap_shape_history", None)
    if p and p.exists():
        return json.loads(p.read_text()).get("entries", {})
    return {}


def parse_log(instance) -> list:
    if not instance.fcl_path or not instance.fcl_path.exists():
        return []
    sidecar = _load_sidecar(instance)
    lines = instance.fcl_path.read_text().splitlines()
    entries, cur, in_fence = [], None, False
    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue  # the §1 schema template lives in a fence — never an entry
        m = _HEADING.match(line)
        if m:
            eid, raw = m.group(1), m.group(2)
            cur = {"id": eid, "raw_status": raw, "status": _map_status(raw),
                   "title": line.split("—", 1)[-1].rsplit("[", 1)[0].strip() if "—" in line else "",
                   "fields": {}, "gap_shape": None, "occurrences": 1, "disposition": None}
            entries.append(cur)
            continue
        if cur is not None:
            f = _FIELD.match(line)
            if f:
                cur["fields"][f.group(1)] = f.group(2).strip()
                if f.group(1) == "gap_shape":
                    cur["gap_shape"] = f.group(2).strip()
    # occurrences from inline gap_shape sharing (fixture path)
    shape_counts: dict[str, int] = {}
    for e in entries:
        if e["gap_shape"]:
            shape_counts[e["gap_shape"]] = shape_counts.get(e["gap_shape"], 0) + 1
    for e in entries:
        if e["gap_shape"]:
            e["occurrences"] = shape_counts[e["gap_shape"]]
        # DECLARED sidecar overrides (the 11 historical entries)
        sc = sidecar.get(e["id"])
        if sc:
            e["gap_shape"] = sc.get("gap_shape", e["gap_shape"])
            e["occurrences"] = sc.get("occurrences", e["occurrences"])
            e["disposition"] = sc.get("disposition")
    return entries


def append_entry(instance, entry_text: str) -> None:
    if not instance.fcl_path or not instance.fcl_path.exists():
        raise FileNotFoundError(f"no FCL log at {instance.fcl_path}")
    existing = {e["id"] for e in parse_log(instance)}
    new_id = None
    m = _HEADING.match(entry_text.strip().splitlines()[0])
    if m:
        new_id = m.group(1)
    if new_id and new_id in existing:
        raise ValueError(f"FCL entry {new_id} already exists — never rewrite (append-only)")
    text = instance.fcl_path.read_text()
    anchor = re.search(r"^##\s+2\b.*$", text, flags=re.M)
    if not anchor:
        instance.fcl_path.write_text(text.rstrip() + "\n\n" + entry_text.strip() + "\n")
        return
    idx = anchor.end()
    instance.fcl_path.write_text(text[:idx] + "\n\n" + entry_text.strip() + "\n" + text[idx:])


def advance_status(instance, entry_id: str, new_status: str) -> None:
    cur = {e["id"]: e for e in parse_log(instance)}.get(entry_id)
    if cur is None:
        raise KeyError(f"FCL entry {entry_id} not found")
    old = cur["status"]
    tgt = new_status.strip().lower()
    legal = (tgt in _TERMINAL or
             (old in _ORDER and tgt in _ORDER and _ORDER.index(tgt) > _ORDER.index(old)))
    if not legal:
        raise ValueError(f"illegal status transition {old} -> {tgt} for {entry_id}")
    text = instance.fcl_path.read_text()
    tag = new_status.strip().upper() if tgt not in _TERMINAL else new_status.strip().upper()

    def _sub(match):
        line = match.group(0)
        return re.sub(r"\[[^\]]+\]", f"[{tag}]", line)

    text = re.sub(rf"^###\s+{re.escape(entry_id)}\s+.+?\[[^\]]+\]\s*$", _sub, text, count=1, flags=re.M)
    instance.fcl_path.write_text(text)
