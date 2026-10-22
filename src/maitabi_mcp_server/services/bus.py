"""Service functions for Maitabi mountain bus tours (bus.maitabi.jp & api.bus.maitabi.jp).

Each service maps an Input model → upstream query params → GET → result
post-processing, and returns a plain dict. Serialization to JSON happens at
the edge (MCP tool / CLI command), never here.
"""

from datetime import datetime
from enum import IntEnum
from typing import Any

from maitabi_mcp_server.config import API_BASE
from maitabi_mcp_server.core.days import parse_days
from maitabi_mcp_server.core.filters import (
    BUS_CLOSED_STATUSES,
    derive_bus_detail_url,
    is_open_status,
    parse_price_jpy,
    within_price_range,
)
from maitabi_mcp_server.core.inputs import (
    BusFilterBase,
    GetBusTourDetailInput,
    ListDistrictGroupsInput,
    ListFiltersInput,
    SearchBusToursInput,
)
from maitabi_mcp_server.services.http import gather_limited, get_json


def _enum_value(value: object) -> object:
    """IntEnum → plain int; other values pass through."""
    return value.value if isinstance(value, IntEnum) else value


def _bus_params(inp: BusFilterBase, *, default_month: bool = True) -> dict[str, str]:
    """Build shared bus-filter query params from any BusFilterBase input.

    `default_month=True` substitutes the current month when omitted (the
    list endpoints require it); search leaves the month untouched.
    """
    month = inp.month if inp.month is not None else (datetime.now().month if default_month else None)
    params: dict[str, str] = {"departure": str(_enum_value(inp.departure))}
    if month is not None:
        params["month"] = str(month)
    for name in ("day", "area", "style", "return_day", "bus_sheet", "stay1", "stay2", "stay3"):
        value = getattr(inp, name, None)
        if value is not None:
            params[name] = str(_enum_value(value))
    if inp.course_cd not in (None, ""):
        params["course_cd"] = inp.course_cd
    if inp.keyword not in (None, ""):
        params["keyword"] = inp.keyword
    return params


async def list_filters_service(input: ListFiltersInput) -> dict[str, Any]:
    """Fetch available filter options for mountain bus tours."""
    return await get_json(f"{API_BASE}/tour_course", params=_bus_params(input))


async def list_district_groups_service(input: ListDistrictGroupsInput) -> dict[str, Any]:
    """Fetch district groups and tour counts for mountain bus tours."""
    return await get_json(f"{API_BASE}/district_group", params=_bus_params(input))


async def search_tours_service(input: SearchBusToursInput) -> dict[str, Any]:
    """Search mountain bus tours with filters."""
    params = _bus_params(input, default_month=False)
    params["page"] = str(input.page)

    parsed_days = parse_days(input.day)
    if parsed_days is not None and len(parsed_days) > 1:
        # Multi-day: fan out one request per day, then merge the tour lists.
        async def fetch_for_day(d: int) -> dict[str, Any]:
            day_params = dict(params, day=str(d))
            return await get_json(f"{API_BASE}/tour_search", params=day_params)

        results = await gather_limited(fetch_for_day, parsed_days)
        data: dict[str, Any] = {"tour": []}
        for res in results:
            if "tour" in res and isinstance(res["tour"], list):
                data["tour"].extend(res["tour"])
    else:
        if parsed_days is not None and len(parsed_days) == 1:
            params["day"] = str(parsed_days[0])
        data = await get_json(f"{API_BASE}/tour_search", params=params)

    # Post-process: price filter, availability filter, detail_url enrichment.
    if "tour" in data and isinstance(data["tour"], list):
        filtered_tours = []
        for item in data["tour"]:
            if (input.min_price is not None or input.max_price is not None) and not within_price_range(
                parse_price_jpy(item.get("price", "0")), input.min_price, input.max_price
            ):
                continue
            if input.require_available_seats and not is_open_status(item.get("status", ""), BUS_CLOSED_STATUSES):
                continue
            item["detail_url"] = derive_bus_detail_url(item.get("course_no"), item.get("date", ""), input.month)
            filtered_tours.append(item)
        data["tour"] = filtered_tours
    return data


async def get_tour_detail_service(input: GetBusTourDetailInput) -> dict[str, Any]:
    """Fetch full details for one or many mountain bus tours."""
    if isinstance(input.course_no, list):

        async def fetch_one(c_no: int) -> dict[str, Any]:
            return await get_json(f"{API_BASE}/tour_detail", params={"course_no": str(c_no)})

        results = await gather_limited(fetch_one, input.course_no)
        return {"tours": results}
    return await get_json(f"{API_BASE}/tour_detail", params={"course_no": str(input.course_no)})
