"""A/B runner — the two arms, matched protocol. Phone-hardened (council 2026-07-20).

run(instance, tasks_path, out_dir, model, arm) -> assembled raw path(s)
  spike-first (spike=True writes ab-spike-ok.json — Phase 6 must not start the
  60-call run until it exists); strictly serialized; per-(task,arm) checkpoints
  under out_dir/raw/ so a Phantom-Process-Killer kill resumes; fixed timeout;
  logged retries (retry_count, excluded from strict one-shot claims by the
  report). Arm A = task + ONLY the graph-slice JSON; arm B = task alone. Both
  run as EXTERNAL headless `claude -p ... --output-format json` subprocesses
  (build-session tokens never spent). Tokens from usage metadata =
  measured:api_usage. Exactly 30 unique task_ids per arm (G6).
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from ..primitives import AdapterError, adapter_for
from ..store import Store

_TIMEOUT = 180
_MAX_ATTEMPTS = 3
_ARM_A_INSTR = ("You are given the relevant slice of a knowledge graph as JSON. "
                "Answer the question in ONE sentence using that graph knowledge:")
_ARM_B_INSTR = "Answer the question in ONE sentence from your own knowledge:"


def _spike(model: str, out_dir: Path) -> dict:
    ok, meta = _one_call("Reply with exactly the word: ok", model)
    art = {"ok": ok, "model": model, "usage_parsed": meta.get("tokens"),
           "note": "single trivial headless call proving usage metadata parses on this host"}
    (out_dir / "ab-spike-ok.json").write_text(json.dumps(art, indent=2))
    if not ok:
        raise RuntimeError("A/B SPIKE FAILED — headless claude CLI did not return parseable "
                           "usage metadata on this host. STOP: the headline proof is "
                           "unbuildable as designed (SoT §7 entry condition).")
    return art


def _one_call(prompt: str, model: str) -> tuple[bool, dict]:
    """One headless call. Returns (ok, {response, tokens, retry_count})."""
    for attempt in range(_MAX_ATTEMPTS):
        try:
            cp = subprocess.run(["claude", "-p", prompt, "--model", model,
                                 "--output-format", "json"],
                                capture_output=True, text=True, timeout=_TIMEOUT)
            data = json.loads(cp.stdout)
            usage = data.get("usage", {})
            resp = data.get("result", "")
            if resp and "input_tokens" in usage:
                return True, {"response": resp, "retry_count": attempt,
                              "tokens": {"input": usage["input_tokens"],
                                         "output": usage["output_tokens"],
                                         "basis": "measured:api_usage"}}
        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
            pass
        time.sleep(1)
    return False, {"response": "", "retry_count": _MAX_ATTEMPTS,
                   "tokens": {"input": 0, "output": 0, "basis": "measured:api_usage"}}


def _graph_slice(instance, task) -> str:
    g = task.get("graph") or {}
    kind = g.get("kind")
    try:
        if kind == "primitive":
            out = adapter_for(instance).run(g["primitive"], g.get("args", {}))
            out = {k: v for k, v in out.items() if not k.startswith("_argv")}
            return json.dumps(out)[:2000]
        if kind == "neighbors":
            want = g.get("edge_type")   # typed traversal: only this edge kind if declared
            with Store.open(instance) as s:
                nb = [{"target": e["target"], "edge_type": e["kind"],
                       "confidence": e["confidence"], "basis": e["basis"],
                       "synthesis_chain": e["synthesis_chain"]}
                      for e in s.neighbors(g["node"], "out")
                      if want is None or e["kind"] == want]
            return json.dumps(nb)[:2000]
        if kind == "node":
            with Store.open(instance) as s:
                n = s.node(g["node"])
            return json.dumps(n)[:2000]
    except (AdapterError, KeyError, Exception):
        return "{}"
    return "{}"


def _prompt_for(instance, task, arm: str) -> str:
    if arm == "A":
        return f"{task['prompt']}\n\n{_ARM_A_INSTR}\n{_graph_slice(instance, task)}"
    return f"{task['prompt']}\n\n{_ARM_B_INSTR}"


def run(instance, tasks_path, out_dir, model: str = "sonnet", arm: str = "both") -> dict:
    out_dir = Path(out_dir)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    tasks = json.loads(Path(tasks_path).read_text())["tasks"]
    arms = ["A", "B"] if arm == "both" else [arm]

    if not (out_dir / "ab-spike-ok.json").exists():
        _spike(model, out_dir)

    date = time.strftime("%Y%m%d-%H%M%S")
    written = {}
    for a in arms:
        rows = []
        for t in tasks:
            cp_path = raw_dir / f"{t['id']}-{a}.json"
            if cp_path.exists():                       # resume: never re-call
                rows.append(json.loads(cp_path.read_text()))
                continue
            prompt = _prompt_for(instance, t, a)
            ok, meta = _one_call(prompt, model)
            row = {"task_id": t["id"], "arm": a, "prompt_stored": prompt,
                   "response": meta["response"], "tokens": meta["tokens"],
                   "model": model, "started_at": time.time(),
                   "retry_count": meta["retry_count"], "ok": ok}
            cp_path.write_text(json.dumps(row, indent=2))
            rows.append(row)
        path = out_dir / f"ab-raw-{a}-{date}.json"
        path.write_text(json.dumps({"arm": a, "model": model, "rows": rows}, indent=2))
        written[a] = str(path)
    return {"written": written, "date": date}
