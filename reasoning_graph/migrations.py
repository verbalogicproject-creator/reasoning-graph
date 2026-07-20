"""Migrations. One exists: m001_edge_confidence.

CORE RULE: this module is corpus-agnostic — it never names an edge kind, node
kind, or corpus id (gate G1 greps). The derivation table lives in the INSTANCE
GraphSchema: every EdgeKind carries its ConfidenceRule (basis + declared value
or derivation), and the instance-0 concrete table is spelled out in the SoT's
edge-confidence section + instances/claude_code_tools/graphschema.py.

OPUS-FILLS (Phase 2). Contract, frozen by this docstring + gate G2:

m001_edge_confidence(instance, dry_run=False, backup=True) -> dict
  1. If the profile's confidence column is absent:
     ALTER TABLE <profile.edges_table> ADD COLUMN <profile.edge_confidence> REAL
     (additive — existing columns and any name-based external SELECTs unaffected).
  2. Backfill every edge with NULL confidence, per edge kind:
     a. If the edge's synthesis-chain column is non-NULL: confidence = the
        minting matcher's declared confidence (read from the staged/minted
        matcher file the chain tag names), basis = "declared:matcher:<mint_id>".
        This PRECEDES the kind's default rule.
     b. Else per the kind's ConfidenceRule:
        - value is not None  → write value, basis = rule.basis
        - basis == "derived:source_rule_confidence" → read the source node's
          metadata confidence; if the source node declares none, write the
          schema-declared corpus minimum with basis "derived:corpus_min(<v>)"
          (the fallback value and its grounds are stated in the rule's
          formula_note — declared in the instance, not here).
     Basis is written into the properties JSON under "confidence_basis".
  3. Idempotent: only NULLs are backfilled, non-NULL confidence is never
     overwritten; a second run reports backfilled=0.
  4. backup=True copies the DB file to <db>.bak-m001 BEFORE any write.
  5. dry_run=True writes nothing and reports would-backfill counts.

Return shape (CLI `reasoning-graph migrate --json` prints exactly this):
  {"migration": "m001_edge_confidence", "applied": bool, "dry_run": bool,
   "edges_total": int, "backfilled": int, "by_basis": {label: count},
   "null_remaining": int, "backup": str|None}
null_remaining MUST be 0 after a real run on a fully-declared instance —
gate G2 fails otherwise.
"""
from __future__ import annotations


def m001_edge_confidence(instance, dry_run: bool = False, backup: bool = True) -> dict:
    raise NotImplementedError("OPUS-FILLS: Phase 2 — see module docstring + SoT")
