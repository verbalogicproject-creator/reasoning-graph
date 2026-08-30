from __future__ import annotations

import sys
from pathlib import Path

import anyio
import pytest

pytest.importorskip("mcp")
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = Path(__file__).resolve().parents[1]
COMPAT = REPO / "instances" / "claude_code_tools" / "instance.json"


def _field(value, snake, camel):
    return getattr(value, snake) if hasattr(value, snake) else getattr(value, camel)


def test_bundled_compatibility_descriptor_mcp_smoke():
    async def exercise():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "reasoning_graph.mcp_server", "--instance", str(COMPAT)],
            cwd=str(REPO),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                assert _field(initialized, "server_info", "serverInfo").name == "reasoning-graph"
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                assert {"resolve", "loop_scan", "frontier_rate", "record_observation",
                        "memory_list", "memory_review", "memory_propose"} <= names
                assert not {"memory_approve", "memory_activate"} & names
                result = await session.call_tool(
                    "resolve",
                    {"start": "dep_003_tool_execution_requires_error_handling",
                     "end": "constr_002_max_iterations_safety"},
                )
                assert not _field(result, "is_error", "isError")
                answer = _field(result, "structured_content", "structuredContent")
                assert answer["status"] == "ANSWER"
                assert abs(answer["confidence"] - 0.9118) < 1e-12

    anyio.run(exercise)
