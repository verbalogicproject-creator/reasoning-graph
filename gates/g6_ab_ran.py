#!/usr/bin/env python3
"""G6 — the A/B proof ran, honestly. Validates the frozen-before-run task set,
the raw arm artifacts (measured tokens, stored prompts), arm-B contamination
(zero graph leakage), judging records, the report's subset split, and the
variant generator sample. All artifact checks — the gate never re-runs the arms.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (CLI_NOT_IMPLEMENTED, INSTANCE0, INSTANCE0_DB, REPO,  # noqa: E402
                     Gate, cli)

RESULTS = REPO / "measure-results"


def main() -> int:
    g = Gate("g6_ab_ran", as_json="--json" in sys.argv)
    tasks_path = RESULTS / "ab-tasks.json"
    if not tasks_path.is_file():
        code, _, _ = cli(["measure", "ab-build-tasks", "--instance", str(INSTANCE0),
                          "--out", str(RESULTS), "--json"])
        return g.not_built("no frozen task set; measure ab-build-tasks "
                           + ("is a stub" if code == CLI_NOT_IMPLEMENTED else f"exit {code} — Phase 5/6 pending"))

    # 1. Task set: 30 tasks, declared subsets 12/10/8, >=2 refusal-expected organic.
    tasks = json.loads(tasks_path.read_text())["tasks"]
    subsets = {}
    for t in tasks:
        subsets[t["subset"]] = subsets.get(t["subset"], 0) + 1
    g.check("30 tasks, subsets fixture=12 organic=10 corpus_private=8",
            len(tasks) == 30 and subsets.get("fixture") == 12
            and subsets.get("organic") == 10 and subsets.get("corpus_private") == 8,
            f"got {subsets}")
    refusals = [t for t in tasks if t["subset"] == "organic"
                and t["answer_key"]["kind"] == "refusal_expected"]
    g.check(">=2 refusal-expected organic tasks (honesty scored)", len(refusals) >= 2)

    # 2. Freeze discipline: hash matches; tasks+hash mtimes precede every result file.
    sha_path = RESULTS / "ab-tasks.sha256"
    ok_hash = (sha_path.is_file()
               and sha_path.read_text().split()[0]
               == hashlib.sha256(tasks_path.read_bytes()).hexdigest())
    g.check("ab-tasks.sha256 matches (frozen before run)", ok_hash)
    raws = sorted(RESULTS.glob("ab-raw-*.json"))
    judged = sorted(RESULTS.glob("ab-judged-*.json"))
    reports = sorted(RESULTS.glob("ab-results-*.json"))
    later = [p.name for p in (*raws, *judged, *reports)
             if p.stat().st_mtime < max(tasks_path.stat().st_mtime, sha_path.stat().st_mtime if sha_path.is_file() else 0)]
    g.check("raw/judged/results files exist", bool(raws) and bool(judged) and bool(reports),
            f"raw={len(raws)} judged={len(judged)} results={len(reports)}")
    g.check("every result file postdates the frozen task set", bool(raws) and not later,
            "; ".join(later[:4]))

    # 2b. Spike-first entry condition (council 2026-07-20): one trivial headless
    #     call must have proven usage-metadata parses on THIS host before the
    #     60-call run was allowed to start.
    g.check("ab-spike-ok.json exists and predates the raw runs",
            (RESULTS / "ab-spike-ok.json").is_file()
            and (not raws or (RESULTS / "ab-spike-ok.json").stat().st_mtime
                 <= min(p.stat().st_mtime for p in raws)))

    # 3. Raw rows: both arms, EXACTLY 30 each, unique task_ids (a retried/
    #    resumed run must never double-count — council 2026-07-20), measured
    #    token basis, stored prompts, retries labeled.
    rows = [r for p in raws for r in json.loads(p.read_text())["rows"]]
    by_arm = {"A": [r for r in rows if r["arm"] == "A"], "B": [r for r in rows if r["arm"] == "B"]}
    uniq = all(len({r["task_id"] for r in arm_rows}) == len(arm_rows)
               for arm_rows in by_arm.values())
    g.check("N == 30 per arm, task_ids unique within arm",
            len(by_arm["A"]) == 30 and len(by_arm["B"]) == 30 and uniq,
            f"A={len(by_arm['A'])} B={len(by_arm['B'])} unique={uniq}")
    g.check("tokens carry basis measured:api_usage",
            all(r.get("tokens", {}).get("basis") == "measured:api_usage" for r in rows))
    g.check("prompts stored verbatim", all(r.get("prompt_stored") for r in rows))
    g.check("every row carries retry_count", all("retry_count" in r for r in rows))

    # 4. PROMPT-LEAKAGE check (renamed per council 2026-07-20 — this proves the
    #    PROMPT doesn't leak the graph; model-prior contamination is addressed
    #    separately, by the corpus-private subset's novel-fact construction):
    #    arm-B prompts contain ZERO graph content — distinctive node ids from
    #    the live DB + the framework's own JSON markers.
    con = sqlite3.connect(f"file:{INSTANCE0_DB}?mode=ro", uri=True)
    node_ids = [r[0] for r in con.execute(
        "SELECT node_id FROM nodes WHERE node_type IN ('synthesis_rule','handbook_capability','relic_script')")]
    con.close()
    markers = node_ids + ["path_product_score", '"edge_type"', '"confidence_basis"']
    hits = []
    for r in by_arm["B"]:
        text = r["prompt_stored"]
        for m in markers:
            if m in text:
                hits.append(f"{r['task_id']}:{m}")
    g.check(f"arm-B prompts clean of graph content ({len(markers)} markers)", not hits,
            "; ".join(hits[:5]))

    # 5. Judging: every judged row records its method; llm_judge rows keep transcripts.
    jrows = [r for p in judged for r in json.loads(p.read_text())["rows"]]
    g.check("every judged row records method",
            bool(jrows) and all(r.get("method") in ("string", "refusal_check", "llm_judge") for r in jrows))
    g.check("llm_judge rows keep transcript refs",
            all(r.get("judge_transcript_ref") for r in jrows if r.get("method") == "llm_judge"))

    # 6. Report: subset split ONLY (no blended headline), paired stats, claim
    #    scope wording, md table.
    rep = json.loads(reports[-1].read_text())
    agg = rep.get("aggregates_by_subset", {})
    g.check("aggregates split by subset incl. corpus_private",
            all(k in agg for k in ("fixture", "organic", "corpus_private")))
    g.check("NO top-level blended accuracy key (per-subset only — a single N=30 "
            "number would launder the tuned-on fixture subset)",
            "accuracy" not in rep and "accuracy_overall" not in rep)
    g.check("paired_stats per subset (Wilson interval + McNemar)",
            all(isinstance(agg.get(k), dict)
                and "wilson" in str(agg[k].get("paired_stats", agg[k]))
                and "mcnemar" in str(agg[k].get("paired_stats", agg[k]))
                for k in ("fixture", "organic", "corpus_private")))
    claim = rep.get("claim", "")
    g.check("claim carries fixed PoC scope wording",
            "PoC evidence" in claim and "not a generalizable benchmark" in claim, claim[:120])
    md = sorted(RESULTS.glob("ab-results-*.md"))
    g.check("markdown results table exists", bool(md) and "|" in md[-1].read_text())
    g.check("indexing/storage cost line present", bool(rep.get("costs")))

    # 7. Variant generator sample (the auto-scale harness), k=2.
    variants = sorted(RESULTS.glob("ab-tasks-variants-k*.json"))
    if g.check("variants sample exists (k>=2)", bool(variants)):
        vt = json.loads(variants[-1].read_text())["tasks"]
        g.check("variants share recomputed answer keys + :variant subset tag",
                bool(vt) and all(t["subset"].endswith(":variant") and t.get("answer_key") for t in vt))
        vtexts = [t["prompt"] for t in vt]
        base_texts = {t["prompt"] for t in tasks}
        g.check("variant prompts differ textually from originals",
                all(v not in base_texts for v in vtexts))
    return g.finish()


if __name__ == "__main__":
    sys.exit(main())
