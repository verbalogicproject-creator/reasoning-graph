"""Shared gate helpers. Gates are SELF-CONTAINED verifiers: independent
recomputation uses sqlite3/hashlib/subprocess directly — never the package under
test — and the package is exercised only through its public CLI in subprocesses.

Verdict exit codes (run_all.py and every gate):
  0 PASS   — every check green
  1 FAIL   — a built capability violates its contract
  2 NOT-BUILT — the capability under test is still an OPUS-FILLS stub
               (CLI exit 3, missing artifact of an unreached phase)
  4 TAMPER — manifest/git/anchor mismatch (run_all only)
  5 INFRA-FLAKE — a subprocess was timed out or signal-killed (exit 124 /
               negative / 137): on this host (proot/Android, thermal +
               Phantom Process Killer) that is a PHONE HICCUP until a re-run
               says otherwise. Re-run the gate before diagnosing code — never
               burn build tokens "fixing" an OS kill (council 2026-07-20).

This file is covered by MANIFEST-GATES.sha256 like every gate.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

GATES_DIR = Path(__file__).resolve().parent
REPO = GATES_DIR.parent
INSTANCE0 = REPO / "instances" / "claude_code_tools" / "instance.json"
INSTANCE0_DB = Path("/root/reasoning-graph/kgs/reasoning-graph.db")
INSTANCE0_ROOT = Path("/root/reasoning-graph")

PASS, FAIL, NOT_BUILT, TAMPER, INFRA = 0, 1, 2, 4, 5
CLI_NOT_IMPLEMENTED = 3
ANCHOR_PATH = Path("/root/reasoning-graph/.reasoning-graph-gates-anchor.sha256")
# ^ lives in instance-0's root — OUTSIDE this repo and outside the build
#   session's write mandate — so the gates manifest cannot be regenerated and
#   re-anchored in the same pass (council 2026-07-20, 4-agent convergence).


def is_infra_exit(code: int) -> bool:
    """Timeout (124) or signal-kill (negative, or 137 SIGKILL via shell) —
    infrastructure flake on this host, not evidence about the code."""
    return code == 124 or code == 137 or code < 0

# Independent copy of the closed basis vocabulary (schema.py is NOT imported —
# a tampered package must not be able to loosen this).
BASIS_EXACT = {
    "declared:structural_extraction",
    "declared:verbatim_extraction",
    "declared:inherited_curation_default",
    "declared:initial_guess",
    "derived:source_rule_confidence",
}
BASIS_PREFIXES = ("declared:matcher:", "derived:corpus_min(")


def basis_ok(label: str) -> bool:
    return label in BASIS_EXACT or label.startswith(BASIS_PREFIXES)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(argv, cwd=None, timeout=600, stdin_text=None):
    """Run a subprocess; return (exit_code, stdout, stderr). Never raises on
    non-zero exit — gates judge exit codes themselves."""
    try:
        cp = subprocess.run(argv, cwd=cwd, timeout=timeout, capture_output=True,
                            text=True, input=stdin_text)
        return cp.returncode, cp.stdout, cp.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s: {argv}"
    except FileNotFoundError as exc:
        return 127, "", str(exc)


def cli(args, timeout=600):
    """Invoke the reasoning-graph CLI via `python3 -m reasoning_graph.cli`
    (works installed or not)."""
    return run([sys.executable, "-m", "reasoning_graph.cli", *args],
               cwd=REPO, timeout=timeout)


def parse_json(stdout: str):
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


class Gate:
    """Check collector: gate.check(name, ok, detail); gate.finish() prints the
    table (+ optional JSON) and returns the verdict exit code."""

    def __init__(self, name: str, as_json: bool = False):
        self.name = name
        self.as_json = as_json
        self.checks: list[tuple[str, str, str]] = []  # (status, name, detail)

    def check(self, name: str, ok: bool, detail: str = "") -> bool:
        self.checks.append(("PASS" if ok else "FAIL", name, detail))
        return ok

    def skip(self, name: str, detail: str = "") -> None:
        self.checks.append(("SKIP", name, detail))

    def not_built(self, detail: str) -> int:
        self.checks.append(("NOT-BUILT", self.name, detail))
        return self.finish()

    def infra(self, name: str, detail: str = "") -> None:
        """A subprocess died by timeout/signal — record as INFRA, not FAIL."""
        self.checks.append(("INFRA", name, detail))

    def finish(self) -> int:
        statuses = [s for s, _, _ in self.checks]
        if "FAIL" in statuses:
            verdict, code = "FAIL", FAIL
        elif "INFRA" in statuses:
            verdict, code = "INFRA-FLAKE", INFRA
        elif "NOT-BUILT" in statuses:
            verdict, code = "NOT-BUILT", NOT_BUILT
        else:
            verdict, code = "PASS", PASS
        if self.as_json:
            print(json.dumps({"gate": self.name, "verdict": verdict,
                              "checks": [{"status": s, "name": n, "detail": d}
                                         for s, n, d in self.checks]}, indent=2))
        else:
            print(f"=== {self.name} ===")
            for s, n, d in self.checks:
                print(f"  [{s:9}] {n}" + (f" — {d}" if d else ""))
            print(f"  verdict: {verdict}")
        return code


def load_manifest(path: Path) -> dict:
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            digest, _, rel = line.partition("  ")
            out[rel] = digest
    return out
