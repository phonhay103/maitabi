"""General tour detail pages: embedded JSON + three tables, fully offline.

The fixtures are real `detail.php` pages saved from production — one day trip
and one multi-day overseas tour — because the parser's only real risk is the
markup changing, and a hand-written sample would never catch that.
"""

import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from maitabi.core.inputs import GetGeneralTourDetailInput
from maitabi.services.general_detail import (
    DetailLayoutError,
    get_general_tour_detail_service,
    parse_detail_page,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _page(course_no: int) -> str:
    return (FIXTURES / f"general_detail_{course_no}.html").read_text(encoding="utf-8")


def test_day_trip_page_is_fully_parsed():
    detail = parse_detail_page(_page(25461))

    # the record comes from the embedded JSON, not from prose
    assert detail["course_no"] == 25461
    assert detail["course_cd"] == "M5626"
    assert detail["title"].startswith("安心安全富士登山2026")
    assert detail["description"] and len(detail["description"]) > 100
    assert detail["source_url"] == "https://www.maitabi.jp/detail.php?courseNo=25461"

    assert detail["itinerary"] == [
        {
            "day": 1,
            "schedule": detail["itinerary"][0]["schedule"],
            "lodging": "",
        }
    ]
    assert "神武寺駅10:45集合" in detail["itinerary"][0]["schedule"]

    conditions = detail["conditions"]
    assert conditions["duration"] == "0泊1日"
    assert conditions["min_participants"] == 10
    assert conditions["tour_conductor"] is True
    assert conditions["local_staff"] is True
    assert conditions["meals"] == {"breakfast": 0, "lunch": 0, "dinner": 0}
    assert conditions["departure_area"] == "関東"
    assert conditions["purposes"] == ["現地発着ツアー", "登山・ハイキング"]

    (departure,) = detail["departures"]
    assert departure["date"] == "2026-11-01"
    assert departure["date_label"] == "2026年11月01日（日）"  # noqa: RUF001
    assert departure["price"] == 3776
    assert departure["price_label"] == "3,776円"
    assert departure["departure_status"] == "催行決定"
    assert departure["booking_status"] == "受付中"
    assert departure["booking_url"].startswith("https://www.travel-answer.ne.jp/")
    assert detail["phone_reservation"] is True
    assert "warnings" not in detail


def test_multi_day_overseas_page_keeps_lodging_and_meal_counts():
    detail = parse_detail_page(_page(24683))

    assert detail["title"].startswith("台湾最高峰")
    itinerary = detail["itinerary"]
    assert len(itinerary) == 4
    assert [day["day"] for day in itinerary] == [1, 2, 3, 4]
    assert itinerary[0]["lodging"] == "(埔里泊)"
    assert itinerary[1]["lodging"] == "(排雲山荘泊)"

    conditions = detail["conditions"]
    assert conditions["duration"] == "3泊4日"
    assert conditions["min_participants"] == 8
    assert conditions["meals"] == {"breakfast": 3, "lunch": 2, "dinner": 3}

    assert len(detail["departures"]) == 2
    assert detail["departures"][0]["price"] == 311100


def test_page_without_the_embedded_record_raises():
    with pytest.raises(DetailLayoutError):
        parse_detail_page("<html><body>no record here</body></html>")


def test_missing_tables_warn_instead_of_returning_hollow_fields():
    """A page that still has the JSON but lost its tables must say so."""
    page = _page(25461)
    start = page.index("<table")
    end = page.rindex("</table>") + len("</table>")
    detail = parse_detail_page(page[:start] + page[end:])

    assert detail["course_no"] == 25461
    assert detail["itinerary"] is None
    assert detail["conditions"] is None
    assert detail["departures"] is None
    assert detail["warnings"] == [
        "itinerary table not found",
        "conditions table not found",
        "departure table not found",
    ]


@respx.mock
@pytest.mark.asyncio
async def test_service_fetches_and_parses_the_page():
    respx.get("https://www.maitabi.jp/detail.php", params={"courseNo": 25461}).mock(
        return_value=Response(200, text=_page(25461))
    )
    detail = await get_general_tour_detail_service(GetGeneralTourDetailInput(course_no=25461))
    assert detail["course_no"] == 25461
    assert detail["departures"][0]["price"] == 3776


@respx.mock
@pytest.mark.asyncio
async def test_layout_change_is_an_error_payload_not_an_exception():
    respx.get("https://www.maitabi.jp/detail.php").mock(return_value=Response(200, text="<html></html>"))
    result = await get_general_tour_detail_service(GetGeneralTourDetailInput(course_no=25461))
    assert result["error"] == "Could not read the general tour detail page"
    assert "detailData" in result["detail"]
    assert result["source_url"] == "https://www.maitabi.jp/detail.php?courseNo=25461"


@respx.mock
@pytest.mark.asyncio
async def test_upstream_500_passes_through_unchanged():
    respx.get("https://www.maitabi.jp/detail.php").mock(return_value=Response(500, text="boom"))
    result = await get_general_tour_detail_service(GetGeneralTourDetailInput(course_no=25461))
    assert result["error"] == "Upstream service returned error: 500"


@respx.mock
@pytest.mark.asyncio
async def test_batch_returns_the_shared_envelope():
    respx.get("https://www.maitabi.jp/detail.php").mock(
        side_effect=[Response(200, text=_page(25461)), Response(200, text=_page(24683))]
    )
    result = await get_general_tour_detail_service(GetGeneralTourDetailInput(course_no=[25461, 24683]))

    assert set(result) == {"count", "page", "items", "query"}
    assert result["page"] is None
    assert result["count"] == 2
    assert [item["course_no"] for item in result["items"]] == [25461, 24683]
    assert json.dumps(result, ensure_ascii=False).startswith('{"count"')
