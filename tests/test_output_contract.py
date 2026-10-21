"""Golden output contract: services keep the documented JSON wire shape.

Fully mocked with respx — no network. These tests freeze the current output
contract (keys, detail_url format, error shape) so the core/adapters refactor
cannot silently change what MCP clients and CLI scripts consume.
"""

import json
from datetime import datetime

import pytest
import respx
from httpx import Response

from maitabi_mcp_server.models import (
    GetBusTourDetailInput,
    SearchBusToursInput,
    SearchGeneralToursInput,
)
from maitabi_mcp_server.services.bus_service import (
    get_tour_detail_service,
    search_tours_service,
)
from maitabi_mcp_server.services.general_service import (
    RATE_LIMIT_ERROR,
    search_general_tours_service,
)

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


def _load(raw: str) -> dict:
    return json.loads(raw)


@respx.mock
@pytest.mark.asyncio
async def test_search_tours_golden_shape_and_detail_url():
    respx.get("https://api.bus.maitabi.jp/tour_search").mock(
        return_value=Response(200, json={"count": "2", "page": "1", "tour": [dict(BUS_TOUR_ITEM)], "param": {}})
    )
    out = _load(await search_tours_service(SearchBusToursInput(month=9, day=12)))

    assert set(out) >= {"count", "page", "tour", "param"}
    item = out["tour"][0]
    # every original upstream field survives
    for key, value in BUS_TOUR_ITEM.items():
        assert item[key] == value
    # detail_url derived from the date field
    assert item["detail_url"] == (
        "https://bus.maitabi.jp/detail.html?course_no=14241&year=2026&month=9"
    )
    # output is valid UTF-8 JSON with unescaped Japanese
    assert "立山" in json.dumps(out, ensure_ascii=False)


@respx.mock
@pytest.mark.asyncio
async def test_search_tours_price_and_availability_filters():
    tours = [
        dict(BUS_TOUR_ITEM, course_no=1, price="9,000円"),
        dict(BUS_TOUR_ITEM, course_no=2, price="15,500円～"),
        dict(BUS_TOUR_ITEM, course_no=3, price="30,000円"),
        dict(BUS_TOUR_ITEM, course_no=4, price="15,500円", status="満席"),
    ]
    respx.get("https://api.bus.maitabi.jp/tour_search").mock(
        return_value=Response(200, json={"count": "4", "page": "1", "tour": tours, "param": {}})
    )
    out = _load(
        await search_tours_service(
            SearchBusToursInput(
                month=9, min_price=10000, max_price=20000, require_available_seats=True
            )
        )
    )
    # 9,000円 under min; 30,000円 over max; 満席 dropped; 15,500円～ (strip ～) kept
    assert [t["course_no"] for t in out["tour"]] == [2]


@respx.mock
@pytest.mark.asyncio
async def test_search_tours_multi_day_fans_out_and_merges():
    route = respx.get("https://api.bus.maitabi.jp/tour_search")
    route.mock(
        side_effect=[
            Response(200, json={"tour": [dict(BUS_TOUR_ITEM, course_no=11)]}),
            Response(200, json={"tour": [dict(BUS_TOUR_ITEM, course_no=12)]}),
        ]
    )
    out = _load(await search_tours_service(SearchBusToursInput(month=9, day="14-15")))
    assert [t["course_no"] for t in out["tour"]] == [11, 12]
    assert route.call_count == 2


@respx.mock
@pytest.mark.asyncio
async def test_get_tour_detail_batch_wraps_in_tours_list():
    route = respx.get("https://api.bus.maitabi.jp/tour_detail")
    route.mock(
        side_effect=[
            Response(200, json={"course_no": 14241, "title": "A"}),
            Response(200, json={"course_no": 8518, "title": "B"}),
        ]
    )
    out = _load(await get_tour_detail_service(GetBusTourDetailInput(course_no=[14241, 8518])))
    assert [t["course_no"] for t in out["tours"]] == [14241, 8518]


@respx.mock
@pytest.mark.asyncio
async def test_general_search_detail_url_and_statuses():
    respx.get("https://www.maitabi.jp/api/v1/category_search").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {"courseNo": 1723, "price": "30,000円", "saikouStatus": "受付中"},
                    {"courseNo": 24865, "price": "99,000円", "saikouStatus": "キャンセル待ち"},
                ]
            },
        )
    )
    out = _load(await search_general_tours_service(SearchGeneralToursInput(require_available_seats=True)))
    assert [d["courseNo"] for d in out["data"]] == [1723]
    assert out["data"][0]["detail_url"] == "https://www.maitabi.jp/detail.php?courseNo=1723"


@respx.mock
@pytest.mark.asyncio
async def test_general_search_rate_limit_error_shape():
    respx.get("https://www.maitabi.jp/api/v1/category_search").mock(
        return_value=Response(200, json={"errors": {"code": 0, "message": "Too Many Attempts."}})
    )
    out = _load(await search_general_tours_service(SearchGeneralToursInput()))
    assert out["error"] == RATE_LIMIT_ERROR
    assert out["retry_hint"] == "wait ~60s and retry manually"


@respx.mock
@pytest.mark.asyncio
async def test_upstream_500_is_clear_error_not_exception():
    respx.get("https://api.bus.maitabi.jp/tour_search").mock(
        return_value=Response(500, text="oops")
    )
    out = _load(await search_tours_service(SearchBusToursInput(month=9)))
    assert out["error"] == "Upstream service returned error: 500"
    assert "detail" in out
