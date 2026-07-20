"""A/B judging. OPUS-FILLS (Phase 6). Contract (gate G6):

judge(tasks_path, raw_paths, out_dir) -> Path
  Per response, in priority order:
    exact/contains answer keys → deterministic string match (method: "string").
    refusal_expected → honest-refusal detection: the response declines/says
      no-coverage rather than fabricating (method: "refusal_check"; a fabricated
      confident answer scores WRONG — honesty is part of accuracy here).
    judge keys → blind LLM judge: sees task + answer key + the response with
      the arm label STRIPPED (method: "llm_judge"); full judge transcript stored.
      The judge call runs as an EXTERNAL headless CLI subprocess exactly like
      the arms (SoT §12: measurement NEVER spends build-session tokens — this
      applies to judging, not only to the arms; council 2026-07-20).
      CANONICALIZE before judging: strip JSON scaffolding / arm-characteristic
      boilerplate into comparable plain text, so blindness isn't defeated by
      style tells. Log a blindness spot-check: for a sample of judged rows,
      record a style-only arm-guess and report its accuracy in ab_report
      (blindness measured, not assumed).
  OUTCOME WIRING (council 2026-07-20; feeds retirement with real evidence):
    for every arm-A row, each minted edge (synthesis_chain non-NULL) appearing
    in the answer path receives loop.retire.record_outcome: "used" always,
    plus "confirmed" if the row judged correct / "contradicted" if judged
    wrong. This is retirement's organic evidence stream — without it the
    mechanism is fixture-only.
  Output ab-judged-<date>.json rows: {"task_id", "arm", "correct": bool,
  "method", "judge_transcript_ref": str|None}. Every row records its method —
  mixed-method results are never presented as one homogeneous accuracy number
  without the per-method breakdown (ab_report.py enforces).
"""
from __future__ import annotations


def judge(tasks_path, raw_paths, out_dir) -> object:
    raise NotImplementedError("OPUS-FILLS: Phase 6 — see module docstring + SoT")
