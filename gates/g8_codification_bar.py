#!/usr/bin/env python3
"""G8 — the codification bar, at the house standard (declared_core /
frontmatter_rag / project_memory). Per Eyal's directive the docs bar is
NON-NEGOTIABLE — the abort ladder may drop the stretch corpus or the LLM judge,
never this. Checks: suite green; demo verbatim; INVARIANTS↔tests 1:1; numpy
byte-identical; docs complete (no OPUS-FILLS markers, required sections,
README quickstart EXECUTED); CHANGELOG hardening pass with RG-n issue ids.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import REPO, Gate, run  # noqa: E402

DOC_FILES = ["README.md", "CLAUDE.md", "HOW-TO-USE.md", "CODEBASE-REPORT.md",
             "RELEASE-NOTES.md", "ROADMAP.md", "CONTRIBUTING.md", "CHANGELOG.md"]
REQUIRED_SECTIONS = {
    "README.md": ["## The 60-second quickstart", "## How it fits together",
                  "## Design choices", "## Reading paths"],
    "RELEASE-NOTES.md": ["What's honest about the scope"],
    "ROADMAP.md": ["Explicitly out of scope"],
}
EXEMPT_FROM_MARKER_CHECK = {"examples/02_second_corpus.py"}  # stretch may stay a stub


def main() -> int:
    g = Gate("g8_codification_bar", as_json="--json" in sys.argv)

    # Phase detection: while Phase 7 is legitimately pending (demo still the
    # exit-3 stub AND OPUS-FILLS markers still present), the bar is NOT-BUILT,
    # not FAILED. Markers gone but demo still a stub = inconsistent → full
    # checks run and fail honestly.
    demo_code, _, _ = run([sys.executable, "-m", "reasoning_graph.demo"], cwd=REPO)
    any_markers = any("OPUS-FILLS" in p.read_text()
                      for p in list((REPO / "tests").rglob("*.py"))
                      + [REPO / f for f in DOC_FILES if (REPO / f).is_file()])
    if demo_code == 3 and any_markers:
        return g.not_built("Phase 7 pending — demo is a stub and OPUS-FILLS markers remain")

    # 1. Test suite green, and no OPUS-FILLS skips left in tests/.
    code, out, err = run([sys.executable, "-m", "pytest", "-q"], cwd=REPO, timeout=1200)
    g.check("pytest green", code == 0, (out + err)[-300:] if code else out.strip().splitlines()[-1])
    marker_hits = [str(p.relative_to(REPO)) for p in (REPO / "tests").rglob("*.py")
                   if "OPUS-FILLS" in p.read_text()]
    g.check("no OPUS-FILLS skip markers left in tests/", not marker_hits, "; ".join(marker_hits[:5]))

    # 2. Demo: deterministic, ends with the exact verification line.
    code, out, err = run([sys.executable, "-m", "reasoning_graph.demo"], cwd=REPO)
    lines = out.strip().splitlines()
    g.check("demo exits 0 and ends 'Verify your build: ok'",
            code == 0 and lines and lines[-1] == "Verify your build: ok",
            (out + err)[-200:])

    # 3. INVARIANTS.md ↔ tests, 1:1 both directions.
    inv_text = (REPO / "tests" / "INVARIANTS.md").read_text()
    inv_tests = re.findall(r"`(tests/[\w/]+\.py::\w+)`", inv_text)
    code, out, err = run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=REPO)
    collected = out
    missing = [t for t in inv_tests if t.replace("tests/", "").replace(".py::", ".py::") .split("::")[1] not in collected]
    g.check(f"every INVARIANTS line names a collected test ({len(inv_tests)} lines)",
            not missing, "; ".join(missing[:4]))
    inv_named = re.findall(r"::(test_inv_\w+)", " ".join(inv_tests))
    stray = [m for m in re.findall(r"(test_inv_\w+)", collected) if m not in inv_named]
    g.check("every test_inv_* test appears in INVARIANTS.md", not stray, "; ".join(stray[:4]))

    # 4. numpy byte-identical: pagerank on the tiny fixture with numpy present vs
    #    hidden (shim package raising ImportError), stdout compared byte-for-byte.
    tmp = Path(tempfile.mkdtemp(prefix="g8-"))
    try:
        shutil.copytree(REPO / "tests" / "fixtures" / "tiny", tmp / "tiny")
        shutil.copy(REPO / "tests" / "fixtures" / "fcl-fixture.ngf.md", tmp / "fcl-fixture.ngf.md")
        run([sys.executable, str(tmp / "tiny" / "build_tiny.py"), str(tmp / "tiny")])
        shim = tmp / "shim" / "numpy"
        shim.mkdir(parents=True)
        (shim / "__init__.py").write_text("raise ImportError('numpy hidden by G8 shim')\n")
        argv = [sys.executable, "-m", "reasoning_graph.cli", "analytics", "pagerank",
                "--instance", str(tmp / "tiny" / "instance.json"), "--top", "10", "--json"]
        r_with = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
        import os
        env = dict(os.environ, PYTHONPATH=str(tmp / "shim"))
        r_without = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, env=env)
        g.check("pagerank runs (numpy present)", r_with.returncode == 0,
                r_with.stderr[-200:] if r_with.returncode else "")
        g.check("pagerank output byte-identical with numpy hidden",
                r_without.returncode == 0 and r_with.stdout == r_without.stdout,
                "outputs differ" if r_with.stdout != r_without.stdout else r_without.stderr[-200:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 5. Docs at the house bar: markers gone, required sections present.
    md_files = [REPO / f for f in DOC_FILES] + sorted((REPO / "docs").glob("*.md")) \
        + [REPO / "HOW-TO-USE.md"]
    marker_hits = sorted({str(p.relative_to(REPO)) for p in md_files
                          if p.is_file() and "OPUS-FILLS" in p.read_text()})
    g.check("no OPUS-FILLS markers left in any doc", not marker_hits, "; ".join(marker_hits[:6]))
    for fname, sections in REQUIRED_SECTIONS.items():
        text = (REPO / fname).read_text()
        absent = [s for s in sections if s not in text]
        g.check(f"{fname} required sections", not absent, "; ".join(absent))
    n_docs = len(list((REPO / "docs").glob("*.md")))
    g.check("docs/00..10 all present (11 chapters)", n_docs == 11, f"found {n_docs}")

    # 6. README quickstart EXECUTES: first fenced bash block, bash -euo pipefail.
    readme = (REPO / "README.md").read_text()
    m = re.search(r"```bash\n(.*?)```", readme, flags=re.S)
    if g.check("README has a fenced bash quickstart", bool(m)):
        script = "set -euo pipefail\n" + m.group(1)
        code, out, err = run(["bash", "-c", script], cwd=REPO, timeout=900)
        g.check("quickstart block executes (exit 0)", code == 0, (out + err)[-300:])

    # 7. CHANGELOG hardening pass with RG-n issue ids (house pattern DC-1/DC-2)
    #    — and every RG-n must be backed by a real git commit (council
    #    2026-07-20: a regex on prose can't tell a real fix from narration;
    #    a diff trail can).
    ch = (REPO / "CHANGELOG.md").read_text()
    rg_ids = sorted(set(re.findall(r"\bRG-\d+\b", ch)))
    g.check("CHANGELOG hardening pass with RG-<n> issue ids",
            re.search(r"hardening", ch, flags=re.I) is not None and len(rg_ids) >= 1)
    gitlog = subprocess.run(["git", "log", "--oneline", "--all"], cwd=REPO,
                            capture_output=True, text=True)
    unbacked = [i for i in rg_ids if i not in gitlog.stdout]
    g.check("every RG-<n> id appears in a git commit message (diff-backed, not narrated)",
            gitlog.returncode == 0 and not unbacked, "; ".join(unbacked[:5]))

    # 8. Self-verifying examples.
    for ex in ["examples/01_hello_traversal.py"]:
        code, out, err = run([sys.executable, str(REPO / ex)], cwd=REPO)
        g.check(f"{ex} self-verifies", code == 0 and "Verify your build: ok" in out,
                (out + err)[-200:])
    return g.finish()


if __name__ == "__main__":
    sys.exit(main())
