"""MCP wire-schema snapshot: tools/list must not drift unnoticed.

Captured from the pre-refactor hand-written tools; Phase 2 regenerates tool
signatures from `core/inputs.py` and must reproduce this byte-for-byte
(keys sorted, so property order is semantically normalized).
"""

import asyncio
import json
from pathlib import Path

from maitabi.mcp.server import mcp

FIXTURE = Path(__file__).parent / "fixtures" / "mcp_schema.json"


def _live_schema() -> dict:
    async def collect():
        tools = await mcp.list_tools()
        return {
            t.name: {
                "description": t.description,
                "parameters": json.loads(json.dumps(t.parameters, sort_keys=True)),
            }
            for t in tools
        }

    return asyncio.run(collect())


def test_mcp_schema_matches_snapshot():
    live = _live_schema()
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert sorted(live) == sorted(expected), f"tool set changed: {sorted(set(live) ^ set(expected))}"
    for name, exp in sorted(expected.items()):
        assert live[name]["parameters"] == exp["parameters"], f"schema drift in {name}"
        assert live[name]["description"] == exp["description"], f"doc drift in {name}"
