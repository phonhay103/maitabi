"""Service functions for general Mainichi Travel tours & calendar (www.maitabi.jp).

Same layering as `services/bus.py`: Input model → query params → GET →
post-processing, returning plain dicts.
"""

from maitabi_mcp_server.config import API_BASE, MAIN_BASE
from maitabi_mcp_server.core.days import parse_days
from maitabi_mcp_server.core.errors import RATE_LIMIT_ERROR
from maitabi_mcp_server.core.filters import (
    GENERAL_CLOSED_STATUSES,
    derive_general_detail_url,
    is_open_status,
    parse_price_jpy,
    within_price_range,
)
from maitabi_mcp_server.core.inputs import (
    GetGeneralTourDetailInput,
    GetTourCalendarInput,
    SearchGeneralToursInput,
)
from maitabi_mcp_server.services.http import gather_limited, get_json


async def search_general_tours_service(input: SearchGeneralToursInput) -> dict:
    """Search Mainichi Travel general tours."""
    params: list[tuple[str, str]] = [
        ("travelType", str(input.travel_type.value)),
        ("page", str(input.page)),
    ]
    if input.keyword:
        params.append(("keyword", input.keyword))
    if input.year_month:
        params.append(("startDateYearMonthMin", input.year_month))
    if input.list_order:
        params.append(("listOrder", input.list_order))

    # Category arrays (must be added BEFORE fetching).
    for group_no, group in enumerate(
        (
            input.category_nos1,
            input.category_nos2,
            input.category_nos3,
            input.category_nos4,
            input.category_nos5,
        ),
        start=1,
    ):
        if group:
            for val in group:
                params.append((f"categoryNos{group_no}[]", str(val)))

    parsed_days = parse_days(input.day)
    if parsed_days and len(parsed_days) > 1:
        # The upstream API doesn't accept array day; fan out per day like bus.
        async def fetch_for_day(d: int):
            day_params = list(params) + [("startDateDayMin", str(d))]
            return await get_json(f"{MAIN_BASE}/api/v1/category_search", params=day_params)

        results = await gather_limited(fetch_for_day, parsed_days)

        all_tours: list = []
        data: dict = {"data": []}
        for res in results:
            # Fail fast on throttle: no partial merges, no auto-retry.
            if res.get("error") == RATE_LIMIT_ERROR:
                return res
            if "data" in res and isinstance(res["data"], list):
                all_tours.extend(res["data"])
        data["data"] = all_tours
    else:
        if parsed_days and len(parsed_days) == 1:
            params.append(("startDateDayMin", str(parsed_days[0])))
        data = await get_json(f"{MAIN_BASE}/api/v1/category_search", params=params)

    # Post-process: detail_url enrichment, price filter, availability filter.
    if "data" in data and isinstance(data["data"], list):
        filtered_tours = []
        for item in data["data"]:
            if c_no := item.get("courseNo"):
                item["detail_url"] = derive_general_detail_url(c_no)
            if input.min_price is not None or input.max_price is not None:
                if not within_price_range(
                    parse_price_jpy(item.get("price", "0")), input.min_price, input.max_price
                ):
                    continue
            if input.require_available_seats and not is_open_status(
                item.get("saikouStatus", ""), GENERAL_CLOSED_STATUSES
            ):
                continue
            filtered_tours.append(item)
        data["data"] = filtered_tours
    return data


async def get_general_tour_detail_service(input: GetGeneralTourDetailInput) -> dict:
    """Fetch complete details for a general tour (shared tour_detail endpoint)."""
    if isinstance(input.course_no, list):
        async def fetch_one(c_no: int):
            return await get_json(f"{API_BASE}/tour_detail", params={"course_no": str(c_no)})

        results = await gather_limited(fetch_one, input.course_no)
        return {"tours": results}
    return await get_json(f"{API_BASE}/tour_detail", params={"course_no": str(input.course_no)})


async def get_tour_calendar_service(input: GetTourCalendarInput) -> dict:
    """Fetch monthly departure calendar and tour schedule matrix."""
    url = f"{MAIN_BASE}/api/v1/calendar/{input.year}/{input.month}"
    params = {}
    if input.travel_type is not None:
        params["travelType"] = str(input.travel_type.value)
    return await get_json(url, params=params)
