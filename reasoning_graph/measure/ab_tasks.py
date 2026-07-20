"""A/B task set — built and FROZEN before any arm runs. OPUS-FILLS (Phase 5).

CORE RULE: corpus-agnostic module — concrete task content comes from the
instance: build() reads the instance's declared seed sources (its acceptance
fixture, its logged organic queries) and the SoT's task-list section names the
instance-0 concrete tasks. No corpus vocabulary here (gate G1 greps).

Contract (gates G5/G6):

build(instance, out_dir) -> Path
  Writes ab-tasks.json: exactly 30 tasks in three declared subsets:
    "fixture"        (12) — drawn from the instance's acceptance fixture
                     (verified answer keys; the artifact NOTES the instance
                     query engine was tuned on these: they measure token cost,
                     not generalization)
    "organic"        (10) — from the instance's logged organic queries with
                     recorded conclusions; MUST include 2 refusal-expected
                     tasks (zero-coverage goals) scoring honesty
    "corpus_private" (8)  — answerable ONLY from this corpus, not pretraining
                     (facts that exist nowhere but this graph: which script a
                     given rule governs, which mint created a given edge and
                     at what confidence) — the contamination control
  Each task: {"id", "subset", "prompt", "answer_key": {"kind": "exact"|"contains"
  |"refusal_expected"|"judge", "value": ...}}.
  FREEZE: writes ab-tasks.sha256 next to it. Gate G6 verifies the hash matches
  and both file mtimes PRECEDE every results file. Editing tasks after a run =
  gate failure by construction.
"""
from __future__ import annotations


def build(instance, out_dir) -> object:
    raise NotImplementedError("OPUS-FILLS: Phase 5 — see module docstring + SoT")
