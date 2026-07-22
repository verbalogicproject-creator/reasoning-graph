"""Measure — frontier-rate matches independent parse; ab_tasks/variants shapes."""
from __future__ import annotations
import json
import tempfile
from pathlib import Path
from reasoning_graph.schema import load_instance
from reasoning_graph.measure import frontier_rate, ab_tasks, ab_variants

ROOT = Path(__file__).resolve().parents[1]
I0 = ROOT / "instances" / "claude_code_tools" / "instance.json"


def test_frontier_rate_matches_independent_parse():
    inst = load_instance(I0)
    r = frontier_rate.compute(inst)
    assert r["entries_total"] == 11 and r["basis"] == "derived:fcl_log_parse"
    assert len(r["series"]) == 11 and len(r["batches"]) >= 2
    # cumulative classes are monotone non-decreasing
    cc = [s["cumulative_classes"] for s in r["series"]]
    assert cc == sorted(cc)


def test_ab_tasks_frozen_hash_and_subsets():
    inst = load_instance(I0)
    out = Path(tempfile.mkdtemp())
    p = ab_tasks.build(inst, out)
    tasks = json.loads(p.read_text())["tasks"]
    subs = {}
    for t in tasks:
        subs[t["subset"]] = subs.get(t["subset"], 0) + 1
    assert subs == {"fixture": 12, "organic": 10, "corpus_private": 8}
    assert (out / "ab-tasks.sha256").is_file()


def test_ab_variants_share_recomputed_answer_keys():
    inst = load_instance(I0)
    out = Path(tempfile.mkdtemp())
    p = ab_tasks.build(inst, out)
    vp = ab_variants.generate(inst, p, 2)
    vt = json.loads(Path(vp).read_text())["tasks"]
    assert all(t["subset"].endswith(":variant") and t.get("answer_key") for t in vt)
    originals = {t["prompt"] for t in json.loads(p.read_text())["tasks"]}
    assert all(t["prompt"] not in originals for t in vt)
