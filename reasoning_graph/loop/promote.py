"""Promotion detector — the recurrence gate, mechanized. OPUS-FILLS (Phase 4).

Contract (gate G4):

detect(instance) -> {"recurring": [entry_ids], "promotable": [entry_ids],
                     "already_disposed": {entry_id: disposition}}
  recurring  = entries whose declared occurrences >= schema.promotion_threshold
               (occurrences from the gap-shape sidecar / inline field — DECLARED,
               never NLP-inferred similarity; RecMem arXiv:2605.16045 validates
               the fixed gate, its non-adaptivity is a logged ROADMAP item).
  promotable = recurring MINUS entries already disposed (closed/resolved/minted/
               frozen/rejected per the sidecar's disposition field).
  Ground truth regression (G4 asserts EXACTLY this on the live instance-0 log):
    recurring == {FCL-001, FCL-007, FCL-008, FCL-009}
    dispositions preserved: FCL-001 minted (promoted on first sight by explicit
      human approval — the allow_single_occurrence_promotion path, recorded);
      FCL-007 closed(code_fix); FCL-009 closed(code_fix);
      FCL-008 rejected(content_gap) — recurred 5x and was CORRECTLY not minted:
      fixing the matcher couldn't produce a right answer the corpus doesn't
      contain, and inventing corpus content would be fabrication. The detector
      must surface FCL-008 as recurring AND respect its human disposition —
      never re-propose it as promotable.
    promotable == {} on the live log (everything recurring is disposed).

promote(instance, entry_id) -> None
  Advances the entry's status tag to PROMOTED (via fcl.advance_status) and
  records the promotion in the sidecar. Refuses if not in promotable set.
"""
from __future__ import annotations


def detect(instance) -> dict:
    raise NotImplementedError("OPUS-FILLS: Phase 4 — see module docstring + SoT")


def promote(instance, entry_id: str) -> None:
    raise NotImplementedError("OPUS-FILLS: Phase 4 — see module docstring + SoT")
