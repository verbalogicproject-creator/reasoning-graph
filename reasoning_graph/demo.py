"""Deterministic demo. OPUS-FILLS (Phase 7). Contract (gate G8):

`python3 -m reasoning_graph.demo` builds the tiny fixture in a temp dir
(tests/fixtures/tiny/build_tiny.py), runs: schema validate → migrate → three
resolve calls (one ANSWER with a real multi-hop confidence product, one
WEAK_ANSWER below floor, one REFUSE(contradiction)) → a full fixture loop pass
(scan→promote→mint→verify→freeze on the fcl fixture) — printing each step's
one-line result, fully deterministic (no wall-clock, no RNG, no network), and
MUST end with exactly:

Verify your build: ok
"""
from __future__ import annotations

import sys


def main() -> int:
    print("NOT-IMPLEMENTED: demo — OPUS-FILLS in Phase 7; see module docstring + SoT")
    return 3


if __name__ == "__main__":
    sys.exit(main())
