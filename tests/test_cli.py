"""CLI — --json on every subcommand; exit-code contract (0 ok / 1 error)."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
I0 = REPO / "instances" / "claude_code_tools" / "instance.json"


def _run(*args):
    return subprocess.run([sys.executable, "-m", "reasoning_graph.cli", *args],
                          cwd=REPO, capture_output=True, text=True)


def test_every_subcommand_supports_json(tiny_instance):
    import json
    for args in (["schema", "validate", "--instance", str(I0)],
                 ["schema", "integrity", "--instance", str(tiny_instance)],
                 ["resolve", "--instance", str(tiny_instance), "--start", "loom_1", "--end", "dye_bath_2"],
                 ["analytics", "cycles", "--instance", str(tiny_instance)],
                 ["loop", "scan", "--instance", str(I0)],
                 ["measure", "frontier-rate", "--instance", str(I0)],
                 ["observe", "--instance", str(tiny_instance), "--query", "q",
                  "--resolution-status", "REFUSE", "--outcome", "gap",
                  "--event-id", "cli-event"]):
        cp = _run(*args, "--json")
        assert cp.returncode == 0, cp.stderr
        json.loads(cp.stdout)                      # valid JSON


def test_exit_codes_0_1_3_contract(tiny_instance):
    # 0 = success (incl. REFUSE — a result, not an error)
    ok = _run("resolve", "--instance", str(tiny_instance), "--start", "loom_1", "--end", "dye_bath_3", "--json")
    assert ok.returncode == 0
    # 1 = error (missing instance file)
    err = _run("schema", "validate", "--instance", "/no/such/instance.json", "--json")
    assert err.returncode == 1


def test_memory_cli_review_and_explicit_approval(tiny_instance):
    import json
    proposed = _run("memory", "propose", "--instance", str(tiny_instance), "--kind", "decision",
                    "--content", "stay local", "--agreement", "user agreed", "--memory-id", "cli-memory", "--json")
    assert proposed.returncode == 0
    review = _run("memory", "review", "--instance", str(tiny_instance), "--json")
    assert json.loads(review.stdout)["review"][0]["memory_id"] == "cli-memory"
    denied = _run("memory", "approve", "--instance", str(tiny_instance), "--memory-id", "cli-memory", "--json")
    assert denied.returncode == 1
    approved = _run("memory", "approve", "--instance", str(tiny_instance), "--memory-id", "cli-memory", "--approve", "--json")
    assert approved.returncode == 0
