"""Frontier-call-log parser. OPUS-FILLS (Phase 4). Contract (gate G4):

parse_log(instance) -> list[Entry]
  Parses the FCL file against its own §1 schema:
    ### <ID> — <one-line>   [LOGGED | PROMOTED | MINTED | FROZEN | ...status tags]
    - query / category / gap / root_cause / reasoning_conclusion / verified_by / pattern
  Real-world tolerance, verified against the 11 live entries FCL-001..FCL-011:
  status tags include compound historical forms ("FIXED 2026-07-14",
  "LOGGED — sharpened on recurrence, still not fixed", "RESOLVED 2026-07-14 —
  corrected, not force-closed", "CLOSED 2026-07-14"). Map them:
    FROZEN→frozen, MINTED→minted, PROMOTED→promoted, FIXED/CLOSED→closed,
    RESOLVED→resolved, LOGGED (any qualifier)→logged.
  Gate G4 requires parse of 11/11 live entries with the status mapping above.

Entry fields: id, title, status (mapped), raw_status, fields: dict of the
  schema keys present, gap_shape: str | None, occurrences: int.
  gap_shape + occurrences come from the DECLARED sidecar
  (instance.gap_shape_history JSON) — never inferred from text similarity.
  New entries going forward carry an explicit `- gap_shape:` line inline; the
  sidecar exists because the 11 historical entries predate the field.

append_entry(instance, entry_text) -> None
  Appends atomically under §2 (newest on top), never rewrites existing text
  (the log's own safe_edit_points contract). Refuses if entry ID already exists.

advance_status(instance, entry_id, new_status) -> None
  Rewrites ONLY the status tag inside the entry's ### heading line, preserving
  every other byte. Legal transitions: logged→promoted→minted→frozen (+ any→closed
  /resolved with a human note). Illegal transition → raise.
"""
from __future__ import annotations


def parse_log(instance) -> list:
    raise NotImplementedError("OPUS-FILLS: Phase 4 — see module docstring + SoT")


def append_entry(instance, entry_text: str) -> None:
    raise NotImplementedError("OPUS-FILLS: Phase 4 — see module docstring + SoT")


def advance_status(instance, entry_id: str, new_status: str) -> None:
    raise NotImplementedError("OPUS-FILLS: Phase 4 — see module docstring + SoT")
