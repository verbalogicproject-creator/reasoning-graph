#!/usr/bin/env python3
"""G0 — substrate-intact. Pre-flight AND permanent regression gate: re-run after
every Opus phase. Proves the P0–P2 substrate this framework builds on is exactly
as delivered: the P2 fixture is 20/20 + 3/3 canonical, the graph baseline holds,
nai composes a real weighted path, and no frozen file has been touched.

Runs GREEN at skeleton-delivery time — if it doesn't, nothing else is trustworthy.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (GATES_DIR, INSTANCE0_DB, INSTANCE0_ROOT, Gate,  # noqa: E402
                     load_manifest, parse_json, run, sha256_file)

BASELINE_NODES = 639
BASELINE_EDGES = 856
MINT_001_EDGES = 11
NAI_PATH_QUERY = ("path dep_003_tool_execution_requires_error_handling "
                  "constr_002_max_iterations_safety")


def main() -> int:
    g = Gate("g0_substrate_intact", as_json="--json" in sys.argv)

    # 1. Frozen-file manifest (query.py, the P2 fixture pair, nai sources,
    #    the 8 top-level synthesis-rules files). minted/, staged/, the FCL log
    #    and the DB are legitimately mutable and deliberately NOT in it.
    manifest_path = GATES_DIR / "FROZEN-MANIFEST.sha256"
    if g.check("frozen manifest exists", manifest_path.is_file(), str(manifest_path)):
        mismatches = []
        manifest = load_manifest(manifest_path)
        for rel, digest in manifest.items():
            p = INSTANCE0_ROOT / rel
            if not p.is_file():
                mismatches.append(f"MISSING {rel}")
            elif sha256_file(p) != digest:
                mismatches.append(rel)
        g.check(f"frozen files unchanged ({len(manifest)} files)",
                not mismatches, "; ".join(mismatches[:5]))

    # 2. P2 acceptance fixture — 20/20, 3/3 canonical, by actually running it.
    code, out, err = run([sys.executable, "p2_fixture_runner.py"], cwd=INSTANCE0_ROOT)
    ok_overall = bool(re.search(r"Overall:\s*20/20", out))
    ok_canon = bool(re.search(r"Canonical queries:\s*3/3", out))
    g.check("p2_fixture_runner exit 0", code == 0, (err or out)[-300:] if code else "")
    g.check("fixture recall 20/20", ok_overall)
    g.check("canonical queries 3/3", ok_canon)

    # 3. Graph baseline — raw SQL, independent of any package code.
    import sqlite3
    con = sqlite3.connect(f"file:{INSTANCE0_DB}?mode=ro", uri=True)
    nodes = con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    edges = con.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    minted = con.execute(
        "SELECT COUNT(*) FROM edges WHERE synthesis_chain LIKE 'mint_001%'"
    ).fetchone()[0]
    con.close()
    g.check(f"nodes >= {BASELINE_NODES}", nodes >= BASELINE_NODES, f"nodes={nodes}")
    g.check(f"edges >= {BASELINE_EDGES}", edges >= BASELINE_EDGES, f"edges={edges}")
    g.check(f"mint_001 provenance edges == {MINT_001_EDGES}", minted == MINT_001_EDGES,
            f"found {minted}")

    # 4. nai weighted-path probe — the P1 read side still composes confidence.
    code, out, err = run([sys.executable, "-m", "nai", "--db",
                          str(INSTANCE0_DB), "--query", NAI_PATH_QUERY, "--json"],
                         cwd=INSTANCE0_ROOT / "systems")
    payload = parse_json(out[out.index("{"):]) if "{" in out else None
    ok_path = bool(payload and payload.get("stats", {}).get("path_confidence") is not None
                   and payload.get("stats", {}).get("path_length", 0) >= 2)
    g.check("nai path query exit 0", code == 0, (err or out)[-300:] if code else "")
    g.check("nai multi-hop path with path_confidence", ok_path,
            f"stats={payload.get('stats') if payload else None}")

    return g.finish()


if __name__ == "__main__":
    sys.exit(main())
