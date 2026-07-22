#!/usr/bin/env python3
"""Stdlib-only MCP server exposing reasoning-graph over stdio (house pattern).
Three read-only tools — resolve, loop_scan, frontier_rate — each a thin shell to
the reasoning-graph CLI with --json. Zero third-party deps. See docs/10.

Run:  python3 examples/mcp_server.py --instance <instance.json>
(reads JSON-RPC on stdin, writes JSON-RPC on stdout).
"""
import json
import subprocess
import sys

TOOLS = {
    "resolve": ["resolve"], "loop_scan": ["loop", "scan"],
    "frontier_rate": ["measure", "frontier-rate"],
}


def _call(name, instance, args):
    argv = ["reasoning-graph", *TOOLS[name], "--instance", instance, "--json"]
    for k, v in (args or {}).items():
        argv += [f"--{k}", str(v)]
    cp = subprocess.run(argv, capture_output=True, text=True)
    return json.loads(cp.stdout) if cp.returncode == 0 else {"error": cp.stderr}


def main():
    instance = sys.argv[sys.argv.index("--instance") + 1] if "--instance" in sys.argv else None
    for line in sys.stdin:
        req = json.loads(line)
        if req.get("method") == "tools/list":
            out = {"tools": [{"name": n} for n in TOOLS]}
        elif req.get("method") == "tools/call":
            p = req.get("params", {})
            out = _call(p["name"], instance, p.get("arguments"))
        else:
            out = {"error": "unknown method"}
        sys.stdout.write(json.dumps({"id": req.get("id"), "result": out}) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
