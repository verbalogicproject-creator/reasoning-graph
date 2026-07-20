"""Verify — P4: a staged matcher must PROVE itself before freezing. OPUS-FILLS (Phase 4).

Contract (gate G4):

verify(instance, staged_path) -> {"ok": bool, "candidates": int,
    "confirmed": [...], "rejected": [{candidate, failed_predicate}],
    "provenance_fired": bool, "composition": {...}}
  1. Runs the machine block's signature_sql → candidates.
  2. Runs every confirm predicate per candidate; ALL must hold to confirm.
  3. provenance_fired: the matcher must actually fire against >= 1 of its own
     originating FCL entries' recorded gap (no unreproduced rule — Phase A's
     "confirm before you claim").
  4. composition: checks the staged rule against COMPOSITION-VALIDATOR's rules
     (instance-0 rules_dir, COMPOSITION-VALIDATOR-SYNTHESIS-RULES.md) where
     mechanically applicable; records which composed rules were checked.
  ok=True requires: >=1 confirmed candidate AND provenance_fired AND zero
  confirm-predicate errors. verify NEVER writes the DB.
"""
from __future__ import annotations


def verify(instance, staged_path) -> dict:
    raise NotImplementedError("OPUS-FILLS: Phase 4 — see module docstring + SoT")
