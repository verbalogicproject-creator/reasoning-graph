from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import anyio
import pytest

pytest.importorskip("mcp")
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = Path(__file__).resolve().parents[1]

def _sdk_field(value, snake, camel):
    return getattr(value, snake) if hasattr(value, snake) else getattr(value, camel)



def test_official_sdk_initialize_list_and_call(tiny_instance):
    db = tiny_instance.parent / "tiny.db"
    before = hashlib.sha256(db.read_bytes()).hexdigest()

    async def exercise():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "reasoning_graph.mcp_server", "--instance", str(tiny_instance)],
            cwd=str(REPO),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                assert _sdk_field(initialized, "server_info", "serverInfo").name == "reasoning-graph"
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                assert {"resolve", "loop_scan", "frontier_rate", "record_observation", "memory_list", "memory_review", "memory_propose"} <= names
                assert not {"memory_approve", "memory_activate"} & names
                answer = await session.call_tool(
                    "resolve", {"start": "loom_1", "end": "dye_bath_2"})
                assert not _sdk_field(answer, "is_error", "isError")
                assert _sdk_field(answer, "structured_content", "structuredContent")["status"] == "ANSWER"
                observation = await session.call_tool(
                    "record_observation",
                    {"event_id": "mcp-event", "query": "q",
                     "resolution_status": "ANSWER", "outcome": "success"})
                assert not _sdk_field(observation, "is_error", "isError")
                assert _sdk_field(
                    observation, "structured_content", "structuredContent")["event_id"] == "mcp-event"
                proposed = await session.call_tool(
                    "memory_propose", {"kind": "preference", "content": "use local mode",
                                        "agreement": "user agreed", "memory_id": "mcp-memory"})
                assert not _sdk_field(proposed, "is_error", "isError")
                listed = await session.call_tool("memory_list", {})
                assert _sdk_field(listed, "structured_content", "structuredContent")["memories"][0]["status"] == "reviewable"

    anyio.run(exercise)
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before
