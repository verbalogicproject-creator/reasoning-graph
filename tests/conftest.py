"""Shared fixtures. The tiny instance is ALWAYS copied to a temp dir and built
there — tests never touch the checked-in fixtures directory or any real DB."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def tiny_instance(tmp_path):
    """Copy tiny/ to tmp, build tiny.db there, return the instance.json path."""
    dest = tmp_path / "tiny"
    shutil.copytree(FIXTURES / "tiny", dest)
    shutil.copy(FIXTURES / "fcl-fixture.ngf.md", tmp_path / "fcl-fixture.ngf.md")
    subprocess.run([sys.executable, str(dest / "build_tiny.py"), str(dest)],
                   check=True, capture_output=True)
    return dest / "instance.json"


@pytest.fixture()
def tiny_instance_bare(tmp_path):
    """Same, but the unmigrated (--bare) variant for m001 tests."""
    dest = tmp_path / "tiny"
    shutil.copytree(FIXTURES / "tiny", dest)
    shutil.copy(FIXTURES / "fcl-fixture.ngf.md", tmp_path / "fcl-fixture.ngf.md")
    subprocess.run([sys.executable, str(dest / "build_tiny.py"), str(dest), "--bare"],
                   check=True, capture_output=True)
    return dest / "instance.json"
