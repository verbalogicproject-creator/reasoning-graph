"""A/B runner — the two arms, matched protocol. OPUS-FILLS (Phase 6).

Contract (gate G6):

run(instance, tasks_path, out_dir, model, arm: "A"|"B"|"both") -> Path
  Arm A (graph): the task prompt + ONLY the traversal output (primitives
    adapter / resolve --json, verbatim JSON block) + a fixed instruction to
    answer from the provided graph result.
  Arm B (prose): the IDENTICAL prompt minus the graph block; the model
    re-derives in prose. NOTHING else differs (matched protocol,
    arXiv:2502.11371): same model, temperature 0, same max_tokens, one shot.
  Both arms run as EXTERNAL headless `claude` CLI subprocesses (build-session
  tokens are never consumed by measurement; the SoT pins the exact command
  shape). Tokens read from the CLI's usage metadata — the ONE legitimately
  measured number in the system, labeled "measured:api_usage".

  PHONE-HARDENING CONTRACT (council 2026-07-20; Android/proot host — Phantom
  Process Killer + thermal/network variability are the design case, not an edge):
  - SPIKE FIRST: `run(..., spike=True)` executes ONE trivial call and validates
    that usage metadata parses; writes ab-spike-ok.json. Phase 6 MUST NOT start
    the 60-call run until the spike artifact exists (G6 checks). If the spike
    fails, the headline proof is unbuildable as designed — stop and surface.
  - SERIALIZED: exactly one subprocess at a time; no parallelism, ever.
  - CHECKPOINTED: one JSON file per (task, arm) under <out>/raw/; the batch
    ab-raw-<arm>-<date>.json is ASSEMBLED from checkpoints at the end. A killed
    run resumes by skipping existing checkpoints — re-running is always safe.
  - TIMEOUT + LOGGED RETRIES: fixed per-call timeout; a retried call carries
    retry_count >= 1 in its row and is EXCLUDED from strict "one shot" claims —
    ab_report must footnote retried rows, never silently merge them.
  - The operator note (SoT §11): keep Termux foregrounded / hold a wake lock
    for the duration of the run.

  Output ab-raw-<arm>-<date>.json rows:
    {"task_id", "arm", "prompt_stored": str, "response": str,
     "tokens": {"input": int, "output": int, "basis": "measured:api_usage"},
     "model", "started_at", "retry_count": int}
  Exactly 30 rows per arm, task_ids UNIQUE within an arm (G6 enforces == and
  uniqueness, not >=). prompt_stored is REQUIRED verbatim — G6 greps arm-B
  prompts for node_ids / graph-block markers to prove no prompt leakage
  (0 hits or fail).
"""
from __future__ import annotations


def run(instance, tasks_path, out_dir, model: str, arm: str = "both") -> object:
    raise NotImplementedError("OPUS-FILLS: Phase 6 — see module docstring + SoT")
