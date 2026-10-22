"""Golden output contract: the documented JSON wire shape.

Fully mocked with respx — no network. These tests freeze what MCP clients and
CLI scripts consume: the envelope keys, the per-item core keys, the
`detail_url` formats, and the error shape.
"""

import json

import pytest
import respx
from httpx import Response

from maitabi.core.errors import RATE_LIMIT_ERROR
from maitabi.core.inputs import (
    GetBusTourDetailInput,
    SearchBusToursInput,
    SearchGeneralToursInput,
)
from maitabi.services.bus import (
    get_tour_detail_service,
    search_tours_service,
)
from maitabi.services.general import (
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

ENVELOPE_KEYS = {"count", "page", "items", "query"}


def _load(result) -> dict:
    """Services return dicts; tolerate JSON strings too (legacy shape)."""
    return json.loads(result) if isinstance(result, str) else result


@respx.mock
@pytest.mark.asyncio
async def test_search_tours_golden_shape_and_detail_url():
    respx.get("https://api.bus.maitabi.jp/tour_search").mock(
        return_value=Response(200, json={"count": "2", "page": "1", "tour": [dict(BUS_TOUR_ITEM)], "param": {}})
    )
    out = _load(await search_tours_service(SearchBusToursInput(month=9, day=12)))

    assert set(out) == ENVELOPE_KEYS
    assert out["count"] == 2  # upstream "2" → int
    assert out["page"] == 1
    assert out["query"]["month"] == 9
    assert out["query"]["day"] == [12]

    item = out["items"][0]
    # every original upstream field survives
    for key, value in BUS_TOUR_ITEM.items():
        assert item[key] == value
    # detail_url derived from the date field
    assert item["detail_url"] == ("https://bus.maitabi.jp/detail.html?course_no=14241&year=2026&month=9")
    # output is valid UTF-8 JSON with unescaped Japanese
    assert "立山" in json.dumps(out, ensure_ascii=False)


@respx.mock
@pytest.mark.asyncio
async def test_search_tours_price_and_availability_filters():
    tours = [
        dict(BUS_TOUR_ITEM, course_no=1, price="9,000円"),
        dict(BUS_TOUR_ITEM, course_no=2, price="15,500円\uff5e"),
        dict(BUS_TOUR_ITEM, course_no=3, price="30,000円"),
        dict(BUS_TOUR_ITEM, course_no=4, price="15,500円", status="満席"),
    ]
    respx.get("https://api.bus.maitabi.jp/tour_search").mock(
        return_value=Response(200, json={"count": "4", "page": "1", "tour": tours, "param": {}})
    )
    out = _load(
        await search_tours_service(
            SearchBusToursInput(month=9, min_price=10000, max_price=20000, require_available_seats=True)
        )
    )
    # 9,000円 under min; 30,000円 over max; 満席 dropped; 15,500円\uff5e (tilde stripped) kept
    assert [t["course_no"] for t in out["items"]] == [2]
    # count is the upstream total for the query, before client-side post-filters
    assert out["count"] == 4


@respx.mock
@pytest.mark.asyncio
async def test_search_tours_multi_day_fans_out_and_merges():
    route = respx.get("https://api.bus.maitabi.jp/tour_search")
    route.mock(
        side_effect=[
            Response(200, json={"count": "1", "tour": [dict(BUS_TOUR_ITEM, course_no=11)]}),
            Response(200, json={"count": "2", "tour": [dict(BUS_TOUR_ITEM, course_no=12)]}),
        ]
    )
    out = _load(await search_tours_service(SearchBusToursInput(month=9, day="14-15")))
    assert [t["course_no"] for t in out["items"]] == [11, 12]
    assert out["count"] == 3  # sum of the per-day totals
    assert route.call_count == 2


@respx.mock
@pytest.mark.asyncio
async def test_search_tours_multi_day_unknown_count_stays_null():
    route = respx.get("https://api.bus.maitabi.jp/tour_search")
    route.mock(
        side_effect=[
            Response(200, json={"tour": [dict(BUS_TOUR_ITEM, course_no=11)]}),
            Response(200, json={"tour": [dict(BUS_TOUR_ITEM, course_no=12)]}),
        ]
    )
    out = _load(await search_tours_service(SearchBusToursInput(month=9, day="14-15")))
    # Upstream did not report a total: null, never len(items).
    assert out["count"] is None


@respx.mock
@pytest.mark.asyncio
async def test_get_tour_detail_batch_returns_envelope():
    route = respx.get("https://api.bus.maitabi.jp/tour_detail")
    route.mock(
        side_effect=[
            Response(200, json={"course_no": 14241, "title": "A"}),
            Response(200, json={"course_no": 8518, "title": "B"}),
        ]
    )
    out = _load(await get_tour_detail_service(GetBusTourDetailInput(course_no=[14241, 8518])))
    assert set(out) == ENVELOPE_KEYS
    assert out["page"] is None
    assert [t["course_no"] for t in out["items"]] == [14241, 8518]


@respx.mock
@pytest.mark.asyncio
async def test_general_search_envelope_and_item_normalisation():
    respx.get("https://www.maitabi.jp/api/v1/category_search").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {
                        "courseNo": 1723,
                        "saikouDate": "2026-11-01",
                        "yoyakuStatus": 1,
                        "roomPriceMin": 30000,
                        "tTravel": {"courseName": "富士山", "courseCd": "M1", "priceMin": 30000},
                    },
                    {
                        "courseNo": 24865,
                        "saikouDate": "2026-11-02",
                        "yoyakuStatus": 3,  # closed
                        "roomPriceMin": 99000,
                        "tTravel": {"courseName": "槍ヶ岳", "courseCd": "M2", "priceMin": 99000},
                    },
                ],
                "meta": {"paging": {"page": 1, "total": 45}},
            },
        )
    )
    out = _load(await search_general_tours_service(SearchGeneralToursInput(require_available_seats=True)))

    assert set(out) == ENVELOPE_KEYS
    assert out["count"] == 45  # from meta.paging.total, not len(items)
    assert out["page"] == 1
    assert [d["course_no"] for d in out["items"]] == [1723]

    item = out["items"][0]
    # the same core keys the bus domain exposes
    assert item["course_cd"] == "M1"
    assert item["title"] == "富士山"
    assert item["date"] == "2026-11-01"
    assert item["price"] == 30000
    assert item["status"] == 1
    assert item["detail_url"] == "https://www.maitabi.jp/detail.php?courseNo=1723"
    # upstream keys are kept, never replaced
    assert item["courseNo"] == 1723


@respx.mock
@pytest.mark.asyncio
async def test_general_search_price_filter_uses_real_price_field():
    respx.get("https://www.maitabi.jp/api/v1/category_search").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {"courseNo": 1, "yoyakuStatus": 1, "roomPriceMin": 9000},
                    {"courseNo": 2, "yoyakuStatus": 1, "roomPriceMin": 15000},
                    {"courseNo": 3, "yoyakuStatus": 1, "roomPriceMin": 30000},
                ],
                "meta": {"paging": {"page": 1, "total": 3}},
            },
        )
    )
    out = _load(await search_general_tours_service(SearchGeneralToursInput(min_price=10000, max_price=20000)))
    assert [d["course_no"] for d in out["items"]] == [2]


@respx.mock
@pytest.mark.asyncio
async def test_general_search_error_passes_through_unchanged():
    respx.get("https://www.maitabi.jp/api/v1/category_search").mock(
        return_value=Response(200, json={"errors": {"code": 0, "message": "Too Many Attempts."}})
    )
    out = _load(await search_general_tours_service(SearchGeneralToursInput()))
    assert out["error"] == RATE_LIMIT_ERROR
    assert out["retry_hint"] == "wait ~60s and retry manually"


@respx.mock
@pytest.mark.asyncio
async def test_upstream_500_is_clear_error_not_exception():
    respx.get("https://api.bus.maitabi.jp/tour_search").mock(return_value=Response(500, text="oops"))
    out = _load(await search_tours_service(SearchBusToursInput(month=9)))
    assert out["error"] == "Upstream service returned error: 500"
    assert "detail" in out
