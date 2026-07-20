#!/usr/bin/env python3
"""G3 — resolver + refusal boundary. Deterministic assertions on the tiny
fixture's planted content (clean chain / below-floor / contradiction / benign
cycle / island) plus the instance-0 known chain with an independent product
recomputation. On PASS writes CORE-LOCK.sha256 (used by G7 to prove corpus 2
required zero core edits).
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (CLI_NOT_IMPLEMENTED, GATES_DIR, INSTANCE0, INSTANCE0_DB,  # noqa: E402
                     REPO, Gate, cli, parse_json, run, sha256_file)


def main() -> int:
    g = Gate("g3_resolver_refusal", as_json="--json" in sys.argv)

    tmp = Path(tempfile.mkdtemp(prefix="g3-tiny-"))
    shutil.copytree(REPO / "tests" / "fixtures" / "tiny", tmp / "tiny")
    shutil.copy(REPO / "tests" / "fixtures" / "fcl-fixture.ngf.md", tmp / "fcl-fixture.ngf.md")
    run([sys.executable, str(tmp / "tiny" / "build_tiny.py"), str(tmp / "tiny")])
    inst = str(tmp / "tiny" / "instance.json")

    def resolve(*args):
        code, out, err = cli(["resolve", "--instance", inst, *args, "--json"])
        return code, parse_json(out), (out + err)

    code, payload, raw = resolve("--start", "loom_1", "--end", "dye_bath_2")
    if code == CLI_NOT_IMPLEMENTED:
        shutil.rmtree(tmp, ignore_errors=True)
        return g.not_built("resolve is a stub (Phase 3)")

    # 1. Clean 2-hop chain: ANSWER, exact product 1.0 * 0.95, basis on every hop.
    ok = (code == 0 and payload and payload.get("status") == "ANSWER"
          and payload.get("confidence_kind") == "path_product_score"
          and abs(payload.get("confidence", 0) - 0.95) < 1e-9
          and len(payload.get("path", [])) == 2
          and all(e.get("basis") for e in payload.get("path", [])))
    g.check("clean chain: ANSWER, product exactly 0.95, basis per hop", bool(ok), raw[-300:] if not ok else "")

    # 1b. Path-class disclosure (council 2026-07-20): a 1.0-only structural walk
    #     must be labeled structural_only; a path with any inferential (<1.0)
    #     edge is reasoning. Never absorbed silently into the product float.
    code, payload, raw = resolve("--start", "loom_1", "--end", "spindle_a")
    g.check("all-1.0 single hop labeled path_class=structural_only",
            code == 0 and (payload or {}).get("path_class") == "structural_only",
            raw[-200:])
    code, payload, raw = resolve("--start", "loom_1", "--end", "dye_bath_2")
    g.check("chain with a 0.95 edge labeled path_class=reasoning",
            code == 0 and (payload or {}).get("path_class") == "reasoning", raw[-200:])

    # 2. Below-floor single path: WEAK_ANSWER at 0.20 — honest, not hidden, not refused.
    code, payload, raw = resolve("--start", "loom_1", "--end", "pattern_card_1")
    ok = (code == 0 and payload and payload.get("status") == "WEAK_ANSWER"
          and abs(payload.get("confidence", 0) - 0.20) < 1e-9)
    g.check("below-floor: WEAK_ANSWER at 0.20", bool(ok), raw[-300:] if not ok else "")

    # 3. Contradiction: the only route crosses a contradicts-class edge → REFUSE,
    #    naming the contradicting pair. Refusal is exit 0 — a result, not an error.
    code, payload, raw = resolve("--start", "loom_2", "--end", "pattern_card_2")
    ref = (payload or {}).get("refusal") or {}
    ok = (code == 0 and payload and payload.get("status") == "REFUSE"
          and ref.get("reason") == "contradiction"
          and "guild_rule_x" in str(ref) and "guild_rule_y" in str(ref))
    g.check("contradiction: REFUSE naming the pair, exit 0", bool(ok), raw[-300:] if not ok else "")

    # 4. Benign reciprocal cycle must NOT refuse: loom_1 → spindle_b via rivals.
    code, payload, raw = resolve("--start", "loom_1", "--end", "spindle_b")
    ok = (code == 0 and payload and payload.get("status") == "ANSWER"
          and abs(payload.get("confidence", 0) - 0.90) < 1e-9)
    g.check("benign reciprocal cycle traversable: ANSWER at 0.90", bool(ok), raw[-300:] if not ok else "")

    # 5. Island: REFUSE(no_frozen_support) + a drafted FCL stub in the log's schema.
    code, payload, raw = resolve("--start", "loom_1", "--end", "dye_bath_3")
    ref = (payload or {}).get("refusal") or {}
    stub = ref.get("fcl_stub") or ""
    ok = (code == 0 and payload and payload.get("status") == "REFUSE"
          and ref.get("reason") == "no_frozen_support"
          and "[LOGGED]" in stub and "gap_shape" in stub)
    g.check("island: REFUSE(no_frozen_support) with drafted FCL stub", bool(ok), raw[-300:] if not ok else "")

    # 6. Instance 0: known rule chain — resolver product vs independent SQL product.
    con = sqlite3.connect(f"file:{INSTANCE0_DB}?mode=ro", uri=True)
    cols = {r[1] for r in con.execute("PRAGMA table_info(edges)")}
    if "confidence" not in cols:
        g.skip("instance-0 chain product", "m001 not applied yet (G2 pending)")
        product = None
    else:
        product = 1.0
        for s, t in [("dep_003_tool_execution_requires_error_handling", "anti_001_infinite_tool_loops"),
                     ("anti_001_infinite_tool_loops", "constr_002_max_iterations_safety")]:
            product *= con.execute(
                "SELECT confidence FROM edges WHERE source_node_id=? AND target_node_id=? LIMIT 1",
                (s, t)).fetchone()[0]
    con.close()
    if product is not None:
        code, out, err = cli(["resolve", "--instance", str(INSTANCE0),
                              "--start", "dep_003_tool_execution_requires_error_handling",
                              "--end", "constr_002_max_iterations_safety", "--json"])
        payload = parse_json(out)
        rc = (payload or {}).get("confidence")
        g.check("instance-0 chain: resolver == independent product (1e-9)",
                code == 0 and rc is not None and abs(rc - product) < 1e-9,
                f"resolver={rc} sql={product}")

    shutil.rmtree(tmp, ignore_errors=True)

    verdict = g.finish()
    if verdict == 0:
        lock = GATES_DIR / "CORE-LOCK.sha256"
        if not lock.exists():
            lines = [f"{sha256_file(p)}  {p.relative_to(REPO)}"
                     for p in sorted((REPO / "reasoning_graph").rglob("*.py"))]
            lock.write_text("\n".join(lines) + "\n")
            # Commit the lock immediately (council 2026-07-20): an uncommitted
            # .sha256 could be silently deleted + regenerated against a moved
            # baseline. Once committed, run_all's git-clean check and G7's git
            # probes make any regeneration a visible diff.
            import subprocess
            subprocess.run(["git", "add", str(lock)], cwd=REPO, capture_output=True)
            r = subprocess.run(["git", "commit", "-m", "CORE-LOCK at first G3 PASS "
                                "(baseline for G7's zero-core-edits proof)"],
                               cwd=REPO, capture_output=True, text=True)
            print(f"CORE-LOCK.sha256 written ({len(lines)} core files) and "
                  f"{'committed' if r.returncode == 0 else 'WRITTEN BUT NOT COMMITTED — commit it manually NOW'}"
                  " — G7 compares against the committed version")
    return verdict


if __name__ == "__main__":
    sys.exit(main())
