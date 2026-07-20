"""Mint — stage a matcher file for a PROMOTED class. OPUS-FILLS (Phase 4).

Contract (gate G4):

stage(instance, entry_id, matcher: dict) -> Path
  Writes <staged_dir>/<mint_id>-STAGED.md in matcher-v2 format: the proven
  matcher-v1 shape (synthesis-rules/minted/TOOL-COMBO-INFERENCE-MINTED.md —
  Rule ID / Category / Confidence / Source / Statement / Signature / Confirm /
  Fix / Validation Formula / Related Rules / Provenance) PLUS one fenced
  ```yaml machine block:
    mint_id: <id>
    provenance: [<FCL entry ids>]
    confidence: <declared float in (0,1]>
    signature_sql: <SELECT that locates candidates in the store>
    confirm:                       # ALL must hold per candidate (anti-false-positive)
      - kind: sql_exists | property_match | anchor_edge_exists
        ...predicate-specific keys...
    fix:
      edge_kind: <declared kind>
      pairs_sql: <SELECT returning (source_id, target_id) rows to mint>
      properties_template: {...}   # written per-edge; confidence_basis added
                                   # automatically as declared:matcher:<mint_id>
  Human text and machine block MUST agree (verify.py cross-checks confidence
  and provenance between them). Staging NEVER writes the DB.
  CLI: `loop mint --entry <id> --matcher <machine-block-fields.json>`.
"""
from __future__ import annotations


def stage(instance, entry_id: str, matcher: dict):
    raise NotImplementedError("OPUS-FILLS: Phase 4 — see module docstring + SoT")
