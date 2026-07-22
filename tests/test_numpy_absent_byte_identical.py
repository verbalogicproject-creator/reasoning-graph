"""Invariant 10 — pagerank output byte-identical with numpy present vs hidden."""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_inv_byte_identical(tiny_instance):
    argv = [sys.executable, "-m", "reasoning_graph.cli", "analytics", "pagerank",
            "--instance", str(tiny_instance), "--top", "10", "--json"]
    with_np = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
    shim = Path(tempfile.mkdtemp()) / "numpy"
    shim.mkdir()
    (shim / "__init__.py").write_text("raise ImportError('numpy hidden')\n")
    env = dict(os.environ, PYTHONPATH=str(shim.parent))
    without_np = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, env=env)
    assert with_np.returncode == 0 and without_np.returncode == 0
    assert with_np.stdout == without_np.stdout
