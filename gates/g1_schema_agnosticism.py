#!/usr/bin/env python3
"""G1 — schema + agnosticism. The framework/instance boundary, mechanically:
declarations load; the tiny fixture (alien domain, non-default names) round-trips;
undeclared kinds raise; and the core package contains ZERO instance vocabulary —
the grep token list is pulled from the live instance-0 DB at run time, so the
gate can't drift from the corpus.
"""
from __future__ import annotations

import re
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (CLI_NOT_IMPLEMENTED, INSTANCE0, INSTANCE0_DB, REPO,  # noqa: E402
                     Gate, cli, parse_json, run)

# Node kinds that are single generic English words get excluded from the grep
# (they'd false-positive on ordinary prose); agnosticism for those is proven by
# the tiny fixture instead. 'contradicts' is a framework-level concept both
# schemas declare — excluded by design.
GREP_EXCLUDE = {"tool", "example", "limitation", "prerequisite", "workaround", "contradicts"}


def main() -> int:
    g = Gate("g1_schema_agnosticism", as_json="--json" in sys.argv)

    # 1. Package imports; instance-0 declaration validates.
    code, out, err = run([sys.executable, "-c", "import reasoning_graph"], cwd=REPO)
    g.check("import reasoning_graph", code == 0, err[-200:] if code else "")
    code, out, err = cli(["schema", "validate", "--instance", str(INSTANCE0), "--json"])
    payload = parse_json(out)
    g.check("instance-0 schema validates", code == 0 and bool(payload and payload.get("ok")),
            (err or out)[-200:] if code else "")

    # 2. Tiny fixture (alien domain, non-default names) — copy, build, validate.
    tmp = Path(tempfile.mkdtemp(prefix="g1-tiny-"))
    shutil.copytree(REPO / "tests" / "fixtures" / "tiny", tmp / "tiny")
    shutil.copy(REPO / "tests" / "fixtures" / "fcl-fixture.ngf.md", tmp / "fcl-fixture.ngf.md")
    code, out, err = run([sys.executable, str(tmp / "tiny" / "build_tiny.py"), str(tmp / "tiny")])
    g.check("tiny fixture builds", code == 0, (err or out)[-200:])
    tiny_inst = tmp / "tiny" / "instance.json"
    code, out, err = cli(["schema", "validate", "--instance", str(tiny_inst), "--json"])
    payload = parse_json(out)
    g.check("tiny schema validates (non-default profile)", code == 0 and bool(payload and payload.get("ok")))

    # 3. Anti-hardcoding grep: kinds/ids from the LIVE DB vs core package source.
    con = sqlite3.connect(f"file:{INSTANCE0_DB}?mode=ro", uri=True)
    tokens = {r[0] for r in con.execute("SELECT DISTINCT node_type FROM nodes")}
    tokens |= {r[0] for r in con.execute("SELECT DISTINCT edge_type FROM edges")}
    tokens |= {r[0] for r in con.execute("SELECT node_id FROM nodes WHERE node_type='tool'")}
    con.close()
    tokens -= GREP_EXCLUDE
    offenders = []
    for py in sorted((REPO / "reasoning_graph").rglob("*.py")):
        text = py.read_text()
        for t in tokens:
            if re.search(rf"\b{re.escape(t)}\b", text):
                offenders.append(f"{py.relative_to(REPO)}:{t}")
    g.check(f"zero instance tokens in core ({len(tokens)} tokens checked)",
            not offenders, "; ".join(offenders[:6]))

    # 4. Behavior half (Phase 1): tiny round-trip + undeclared-kind raise, via CLI.
    code, out, err = cli(["resolve", "--instance", str(tiny_inst),
                          "--start", "loom_1", "--end", "spindle_a", "--json"])
    if code == CLI_NOT_IMPLEMENTED:
        g.checks.append(("NOT-BUILT", "tiny round-trip resolve (Phase 1)", "resolve is a stub"))
    else:
        payload = parse_json(out)
        g.check("tiny round-trip resolve answers", code == 0 and bool(payload)
                and payload.get("status") in ("ANSWER", "WEAK_ANSWER"), (err or out)[-200:])
        # plant an undeclared kind; any read that touches it must raise (exit 1)
        con = sqlite3.connect(tmp / "tiny" / "tiny.db")
        con.execute("INSERT INTO ties VALUES ('loom_1','spindle_a','sorcery',0.5,'{}',NULL)")
        con.commit(); con.close()
        code, out, err = cli(["resolve", "--instance", str(tiny_inst),
                              "--start", "loom_1", "--end", "spindle_a", "--json"])
        g.check("undeclared edge kind raises (exit 1, names the kind)",
                code == 1 and "sorcery" in (out + err), (out + err)[-200:])

    shutil.rmtree(tmp, ignore_errors=True)
    return g.finish()


if __name__ == "__main__":
    sys.exit(main())
