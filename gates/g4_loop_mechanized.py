#!/usr/bin/env python3
"""G4 — the loop, mechanized (+ retirement). Two halves:
REAL half — parse the live 11-entry FCL log; the promotion detector must
  reproduce history exactly ({FCL-001, FCL-007, FCL-008, FCL-009} recurring,
  nothing promotable — every recurring class is human-disposed, including
  FCL-008's rejection, which must be respected, never re-proposed).
FIXTURE half — full scan→promote→mint→verify→freeze on the tiny fixture with
  the canned matcher, against a SCRATCH copy; freeze twice (idempotency); then
  the retirement pass on declared counters (demote-not-delete; ratio before cap).
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (CLI_NOT_IMPLEMENTED, GATES_DIR, INSTANCE0, REPO,  # noqa: E402
                     Gate, cli, parse_json, run)

EXPECT_RECURRING = {"FCL-001", "FCL-007", "FCL-008", "FCL-009"}


def main() -> int:
    g = Gate("g4_loop_mechanized", as_json="--json" in sys.argv)

    # ---- REAL half ----
    code, out, err = cli(["loop", "scan", "--instance", str(INSTANCE0), "--json"])
    if code == CLI_NOT_IMPLEMENTED:
        return g.not_built("loop scan is a stub (Phase 4)")
    payload = parse_json(out)
    entries = {e.get("id"): e for e in (payload or {}).get("entries", [])}
    g.check("live log parses 11/11 entries", len(entries) == 11,
            f"got {sorted(entries)}")
    expected_ids = {f"FCL-{i:03d}" for i in range(1, 12)}
    g.check("entry ids FCL-001..FCL-011", set(entries) == expected_ids)
    g.check("every entry carries declared gap_shape + occurrences",
            all(e.get("gap_shape") and isinstance(e.get("recurrences", e.get("occurrences")), int)
                for e in entries.values()))

    code, out, err = cli(["loop", "promote", "--instance", str(INSTANCE0), "--json"])
    payload = parse_json(out) or {}
    recurring = set(payload.get("recurring", []))
    promotable = set(payload.get("promotable", []))
    g.check("recurring == {FCL-001,007,008,009} exactly", recurring == EXPECT_RECURRING,
            f"got {sorted(recurring)}")
    g.check("promotable == {} (all recurring classes human-disposed; FCL-008's "
            "rejection respected)", promotable == set(), f"got {sorted(promotable)}")

    # ---- FIXTURE half ----
    tmp = Path(tempfile.mkdtemp(prefix="g4-"))
    shutil.copytree(REPO / "tests" / "fixtures" / "tiny", tmp / "tiny")
    shutil.copy(REPO / "tests" / "fixtures" / "fcl-fixture.ngf.md", tmp / "fcl-fixture.ngf.md")
    run([sys.executable, str(tmp / "tiny" / "build_tiny.py"), str(tmp / "tiny")])
    inst = str(tmp / "tiny" / "instance.json")

    code, out, err = cli(["loop", "scan", "--instance", inst, "--json"])
    payload = parse_json(out) or {}
    g.check("fixture log parses 6/6", len(payload.get("entries", [])) == 6)

    code, out, err = cli(["loop", "promote", "--instance", inst, "--json"])
    payload = parse_json(out) or {}
    g.check("fixture pair promotable (FIX-003 + FIX-005, same declared gap_shape)",
            set(payload.get("promotable", [])) == {"FIX-003", "FIX-005"},
            f"got {payload.get('promotable')}")

    code, out, err = cli(["loop", "mint", "--instance", inst, "--entry", "FIX-005",
                          "--matcher", str(GATES_DIR / "g4-matcher.json"), "--json"])
    payload = parse_json(out) or {}
    staged = payload.get("staged_path", "")
    g.check("mint stages matcher-v2 file", code == 0 and staged and Path(staged).is_file(),
            (out + err)[-200:])
    if staged:
        text = Path(staged).read_text()
        g.check("staged file carries the machine block + provenance",
                "```yaml" in text and "mint_f_tension" in text and "FIX-003" in text)

    code, out, err = cli(["loop", "verify", "--instance", inst, "--staged", staged, "--json"])
    payload = parse_json(out) or {}
    g.check("verify: ok, >=1 confirmed, provenance fired",
            code == 0 and payload.get("ok") is True and payload.get("provenance_fired") is True
            and len(payload.get("confirmed", [])) >= 1, (out + err)[-250:])

    def minted_count():
        con = sqlite3.connect(tmp / "tiny" / "tiny.db")
        n = con.execute("SELECT COUNT(*) FROM ties WHERE chain_tag LIKE 'mint_f_tension%'").fetchone()[0]
        row = con.execute("SELECT trust, extra_json FROM ties WHERE chain_tag LIKE 'mint_f_tension%' LIMIT 1").fetchone()
        con.close()
        return n, row

    code, out, err = cli(["loop", "freeze", "--instance", inst, "--staged", staged, "--json"])
    n1, row = minted_count()
    basis_ok_ = bool(row and abs(row[0] - 0.75) < 1e-9
                     and json.loads(row[1] or "{}").get("confidence_basis") == "declared:matcher:mint_f_tension")
    g.check("freeze inserts tagged edge(s) at declared 0.75 + matcher basis",
            code == 0 and n1 >= 1 and basis_ok_, (out + err)[-250:])

    code, out, err = cli(["loop", "freeze", "--instance", inst, "--staged", staged, "--json"])
    payload = parse_json(out) or {}
    n2, _ = minted_count()
    g.check("freeze idempotent: second run inserts 0, reports already_frozen",
            n2 == n1 and payload.get("already_frozen") is True, f"n1={n1} n2={n2}")

    # ---- retirement (declared counters; demote-not-delete; ratio before cap) ----
    fixture = REPO / "tests" / "fixtures" / "retire-fixture.json"
    expected = json.loads(fixture.read_text())["expected"]
    code, out, err = cli(["loop", "retire", "--instance", inst,
                          "--fixture", str(fixture), "--json"])
    payload = parse_json(out) or {}
    demoted = [d.get("mint_id") for d in payload.get("demoted", [])]
    g.check("retire: demoted exactly per declared expectation",
            code == 0 and demoted == expected["demoted"], f"got {demoted}")
    g.check("retire: nothing deleted, dormant carries evidence",
            payload.get("deleted", []) == [] and all(d.get("evidence") for d in payload.get("demoted", [])),
            (out + err)[-200:])

    shutil.rmtree(tmp, ignore_errors=True)
    return g.finish()


if __name__ == "__main__":
    sys.exit(main())
