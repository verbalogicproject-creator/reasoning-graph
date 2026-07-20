#!/usr/bin/env python3
"""Gate runner. Verifies gate integrity BEFORE running anything, three ways
(council 2026-07-20 — the manifest alone was self-referential):
  1. MANIFEST-GATES.sha256 over every gates/ file it lists;
  2. EXTERNAL ANCHOR: /root/reasoning-graph/.reasoning-graph-gates-anchor.sha256
     (instance-0 root, outside this repo's write mandate) must contain the
     sha256 OF the manifest itself — regenerating the manifest in-repo is
     visible unless the attacker also writes outside their mandate;
  3. GIT: if the repo has commits, `git status --porcelain -- gates/` must be
     empty except gates/BUDGET-LOG.md (the one legitimately mutable file) and
     a not-yet-committed gates/CORE-LOCK.sha256 (g3 commits it on creation).
Any mismatch → refuse to run (exit 4). Then runs g0..g8 in order (or --only).

Verdicts per gate: 0 PASS · 1 FAIL · 2 NOT-BUILT · 5 INFRA-FLAKE (re-run the
gate before diagnosing code — on this host a timeout/signal-kill is a phone
hiccup until a re-run says otherwise).

--resume: skips gates recorded PASS in ../.gates-state.json under the SAME
manifest digest — an OS-level interruption restarts at the first
not-yet-passed gate instead of Phase 0 (state lives at the repo root, not in
gates/, so it is never confused with the tamper-protected suite).

Exit: 4 tamper · 1 any FAIL · 5 any INFRA-FLAKE (and no FAIL) · 0 otherwise.
The ultimate arbiter is the human re-running this file.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ANCHOR_PATH, FAIL, GATES_DIR, INFRA, NOT_BUILT, PASS,  # noqa: E402
                     REPO, TAMPER, is_infra_exit, load_manifest, run, sha256_file)

GATES = ["g0_substrate_intact", "g1_schema_agnosticism", "g2_edge_confidence",
         "g3_resolver_refusal", "g4_loop_mechanized", "g5_frontier_rate",
         "g6_ab_ran", "g7_second_corpus", "g8_codification_bar"]
VERDICT = {PASS: "PASS", FAIL: "FAIL", NOT_BUILT: "NOT-BUILT", INFRA: "INFRA-FLAKE"}
STATE_PATH = REPO / ".gates-state.json"
MANIFEST_PATH = GATES_DIR / "MANIFEST-GATES.sha256"
MUTABLE_IN_GATES = {"BUDGET-LOG.md", "CORE-LOCK.sha256", ".gitignore"}


def verify_integrity() -> list[str]:
    problems: list[str] = []

    # 1. Manifest over listed files.
    if not MANIFEST_PATH.is_file():
        return ["MANIFEST-GATES.sha256 is missing"]
    manifest = load_manifest(MANIFEST_PATH)
    for rel, digest in manifest.items():
        p = GATES_DIR / rel
        if not p.is_file():
            problems.append(f"missing: {rel}")
        elif sha256_file(p) != digest:
            problems.append(f"modified: {rel}")
    on_disk = ({p.name for p in GATES_DIR.glob("*.py")}
               | {p.name for p in GATES_DIR.glob("*.json")}
               | {f"eyal-approvals/{p.name}" for p in (GATES_DIR / "eyal-approvals").glob("*.json")})
    for name in sorted(on_disk - set(manifest)):
        problems.append(f"unlisted file in gates/: {name}")

    # 2. External anchor (outside this repo's write mandate).
    if ANCHOR_PATH.is_file():
        anchored = ANCHOR_PATH.read_text().split()[0]
        actual = sha256_file(MANIFEST_PATH)
        if anchored != actual:
            problems.append(f"external anchor mismatch: {ANCHOR_PATH} holds {anchored[:12]}…, "
                            f"manifest is {actual[:12]}… — the manifest was regenerated")
    else:
        problems.append(f"external anchor missing: {ANCHOR_PATH} (write it from OUTSIDE "
                        "the build session; see SoT §10)")

    # 3. Git cleanliness of gates/ (BUDGET-LOG.md + uncommitted CORE-LOCK exempt).
    r = subprocess.run(["git", "status", "--porcelain", "--", "gates/"],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode == 0:
        dirty = [ln for ln in r.stdout.splitlines()
                 if ln.strip() and Path(ln.split(None, 1)[1]).name not in MUTABLE_IN_GATES]
        for ln in dirty:
            problems.append(f"git-dirty in gates/: {ln.strip()}")
    else:
        problems.append("git unavailable or no repository — the delivery contract "
                        "requires an initial commit before the build session (SoT §10)")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="comma-separated gate prefixes, e.g. g0 or g0,g3")
    ap.add_argument("--resume", action="store_true",
                    help="skip gates recorded PASS under the same manifest digest")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    problems = verify_integrity()
    if problems:
        print("GATE INTEGRITY CHECK FAILED — refusing to run:")
        for p in problems:
            print(f"  {p}")
        return TAMPER

    manifest_digest = sha256_file(MANIFEST_PATH)
    state = {}
    if STATE_PATH.is_file():
        try:
            state = json.loads(STATE_PATH.read_text())
        except json.JSONDecodeError:
            state = {}
    if state.get("manifest") != manifest_digest:
        state = {"manifest": manifest_digest, "verdicts": {}}

    selected = GATES
    if args.only:
        prefixes = tuple(x.strip() for x in args.only.split(","))
        selected = [g for g in GATES if g.startswith(prefixes)]

    results = {}
    for gate in selected:
        if args.resume and state["verdicts"].get(gate) == "PASS":
            results[gate] = PASS
            if not args.json:
                print(f"=== {gate} === (resumed: PASS under current manifest)")
            continue
        code, out, err = run([sys.executable, str(GATES_DIR / f"{gate}.py")], timeout=1800)
        if is_infra_exit(code):
            code = INFRA
        results[gate] = code
        state["verdicts"][gate] = VERDICT.get(code, f"exit {code}")
        STATE_PATH.write_text(json.dumps(state, indent=2))
        if not args.json:
            print(out, end="")
            if err.strip():
                print(err, end="", file=sys.stderr)
            if code == INFRA:
                print(f"  !! {gate}: subprocess timed out or was signal-killed — "
                      "INFRA-FLAKE on this host; re-run before diagnosing code.")

    summary = {g: VERDICT.get(c, f"exit {c}") for g, c in results.items()}
    if args.json:
        print(json.dumps({"summary": summary,
                          "failed": any(c == FAIL for c in results.values()),
                          "infra_flakes": [g for g, c in results.items() if c == INFRA]},
                         indent=2))
    else:
        print("\n=== SUMMARY ===")
        for gate, verdict in summary.items():
            print(f"  {gate:24} {verdict}")
    if any(c == FAIL for c in results.values()):
        return FAIL
    if any(c == INFRA for c in results.values()):
        return INFRA
    return PASS


if __name__ == "__main__":
    sys.exit(main())
