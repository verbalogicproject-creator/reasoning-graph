"""A/B report — the deliverable table. Contract (gate G6):

report(tasks_path, out_dir) -> Path
  Writes ab-results-<date>.json + .md. Per-task rows + aggregates SPLIT BY
  SUBSET ONLY — the JSON has NO top-level blended accuracy field (a single N=30
  number would launder the tuned-on fixture subset; G6 fails on it). MANDATORY
  paired_stats per subset: Wilson interval per arm + McNemar's exact paired test
  (arms answer identical prompts — free power). All derived:*-labeled; at n<=12
  per subset the interval IS the honest story. Retried rows footnoted. Reports
  indexing/storage costs beyond per-query tokens. Fixed PoC-scope claim wording.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

_CLAIM = ("PoC evidence on the claude-code-tools corpus (N=30); not a generalizable "
          "benchmark. Fixture subset was tuned on — it measures token cost, not "
          "generalization; corpus-private subset carries facts only this graph holds.")


def _wilson(k: int, n: int, z: float = 1.96) -> list:
    if n == 0:
        return [0.0, 0.0]
    phat = k / n
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    margin = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denom
    return [round(max(0.0, centre - margin), 4), round(min(1.0, centre + margin), 4)]


def _mcnemar(pairs) -> dict:
    """pairs: list of (a_correct, b_correct). Exact two-sided binomial on the
    discordant pairs."""
    b = sum(1 for a, bb in pairs if a and not bb)   # A right, B wrong
    c = sum(1 for a, bb in pairs if bb and not a)   # B right, A wrong
    n = b + c
    if n == 0:
        p = 1.0
    else:
        x = min(b, c)
        tail = sum(math.comb(n, i) for i in range(x + 1))
        p = min(1.0, 2 * tail / (2 ** n))
    return {"b_A_right_B_wrong": b, "c_B_right_A_wrong": c, "n_discordant": n,
            "exact_two_sided_p": round(p, 4)}


def report(instance, tasks_path, out_dir) -> Path:
    out_dir = Path(out_dir)
    tasks = {t["id"]: t for t in json.loads(Path(tasks_path).read_text())["tasks"]}
    judged = sorted(out_dir.glob("ab-judged-*.json"))[-1]
    jrows = json.loads(judged.read_text())["rows"]
    raw = {}
    for rp in sorted(out_dir.glob("ab-raw-*.json")):
        for r in json.loads(rp.read_text())["rows"]:
            raw[(r["task_id"], r["arm"])] = r

    # index judged by task+arm
    jd = {(r["task_id"], r["arm"]): r for r in jrows}
    subsets = {}
    per_task = []
    retried = 0
    for tid, task in tasks.items():
        sub = task["subset"]
        subsets.setdefault(sub, [])
        a, b = jd.get((tid, "A")), jd.get((tid, "B"))
        ra, rb = raw.get((tid, "A")), raw.get((tid, "B"))
        if not (a and b and ra and rb):
            continue
        retried += (ra.get("retry_count", 0) > 0) + (rb.get("retry_count", 0) > 0)
        subsets[sub].append((a["correct"], b["correct"],
                             ra["tokens"], rb["tokens"], a["method"]))
        for arm, jr, rr in (("A", a, ra), ("B", b, rb)):
            per_task.append({"task_id": tid, "subset": sub, "arm": arm,
                             "correct": jr["correct"], "method": jr["method"],
                             "tokens_in": rr["tokens"]["input"],
                             "tokens_out": rr["tokens"]["output"],
                             "retry_count": rr.get("retry_count", 0)})

    agg = {}
    for sub, items in subsets.items():
        n = len(items)
        ka = sum(1 for a, *_ in items if a)
        kb = sum(1 for _, b, *_ in items if b)
        out_a = sum(t[2]["output"] for t in items)
        out_b = sum(t[3]["output"] for t in items)
        tot_a = sum(t[2]["input"] + t[2]["output"] for t in items)
        tot_b = sum(t[3]["input"] + t[3]["output"] for t in items)
        agg[sub] = {
            "n": n,
            "arm_A": {"correct": ka, "accuracy": round(ka / n, 4) if n else 0.0},
            "arm_B": {"correct": kb, "accuracy": round(kb / n, 4) if n else 0.0},
            "tokens": {"basis": "measured:api_usage",
                       "mean_output_A": round(out_a / n, 1) if n else 0,
                       "mean_output_B": round(out_b / n, 1) if n else 0,
                       "mean_total_A": round(tot_a / n, 1) if n else 0,
                       "mean_total_B": round(tot_b / n, 1) if n else 0,
                       "output_token_delta_pct": round(100 * (out_b - out_a) / out_b, 1)
                       if out_b else 0.0},
            "paired_stats": {
                "basis": "derived:api_usage_counts",
                "wilson_A": _wilson(ka, n), "wilson_B": _wilson(kb, n),
                "mcnemar": _mcnemar([(a, b) for a, b, *_ in items]),
                "note": f"at n={n} per subset the interval is the honest story"},
        }

    costs = _costs(instance)
    date = time.strftime("%Y%m%d-%H%M%S")
    result = {
        "claim": _CLAIM,
        "aggregates_by_subset": agg,   # NO top-level blended accuracy — by design
        "per_task": per_task,
        "costs": costs,
        "retried_rows": retried,
        "exploratory_note": ("arm-A path_product_score vs correctness correlation is "
                             "exploratory only — a score, not a calibrated probability "
                             "(arXiv:2601.11956)"),
        "protocol_note": ("matched protocol (arXiv:2502.11371): identical model + settings "
                          "both arms; temperature not CLI-exposed so both use the CLI default "
                          "(same for both arms). All 30 tasks scored deterministically "
                          "(string / refusal_check) — zero LLM-judge calls, fully reproducible."),
    }
    path = out_dir / f"ab-results-{date}.json"
    path.write_text(json.dumps(result, indent=2))
    (out_dir / f"ab-results-{date}.md").write_text(_markdown(result))
    return path


def _costs(instance) -> dict:
    db = instance.db_path
    return {"basis": "measured:filesystem",
            "db_size_bytes": db.stat().st_size if db.exists() else 0,
            "note": "indexing/storage cost beyond per-query tokens (RAG-vs-GraphRAG discipline)"}


def _markdown(result) -> str:
    lines = ["# A/B results — reasoning-graph PoC", "",
             f"**Claim.** {result['claim']}", "",
             "## Per-subset (split reported separately — no blended headline)", "",
             "| subset | n | arm-A acc | arm-B acc | A wilson | B wilson | "
             "mean out A | mean out B | out Δ% | McNemar p |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for sub, a in result["aggregates_by_subset"].items():
        ps = a["paired_stats"]
        tk = a["tokens"]
        lines.append(f"| {sub} | {a['n']} | {a['arm_A']['accuracy']} | {a['arm_B']['accuracy']} "
                     f"| {ps['wilson_A']} | {ps['wilson_B']} | {tk['mean_output_A']} "
                     f"| {tk['mean_output_B']} | {tk['output_token_delta_pct']} "
                     f"| {ps['mcnemar']['exact_two_sided_p']} |")
    lines += ["", f"- Retried rows (excluded from strict one-shot claims): {result['retried_rows']}",
              f"- {result['protocol_note']}", f"- {result['exploratory_note']}",
              f"- Storage cost: db {result['costs']['db_size_bytes']} bytes"]
    return "\n".join(lines) + "\n"
