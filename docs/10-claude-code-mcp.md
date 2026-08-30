# 10 — Claude Code + MCP

The MCP integration uses the official Python SDK v2 and structured tool schemas.
Install the optional integration:

```sh
python3 -m pip install -e '.[mcp]'
```

Run one instance over stdio:

```sh
reasoning-graph-mcp --instance instances/claude_code_tools/instance.json
# equivalent:
python3 examples/mcp_server.py --instance instances/claude_code_tools/instance.json
```

This bundled descriptor is canonical and self-contained. Its relative paths
resolve the clean database, log, observations, rules, and adapter from any
fresh clone.

Tools:

- `resolve`: deterministic `ANSWER`, `WEAK_ANSWER`, or `REFUSE` with typed path confidence, support class, and provenance.
- `loop_scan`: read the declared frontier-call log.
- `frontier_rate`: compute gap-class recurrence from the log.
- `record_observation`: append a bounded success, failure, contradiction, or gap event to the instance's JSONL observation ledger.
- `memory_list`: read the compact governed MemoryLog state.
- `memory_review`: open review candidates without writing.
- `memory_propose`: propose typed content; approval is intentionally unavailable.

`record_observation` is deliberately not a graph writer. MCP cannot mint,
freeze, activate, retire, or approve memory. Promotion, graph lifecycle
changes, and memory activation stay behind local verification and explicit
human approval.

An instance may set `observations_path` in `instance.json`; otherwise the
ledger is `observations.jsonl` beside that descriptor. Event IDs are unique,
details are JSON and limited to 16 KiB, and optional event times must be
timezone-aware ISO-8601.

The package declares `mcp>=2,<3`. Protocol tests launch the server via stdio
and use the SDK's `ClientSession` for initialization, discovery, and calls.
