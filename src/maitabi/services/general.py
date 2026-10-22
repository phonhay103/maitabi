"""Service functions for general tours & calendar (www.maitabi.jp).

Same layering as `services/bus.py`: Input model → query params → GET →
post-processing, returning plain dicts. Search returns the uniform envelope
(see `core/envelope.py`); calendar and single-tour detail return their own
objects.

www.maitabi.jp nests the presentable fields under `tTravel` and reports
statuses as numbers, so items are normalised to the same core keys the bus
domain uses (`course_no`, `course_cd`, `title`, `date`, `price`, `status`,
`detail_url`). Upstream keys are kept alongside, never replaced.
"""

from typing import Any

from maitabi.config import API_BASE, MAIN_BASE
from maitabi.core.days import parse_days
from maitabi.core.envelope import as_int, dict_items, envelope, query_of
from maitabi.core.errors import RATE_LIMIT_ERROR
from maitabi.core.filters import (
    GENERAL_CLOSED_STATUSES,
    derive_general_detail_url,
    is_open_status,
    parse_price_jpy,
    within_price_range,
)
from maitabi.core.inputs import (
    GetGeneralTourDetailInput,
    GetTourCalendarInput,
    SearchGeneralToursInput,
)
from maitabi.services.http import gather_limited, get_json

SEARCH_URL = f"{MAIN_BASE}/api/v1/category_search"


def _first(*values: object) -> object:
    """First value that is neither None nor empty."""
    for value in values:
        if value not in (None, ""):
            return value
    return None


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    """Add the shared core keys to one www.maitabi.jp search item.

    `status` is `yoyakuStatus` (booking availability), not `saikouStatus`
    (latest departure availability), because only the former decides whether
    the tour can be booked right now.
    """
    travel = item.get("tTravel") or {}
    course_no = _first(item.get("courseNo"), travel.get("courseNo"))
    item["course_no"] = course_no
    item["course_cd"] = _first(item.get("courseCd"), travel.get("courseCd"))
    item["title"] = _first(travel.get("courseName"), item.get("courseName"))
    item["date"] = _first(item.get("saikouDate"), travel.get("saikouDate"))
    item["price"] = _first(item.get("roomPriceMin"), travel.get("priceMin"), item.get("price"))
    item["status"] = _first(item.get("yoyakuStatus"), item.get("saikouStatus"))
    if isinstance(course_no, (int, str)):
        item["detail_url"] = derive_general_detail_url(course_no)
    return item


def _filter_items(input: SearchGeneralToursInput, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for item in items:
        item = normalize_item(item)
        if (input.min_price is not None or input.max_price is not None) and not within_price_range(
            parse_price_jpy(item["price"]), input.min_price, input.max_price
        ):
            continue
        if input.require_available_seats and not is_open_status(item["status"], GENERAL_CLOSED_STATUSES):
            continue
        kept.append(item)
    return kept


def _search_params(input: SearchGeneralToursInput) -> list[tuple[str, str]]:
    params: list[tuple[str, str]] = [
        ("travelType", str(input.travel_type.value)),
        ("page", str(input.page)),
    ]
    if input.keyword not in (None, ""):
        params.append(("keyword", input.keyword))
    if input.year_month not in (None, ""):
        params.append(("startDateYearMonthMin", input.year_month))
    if input.list_order not in (None, ""):
        params.append(("listOrder", input.list_order))
    for group_no, group in enumerate(
        (input.category_nos1, input.category_nos2, input.category_nos3, input.category_nos4, input.category_nos5),
        start=1,
    ):
        for val in group or ():
            params.append((f"categoryNos{group_no}[]", str(val)))
    return params


async def search_general_tours_service(input: SearchGeneralToursInput) -> dict[str, Any]:
    """Search Mainichi Travel general tours."""
    params = _search_params(input)
    parsed_days = parse_days(input.day)

    count: int | None = None
    if parsed_days is not None and len(parsed_days) > 1:
        # The upstream API doesn't accept an array day; fan out per day.
        async def fetch_for_day(d: int) -> dict[str, Any]:
            return await get_json(SEARCH_URL, params=[*params, ("startDateDayMin", str(d))])

        results = await gather_limited(fetch_for_day, parsed_days)
        items: list[dict[str, Any]] = []
        total = 0
        known = False
        for res in results:
            # Fail fast on throttle: no partial merges, no auto-retry.
            if res.get("error") == RATE_LIMIT_ERROR or "error" in res:
                return res
            day_items = dict_items(res.get("data"))
            if day_items:
                items.extend(day_items)
                day_total = as_int(((res.get("meta") or {}).get("paging") or {}).get("total"))
                if day_total is not None:
                    total += day_total
                    known = True
        count = total if known else None
    else:
        if parsed_days is not None and len(parsed_days) == 1:
            params = [*params, ("startDateDayMin", str(parsed_days[0]))]
        data = await get_json(SEARCH_URL, params=params)
        if "error" in data:
            return data
        items = dict_items(data.get("data"))
        count = as_int(((data.get("meta") or {}).get("paging") or {}).get("total"))

    return envelope(items=_filter_items(input, items), count=count, page=input.page, query=query_of(input))


async def get_general_tour_detail_service(input: GetGeneralTourDetailInput) -> dict[str, Any]:
    """Fetch complete details for a general tour (shared tour_detail endpoint)."""
    if isinstance(input.course_no, list):

        async def fetch_one(c_no: int) -> dict[str, Any]:
            return await get_json(f"{API_BASE}/tour_detail", params={"course_no": str(c_no)})

        results = await gather_limited(fetch_one, input.course_no)
        return envelope(items=results, count=len(results), page=None, query=query_of(input))
    return await get_json(f"{API_BASE}/tour_detail", params={"course_no": str(input.course_no)})


async def get_tour_calendar_service(input: GetTourCalendarInput) -> dict[str, Any]:
    """Fetch monthly departure calendar and tour schedule matrix."""
    url = f"{MAIN_BASE}/api/v1/calendar/{input.year}/{input.month}"
    params = {}
    if input.travel_type is not None:
        params["travelType"] = str(input.travel_type.value)
    return await get_json(url, params=params)
