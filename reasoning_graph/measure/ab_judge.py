"""A/B judging. Contract (gate G6):

judge(tasks_path, out_dir) -> Path
  Per response, by the task's answer_key kind:
    contains          -> deterministic substring match (method "string").
    refusal_expected  -> honest-refusal detection: correct iff the response
                         points to the shell / no-dedicated-tool rather than
                         fabricating a dedicated tool (method "refusal_check").
    judge             -> blind external LLM judge (method "llm_judge", transcript
                         stored) — arm label stripped, response canonicalized.
  Writes ab-judged-<date>.json rows {task_id, arm, correct, method,
  judge_transcript_ref}. Every row records its method; mixed methods are never
  blended into one accuracy number (ab_report enforces). This instance's 30
  tasks use only deterministic keys, so llm_judge is implemented but unused —
  the whole A/B scores reproducibly with zero judge cost.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

_REFUSAL_HONEST = ("bash", "shell", " rm", "tar", "no dedicated", "no specific",
                   "not a dedicated", "no single dedicated", "no built-in", "no direct",
                   "there is no", "no such tool")


def _score(task, response: str, out_dir: Path) -> tuple[bool, str, str | None]:
    key = task["answer_key"]
    kind = key["kind"]
    resp = (response or "").lower()
    if kind == "contains":
        return key["value"].lower() in resp, "string", None
    if kind == "refusal_expected":
        return any(tok in resp for tok in _REFUSAL_HONEST), "refusal_check", None
    if kind == "judge":
        return _llm_judge(task, response, out_dir)
    raise ValueError(f"unknown answer_key kind {kind!r}")


def _llm_judge(task, response, out_dir):
    prompt = (f"Task: {task['prompt']}\nExpected: {task['answer_key']['value']}\n"
              f"Answer: {response}\nReply with exactly CORRECT or WRONG.")
    try:
        cp = subprocess.run(["claude", "-p", prompt, "--model", "sonnet",
                             "--output-format", "json"],
                            capture_output=True, text=True, timeout=180)
        verdict = json.loads(cp.stdout).get("result", "")
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        verdict = ""
    ref = out_dir / "judge-transcripts" / f"{task['id']}.txt"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text(f"PROMPT:\n{prompt}\n\nVERDICT:\n{verdict}\n")
    return "correct" in verdict.lower(), "llm_judge", str(ref)


def judge(tasks_path, out_dir) -> Path:
    out_dir = Path(out_dir)
    tasks = {t["id"]: t for t in json.loads(Path(tasks_path).read_text())["tasks"]}
    rows = []
    for raw in sorted(out_dir.glob("ab-raw-*.json")):
        for r in json.loads(raw.read_text())["rows"]:
            task = tasks.get(r["task_id"])
            if not task:
                continue
            correct, method, ref = _score(task, r["response"], out_dir)
            rows.append({"task_id": r["task_id"], "arm": r["arm"], "correct": correct,
                         "method": method, "judge_transcript_ref": ref})
    date = time.strftime("%Y%m%d-%H%M%S")
    path = out_dir / f"ab-judged-{date}.json"
    path.write_text(json.dumps({"rows": rows}, indent=2))
    return path
