"""Parametric task-variant generator — the auto-scale harness (Eyal's declared
choice: N=30 now, scaling later is a command, not a project). OPUS-FILLS (Phase 5).

Contract (gate G6):

generate(instance, tasks_path, k) -> Path
  For each generatable task, emits k variants that differ textually
  (template slots: tool/rule/goal names drawn from the live graph; paraphrase
  frames declared in a template table — NEVER model-generated at run time, so
  generation is deterministic and offline) while SHARING the same answer key
  derivation (the key is recomputed per variant from the graph, not copied).
  Output ab-tasks-variants-k<k>.json, same schema as ab-tasks.json, subset
  suffixed ":variant". Contamination property: variant text never appears in
  any corpus file or pretraining-quotable doc — G6 spot-greps.
  This is how the ROADMAP's "scale to hundreds" claim becomes runnable later
  without re-authoring; at N=30 it is built and gate-exercised with k=2 on a
  sample, not used for the headline claim.
"""
from __future__ import annotations


def generate(instance, tasks_path, k: int) -> object:
    raise NotImplementedError("OPUS-FILLS: Phase 5 — see module docstring + SoT")
