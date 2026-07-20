"""Freeze — P5: a VERIFIED matcher becomes graph content + provenance rows.
OPUS-FILLS (Phase 4). Contract (gate G4):

freeze(instance, staged_path, approve: bool = False) -> dict
  Gate: approve=True is REQUIRED for any write against a real instance DB
  (fixture instances may set "self_approve": true in instance.json — real
  instance 0 does not). The approval is recorded in evolution_log.
  Writes, in one transaction:
    1. The confirmed edges: edge_kind from the machine block, confidence =
       matcher's declared confidence, properties.confidence_basis =
       "declared:matcher:<mint_id>", synthesis_chain = "<mint_id> / <FCL ids>".
    2. Fact-loop rows (the tables already live in the store — schema_version 7):
       synthesis_facts (the rule statement), fact_validations (the verify()
       result), evolution_log (who/when/what + approval), insights (the pattern
       line from the FCL entry).
    3. Outcome counters init on the minted rule's node/file metadata:
       {"times_used": 0, "times_confirmed": 0, "times_contradicted": 0,
        "status": "active"} — retirement's raw material (retire.py).
    4. Moves <staged>.md → <minted_dir>/<mint_id>-MINTED.md with a Provenance:
       line; advances the FCL entry tag (fcl.advance_status → MINTED/FROZEN).
  IDEMPOTENT: keyed on synthesis_chain — re-running freeze for the same mint_id
  inserts 0 edges/rows and reports {"already_frozen": true}. Gate G4 runs it twice.
  Return: {"mint_id", "edges_inserted", "rows": {table: n}, "already_frozen": bool}
"""
from __future__ import annotations


def freeze(instance, staged_path, approve: bool = False) -> dict:
    raise NotImplementedError("OPUS-FILLS: Phase 4 — see module docstring + SoT")
