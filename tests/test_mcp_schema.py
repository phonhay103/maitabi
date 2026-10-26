"""MCP wire-schema snapshot: tools/list must not drift unnoticed.

Captured from the pre-refactor hand-written tools; Phase 2 regenerates tool
signatures from `core/inputs.py` and must reproduce this byte-for-byte
(keys sorted, so property order is semantically normalized).

Title, annotations and outputSchema are frozen here too: they are what lets a
client auto-approve a read, label the tool with its service, and read
`structuredContent` without reparsing the text block, so a silent change is a
contract change just like a parameter rename.
"""

import asyncio
import json
from pathlib import Path

from maitabi.mcp.server import mcp

FIXTURE = Path(__file__).parent / "fixtures" / "mcp_schema.json"


def _normalized(value):
    return json.loads(json.dumps(value, sort_keys=True))


def live_schema() -> dict:
    async def collect():
        tools = await mcp.list_tools()
        return {
            t.name: {
                "title": t.title,
                "description": t.description,
                "parameters": _normalized(t.parameters),
                "output_schema": _normalized(t.output_schema),
                "annotations": _normalized(t.annotations.model_dump(exclude_none=True)) if t.annotations else None,
            }
            for t in tools
        }

    return asyncio.run(collect())


def test_mcp_schema_matches_snapshot():
    live = live_schema()
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert sorted(live) == sorted(expected), f"tool set changed: {sorted(set(live) ^ set(expected))}"
    for name, exp in sorted(expected.items()):
        for field in ("title", "annotations", "output_schema", "parameters"):
            assert live[name][field] == exp[field], f"{field} drift in {name}"
        assert live[name]["description"] == exp["description"], f"doc drift in {name}"
