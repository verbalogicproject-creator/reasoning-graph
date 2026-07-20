#!/usr/bin/env python3
"""G7 — second corpus (STRETCH, Phase 8). The generality proof: the
lowering-ladder mini-corpus runs through the SAME core with only a new
GraphSchema declaration — CORE-LOCK.sha256 (written at G3 pass) must be
byte-identical, proving zero core edits. NOT-BUILT (never FAIL) if Phase 8
was dropped by the abort ladder.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (GATES_DIR, REPO, Gate, cli, parse_json,  # noqa: E402
                     sha256_file)

INSTANCE2 = REPO / "instances" / "lowering_ladder" / "instance.json"
FIXTURE_QUERIES = REPO / "instances" / "lowering_ladder" / "fixture-queries.json"


def main() -> int:
    g = Gate("g7_second_corpus", as_json="--json" in sys.argv)
    if not INSTANCE2.is_file():
        return g.not_built("stretch phase not built (instances/lowering_ladder absent) — "
                           "legitimate under the abort ladder")

    code, out, err = cli(["schema", "validate", "--instance", str(INSTANCE2), "--json"])
    payload = parse_json(out)
    g.check("second-corpus schema validates", code == 0 and bool(payload and payload.get("ok")),
            (err or out)[-200:])

    g.check("fixture-queries.json exists (5 queries)", FIXTURE_QUERIES.is_file())
    if FIXTURE_QUERIES.is_file():
        queries = json.loads(FIXTURE_QUERIES.read_text())["queries"]
        g.check("declares exactly 5 queries", len(queries) == 5)
        failures = []
        for q in queries:
            code, out, err = cli(["resolve", "--instance", str(INSTANCE2),
                                  *q["args"], "--json"])
            payload = parse_json(out) or {}
            if code != 0 or payload.get("status") != q["expect_status"]:
                failures.append(f"{q['id']}: got {payload.get('status')} (exit {code})")
        g.check("5/5 fixture queries return their declared status", not failures,
                "; ".join(failures))

    lock = GATES_DIR / "CORE-LOCK.sha256"
    if g.check("CORE-LOCK.sha256 exists (written at G3 pass)", lock.is_file()):
        drift = []
        for line in lock.read_text().splitlines():
            digest, _, rel = line.partition("  ")
            p = REPO / rel
            if not p.is_file() or sha256_file(p) != digest:
                drift.append(rel)
        g.check("ZERO core edits since G3 (generality is declaration-only)",
                not drift, "; ".join(drift[:5]))
        # Council 2026-07-20: the lock file itself must be GIT-ANCHORED —
        # otherwise deleting + regenerating it after a core edit makes this
        # check vacuously true against a moved baseline.
        import subprocess
        committed = subprocess.run(["git", "log", "--oneline", "--", str(lock)],
                                   cwd=REPO, capture_output=True, text=True)
        clean = subprocess.run(["git", "status", "--porcelain", "--", str(lock)],
                               cwd=REPO, capture_output=True, text=True)
        g.check("CORE-LOCK is committed and unmodified in git (no silent regeneration)",
                committed.returncode == 0 and bool(committed.stdout.strip())
                and clean.returncode == 0 and not clean.stdout.strip(),
                (clean.stdout or committed.stderr)[:150])
    return g.finish()


if __name__ == "__main__":
    sys.exit(main())
