"""Frontier-call rate. OPUS-FILLS (Phase 5). Contract (gate G5):

compute(instance) -> {
  "entries_total": int,
  "series": [{"entry_id": str, "entry_index": int, "cumulative_classes": int,
              "is_new_class": bool}],           # log order, oldest first
  "batches": [{"label": str, "entries": int, "new_classes": int,
               "new_class_rate": float}],       # from the log's own batch markers
  "baseline": {...},   # the 2 historical organic batches computed as shipped
  "reading": str       # ONE honest sentence: falling / flat / rising / too-few-
                       # entries — computed from the numbers, never pre-claimed
}
Classes come from declared gap_shapes (sidecar + inline field). The gate
recomputes the series from its own independent parse and requires equality.
Every number is derived-from-declared-inputs; the output carries
"basis": "derived:fcl_log_parse" at top level.
"""
from __future__ import annotations


def compute(instance) -> dict:
    raise NotImplementedError("OPUS-FILLS: Phase 5 — see module docstring + SoT")
