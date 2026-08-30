#!/usr/bin/env python3
"""Runs p2-acceptance-fixture.json against query.py's IntentDrivenQuery and
reports recall per primitive type. Doubles as the seed for P5's measurement
harness (implementation-plan-reasoning-graph-v2-2026-07-13.md, P2 section) --
re-running this over time and watching recall trend up / misses trend down
across categories IS the frontier-call-rate-falling metric in miniature.
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from query import IntentDrivenQuery


def check(q, iq):
    p, a, e = q["primitive"], q["args"], q["expect"]
    try:
        if p == "want_to":
            r = iq.want_to(a["goal"], k=e.get("k", 10))
            ids = [x.get("node_id") for x in r]
            if e["check"] == "top_result":
                return (ids[:1] == [e["node_id"]], ids[:3])
            if e["check"] == "top_result_in":
                return (bool(ids) and ids[0] in e["node_ids"], ids[:3])
            if e["check"] == "node_in_topk":
                return (e["node_id"] in ids[: e.get("k", 10)], ids[:5])
        elif p == "can_it":
            r = iq.can_it(a["capability"])
            if e["check"] == "can_true_and_tool":
                return (r["can"] and e["tool"] in r["related_tools"], r["related_tools"][:5])
        elif p == "trace":
            r = iq.trace(a["from"], a["to"])
            if e["check"] == "found":
                return (r["found"] and r.get("path_length", 999) <= e["max_length"], r.get("path_length"))
        elif p == "why_not":
            r = iq.why_not(a["tool"], a["goal"])
            if e["check"] == "limitations_nonempty":
                return (len(r.get("limitations", [])) > 0, len(r.get("limitations", [])))
        elif p == "similar_to":
            r = iq.similar_to(a["tool"], k=e.get("k", 5))
            tools = [x.get("tool") for x in r if "error" not in x]
            if e["check"] == "node_in_topk_similar":
                return (e["tool"] in tools[: e.get("k", 5)], tools[:5])
        elif p == "alternatives":
            r = iq.alternatives(a["tool"])
            if e["check"] == "results_nonempty":
                return (len(r) > 0, len(r))
        elif p == "compose_for":
            r = iq.compose_for(a["goal"])
            tools = [t["tool"] for t in r.get("tools", [])]
            if e["check"] == "tools_nonempty":
                return (len(tools) > 0, tools)
            if e["check"] == "tool_sequence":
                return (tools == e["tools"], tools)
    except Exception as exc:
        return (False, f"ERROR: {exc}")
    return (False, "unrecognized check")


def main():
    fixture = json.loads((Path(__file__).parent / "p2-acceptance-fixture.json").read_text())
    iq = IntentDrivenQuery()

    by_primitive = defaultdict(lambda: [0, 0])
    results = []
    for q in fixture["queries"]:
        passed, detail = check(q, iq)
        by_primitive[q["primitive"]][0] += int(passed)
        by_primitive[q["primitive"]][1] += 1
        results.append((q["id"], q["primitive"], q.get("canonical", False), passed, detail))

    iq.close()

    print(f"{'ID':12} {'PRIMITIVE':12} {'CANON':6} {'PASS':5} DETAIL")
    for qid, prim, canon, passed, detail in results:
        print(f"{qid:12} {prim:12} {'yes' if canon else '':6} {'PASS' if passed else 'FAIL':5} {detail}")

    print("\nRecall by primitive:")
    total_p, total_n = 0, 0
    for prim, (p, n) in sorted(by_primitive.items()):
        print(f"  {prim:14} {p}/{n}  ({100*p/n:.0f}%)")
        total_p += p
        total_n += n
    print(f"\nOverall: {total_p}/{total_n} ({100*total_p/total_n:.0f}%)")

    canon = [(qid, passed) for qid, prim, c, passed, detail in results if c]
    canon_pass = sum(1 for _, p in canon if p)
    print(f"Canonical queries: {canon_pass}/{len(canon)} passing "
          f"({', '.join(qid for qid, p in canon if not p) or 'none failing'})")


if __name__ == "__main__":
    main()
