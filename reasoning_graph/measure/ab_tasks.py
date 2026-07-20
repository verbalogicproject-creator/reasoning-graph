"""A/B task set — built and FROZEN before any arm runs.

CORE RULE: corpus-agnostic — the concrete task content comes from the instance
(instances/<name>/ab-task-seeds.json). No corpus vocabulary here (gate G1 greps).

build(instance, out_dir) -> Path
  Reads the instance's declared seeds, validates the declared shape (30 tasks;
  subsets fixture=12 / organic=10 / corpus_private=8; >= 2 refusal-expected
  organic), writes out_dir/ab-tasks.json + ab-tasks.sha256 (freeze). Editing
  tasks after a run flips the hash → G6 fails by construction.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def build(instance, out_dir) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    seeds = instance.root / "ab-task-seeds.json"
    if not seeds.is_file():
        raise FileNotFoundError(f"instance declares no A/B task seeds: {seeds}")
    tasks = json.loads(seeds.read_text())["tasks"]

    subsets: dict[str, int] = {}
    for t in tasks:
        subsets[t["subset"]] = subsets.get(t["subset"], 0) + 1
    refusals = [t for t in tasks if t["subset"] == "organic"
                and t["answer_key"]["kind"] == "refusal_expected"]
    if not (len(tasks) == 30 and subsets.get("fixture") == 12
            and subsets.get("organic") == 10 and subsets.get("corpus_private") == 8):
        raise ValueError(f"task-set shape violation: {len(tasks)} tasks, subsets {subsets} "
                         "(need 30: fixture=12 organic=10 corpus_private=8)")
    if len(refusals) < 2:
        raise ValueError(f"need >= 2 refusal-expected organic tasks, got {len(refusals)}")

    tasks_path = out_dir / "ab-tasks.json"
    payload = json.dumps({"tasks": tasks}, indent=2, sort_keys=True)
    tasks_path.write_text(payload)
    digest = hashlib.sha256(tasks_path.read_bytes()).hexdigest()
    (out_dir / "ab-tasks.sha256").write_text(f"{digest}  ab-tasks.json\n")
    return tasks_path
