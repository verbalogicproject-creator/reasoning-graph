# 10 — Claude Code + MCP

`examples/mcp_server.py` is a stdlib-only, zero-dependency MCP server exposing three read-only tools — `resolve`, `loop_scan`, `frontier_rate` — each a thin shell to the `reasoning-graph` CLI with `--json`. It reads JSON-RPC on stdin and writes it on stdout:

```bash
python3 examples/mcp_server.py --instance instances/claude_code_tools/instance.json
```

Point a Claude Code session at it to look up reasoning by traversal instead of re-deriving it. The server is read-only by design; the loop's write path (mint/verify/freeze) stays local CLI/files (SoT lock #8). A future PostToolUse hook may auto-append REFUSE-drafted frontier-call-log stubs (transcription only — `gap_shape` stays human; SoT lock #26, on the ROADMAP).
