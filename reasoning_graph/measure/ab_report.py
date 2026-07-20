"""A/B report — the deliverable table. OPUS-FILLS (Phase 6). Contract (gate G6):

report(tasks_path, judged_path, raw_paths, out_dir) -> Path
  Writes ab-results-<date>.json + ab-results-<date>.md:
    per-task rows (task, subset, arm, tokens in/out, correct, method,
    refusal-honest, retry_count) and aggregates SPLIT BY SUBSET ONLY — the
    JSON schema has NO top-level blended accuracy field, by contract (council
    2026-07-20): a single N=30 number would launder the tuned-on fixture
    subset into a headline. G6 fails on any blended accuracy key.
    MANDATORY paired_stats block per subset: Wilson interval on each arm's
    accuracy AND McNemar's exact test on the paired correct/incorrect
    outcomes (arms answer identical prompts — the pairing is free power).
    All derived:*-labeled; at n<=12 per subset the interval IS the honest
    story — print it next to every point estimate, same font, same table.
    Retried rows (retry_count>0) are footnoted and excluded from strict
    one-shot claims.
    Plus: indexing/storage cost line (DB size, migration time — the
    RAG-vs-GraphRAG discipline of reporting costs beyond per-query tokens);
    exploratory: correlation of arm-A path_confidence vs correctness, labeled
    "exploratory — path_product_score is not a calibrated probability
    (arXiv:2601.11956)".
  The claim sentence is generated with FIXED scope wording: "PoC evidence on
  the claude-code-tools corpus (N=30); not a generalizable benchmark." Every
  number carries its basis label (measured:api_usage for tokens; derived:* for
  aggregates).
"""
from __future__ import annotations


def report(tasks_path, judged_path, raw_paths, out_dir) -> object:
    raise NotImplementedError("OPUS-FILLS: Phase 6 — see module docstring + SoT")
