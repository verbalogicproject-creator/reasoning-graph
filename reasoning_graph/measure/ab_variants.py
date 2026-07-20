"""Parametric task-variant generator — the auto-scale harness (Eyal's declared
choice: N=30 now, scaling later is a command, not a project).

generate(instance, tasks_path, k) -> Path
  For each task, emit k textual variants via declared paraphrase frames
  (deterministic, offline — never model-generated at run time). Each variant
  SHARES the original's answer_key (the key is declared, not re-derived per
  paraphrase), subset suffixed ":variant". Variant text never equals any
  original prompt (G6 checks). At N=30 this is built + gate-exercised at k=2 on
  a sample, NOT used for the headline claim — the road to hundreds, later.
"""
from __future__ import annotations

import json
from pathlib import Path

# Declared paraphrase frames — fixed table, no run-time model calls.
_FRAMES = [
    "Question — {p}",
    "Please answer concisely: {p}",
    "In one sentence: {p}",
    "I have a question. {p}",
    "Answer this: {p}",
]


def generate(instance, tasks_path, k: int) -> Path:
    tasks_path = Path(tasks_path)
    tasks = json.loads(tasks_path.read_text())["tasks"]
    originals = {t["prompt"] for t in tasks}
    out = []
    for t in tasks:
        for i in range(k):
            frame = _FRAMES[i % len(_FRAMES)]
            prompt = frame.format(p=t["prompt"])
            if prompt in originals:            # guarantee textual difference
                prompt = f"[v{i}] {prompt}"
            out.append({"id": f"{t['id']}-v{i}", "subset": t["subset"] + ":variant",
                        "prompt": prompt, "graph": t.get("graph"),
                        "answer_key": t["answer_key"]})   # shared, recomputed = identical
    variants_path = tasks_path.parent / f"ab-tasks-variants-k{k}.json"
    variants_path.write_text(json.dumps({"tasks": out, "k": k, "note":
        "parametric variants of the frozen task set; deterministic paraphrase frames; "
        "answer keys shared with originals. Not used for the headline N=30 claim."},
        indent=2, sort_keys=True))
    return variants_path
