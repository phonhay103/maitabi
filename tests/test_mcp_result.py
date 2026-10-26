"""MCP result surface: one payload, three representations.

Every tool call must satisfy all of these at once:

- the text block is the same JSON the CLI prints (byte-identical serialization),
- `structuredContent` is that payload already parsed, so clients never reparse,
- `isError` is true exactly when the payload is the shared error shape.

Upstream failures are never exceptions (`services/http.py` normalizes them), so
without the `isError` mapping a rate-limited or 4xx call would look successful
to the model. Batch detail is the deliberate exception: a partial failure is
data inside a successful envelope.
"""

import json

import pytest
import respx
from httpx import Response

from maitabi.core.errors import RATE_LIMIT_ERROR
from maitabi.mcp.server import mcp

BUS_TOUR_ITEM = {
    "travel_type": 3,
    "course_cd": "S104C21",
    "course_no": 14241,
    "date": "2026年09月12日(土)",
    "title": "立山室堂ライン往復ツアー",
    "tour_day": "1日",
    "price": "15,500円",
    "status": "受付中",
    "phone_reserve": 0,
}

SEARCH_URL = "https://api.bus.maitabi.jp/tour_search"
DETAIL_URL = "https://api.bus.maitabi.jp/tour_detail"


def _text(result) -> str:
    return result.content[0].text


@respx.mock
@pytest.mark.asyncio
async def test_success_carries_structured_content_equal_to_the_text_block():
    respx.get(SEARCH_URL).mock(
        return_value=Response(200, json={"count": "1", "page": "1", "tour": [dict(BUS_TOUR_ITEM)]})
    )

    result = await mcp.call_tool("bus_search_tours", {"month": 9, "day": 12})

    assert result.is_error is False
    assert json.loads(_text(result)) == result.structured_content
    assert set(result.structured_content) == {"count", "page", "items", "query"}
    # the serialization is the public one: unescaped Japanese, 2-space indent
    assert "立山" in _text(result)
    assert _text(result).startswith('{\n  "count"')
    assert result.structured_content["items"][0]["detail_url"].startswith("https://bus.maitabi.jp/detail.html")


@respx.mock
@pytest.mark.asyncio
async def test_upstream_4xx_sets_is_error_and_hints_at_the_inputs():
    respx.get(SEARCH_URL).mock(return_value=Response(400, text="bad request"))

    result = await mcp.call_tool("bus_search_tours", {"month": 9})

    assert result.is_error is True
    assert result.structured_content["error"] == "Upstream service returned error: 400"
    assert "check the filter values" in result.structured_content["retry_hint"]
    # the human-readable message reaches the model even on a failed call
    assert "Upstream service returned error: 400" in _text(result)


@respx.mock
@pytest.mark.asyncio
async def test_upstream_5xx_sets_is_error_without_blaming_the_inputs():
    respx.get(SEARCH_URL).mock(return_value=Response(500, text="oops"))

    result = await mcp.call_tool("bus_search_tours", {"month": 9})

    assert result.is_error is True
    assert "retry_hint" not in result.structured_content


@respx.mock
@pytest.mark.asyncio
async def test_rate_limit_sets_is_error_and_keeps_the_retry_hint():
    respx.get("https://www.maitabi.jp/api/v1/category_search").mock(
        return_value=Response(200, json={"errors": {"code": 0, "message": "Too Many Attempts."}})
    )

    result = await mcp.call_tool("general_search_tours", {})

    assert result.is_error is True
    assert result.structured_content["error"] == RATE_LIMIT_ERROR
    assert result.structured_content["retry_hint"] == "wait ~60s and retry manually"


@respx.mock
@pytest.mark.asyncio
async def test_batch_detail_partial_failure_stays_a_successful_envelope():
    def per_course(request):
        course_no = request.url.params["course_no"]
        if course_no == "1":
            return Response(200, json={"course_no": 1, "title": "ok"})
        return Response(500, text="boom")

    respx.get(DETAIL_URL).mock(side_effect=per_course)

    result = await mcp.call_tool("bus_get_tour_detail", {"course_no": [1, 2]})

    assert result.is_error is False
    items = result.structured_content["items"]
    assert items[0] == {"course_no": 1, "title": "ok"}
    assert items[1]["error"] == "Upstream service returned error: 500"


def test_every_tool_is_annotated_read_only_and_titled():
    """Annotations and titles are the client-side half of the contract."""
    import asyncio

    tools = asyncio.run(mcp.list_tools())

    assert len(tools) == 8
    for tool in tools:
        assert tool.title and tool.title.startswith("Maitabi: ")
        assert tool.annotations is not None
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.destructiveHint is False
        assert tool.annotations.idempotentHint is True
        assert tool.annotations.openWorldHint is True
        assert tool.output_schema == {"type": "object", "additionalProperties": True}
