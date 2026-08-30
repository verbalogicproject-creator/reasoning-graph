"""Official MCP SDK integration for a bound reasoning-graph instance."""
from __future__ import annotations

import argparse
from typing import Any

from .schema import load_instance


def create_server(instance_path: str):
    """Build an instance-bound MCP SDK v2 server with structured tool schemas."""
    try:
        from mcp.server.mcpserver import MCPServer
    except ImportError as exc:
        try:  # 1.28 compatibility; package installs target v2.
            from mcp.server.fastmcp import FastMCP as MCPServer
        except ImportError:
            raise RuntimeError(
                "MCP support requires: pip install 'reasoning-graph[mcp]'") from exc

    instance = load_instance(instance_path)
    server = MCPServer(
        "reasoning-graph",
        instructions=(
            "Retrieve governed reasoning paths, record observations, and propose MemoryLog entries. "
            "MCP cannot approve, activate, freeze, retire, or alter graph rules."
        ),
    )

    @server.tool(description="Resolve a typed graph path or natural-language query.",
                 structured_output=True)
    def resolve(
        start: str | None = None,
        end: str | None = None,
        text: str | None = None,
        weighted: bool = True,
        include_dormant: bool = False,
        hard: bool = False,
    ) -> dict[str, Any]:
        from .resolver import resolve as resolve_graph
        return resolve_graph(instance, start=start, end=end, text=text, weighted=weighted,
                             include_dormant=include_dormant, hard=hard)

    @server.tool(description="Read the frontier-call log without changing graph state.",
                 structured_output=True)
    def loop_scan() -> dict[str, Any]:
        from .loop.fcl import parse_log
        return {"entries": parse_log(instance)}

    @server.tool(description="Measure the current unsupported-query frontier rate.",
                 structured_output=True)
    def frontier_rate() -> dict[str, Any]:
        from .measure.frontier_rate import compute
        return compute(instance)

    @server.tool(
        description=(
            "Append a success, failure, contradiction, or gap observation. "
            "This tool cannot activate, freeze, retire, or modify graph rules."
        ),
        structured_output=True,
    )
    def record_observation(
        query: str,
        resolution_status: str,
        outcome: str,
        event_id: str | None = None,
        event_time: str | None = None,
        path_signature: str | None = None,
        source_ref: str | None = None,
        gap_classification: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from .observations import record_observation as append
        return append(
            instance, query=query, resolution_status=resolution_status, outcome=outcome,
            event_id=event_id, event_time=event_time, path_signature=path_signature,
            source_ref=source_ref, gap_classification=gap_classification, details=details)

    @server.tool(description="Read the compact governed MemoryLog snapshot.", structured_output=True)
    def memory_list() -> dict[str, Any]:
        from .memory import snapshot
        return snapshot(instance)

    @server.tool(description="Open MemoryLog review candidates without writing any event.", structured_output=True)
    def memory_review() -> dict[str, Any]:
        from .memory import review
        return review(instance)

    @server.tool(description="Propose typed MemoryLog content; it cannot approve or activate memory.", structured_output=True)
    def memory_propose(kind: str, content: str, evidence: Any = None, validation: str | None = None,
                       agent_acknowledged: bool = False, agreement: str | None = None,
                       conflicts_with: list[str] | None = None, memory_id: str | None = None,
                       event_id: str | None = None) -> dict[str, Any]:
        from .memory import propose
        return propose(instance, kind=kind, content=content, evidence=evidence, validation=validation,
                       agent_acknowledged=agent_acknowledged, agreement=agreement,
                       conflicts_with=conflicts_with, memory_id=memory_id, event_id=event_id)

    return server


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Serve one reasoning-graph instance over MCP.")
    parser.add_argument("--instance", required=True, help="path to instance.json")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"],
                        default="stdio")
    args = parser.parse_args(argv)
    create_server(args.instance).run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
