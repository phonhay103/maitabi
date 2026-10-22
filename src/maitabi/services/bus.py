"""Service functions for Maitabi mountain bus tours (bus.maitabi.jp & api.bus.maitabi.jp).

Each service maps an Input model → upstream query params → GET → result
post-processing, and returns a plain dict. Serialization to JSON happens at
the edge (MCP tool / CLI command), never here.

Search returns the uniform envelope (see `core/envelope.py`); filter options,
district groups, and single-tour detail return their own objects.
"""

from datetime import datetime
from enum import IntEnum
from typing import Any

from maitabi.config import API_BASE
from maitabi.core.days import parse_days
from maitabi.core.envelope import as_int, dict_items, envelope, query_of
from maitabi.core.filters import (
    BUS_CLOSED_STATUSES,
    derive_bus_detail_url,
    is_open_status,
    parse_price_jpy,
    within_price_range,
)
from maitabi.core.inputs import (
    BusFilterBase,
    GetBusTourDetailInput,
    ListDistrictGroupsInput,
    ListFilterMasterInput,
    ListFiltersInput,
    SearchBusToursInput,
)
from maitabi.services.http import gather_limited, get_json


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


def _collect_tours(input: SearchBusToursInput, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply price/availability filters and derive `detail_url` for each item."""
    kept: list[dict[str, Any]] = []
    for item in items:
        if (input.min_price is not None or input.max_price is not None) and not within_price_range(
            parse_price_jpy(item.get("price", "0")), input.min_price, input.max_price
        ):
            continue
        if input.require_available_seats and not is_open_status(item.get("status", ""), BUS_CLOSED_STATUSES):
            continue
        course_no = item.get("course_no")
        if isinstance(course_no, (int, str)):
            item["detail_url"] = derive_bus_detail_url(course_no, str(item.get("date", "")), input.month)
        kept.append(item)
    return kept


async def list_filters_service(input: ListFiltersInput) -> dict[str, Any]:
    """Fetch available filter options for mountain bus tours."""
    return await get_json(f"{API_BASE}/tour_course", params=_bus_params(input))


async def list_district_groups_service(input: ListDistrictGroupsInput) -> dict[str, Any]:
    """Fetch district groups and tour counts for mountain bus tours."""
    return await get_json(f"{API_BASE}/district_group", params=_bus_params(input))


async def list_filter_master_service(input: ListFilterMasterInput) -> dict[str, Any]:
    """Fetch one cascading master list (style, bus sheet, return day, district).

    Same data `list_filters` returns, but a single group at a time and a much
    smaller payload; counts stay filter-aware.
    """
    data = await get_json(f"{API_BASE}/{input.kind}", params=_bus_params(input))
    if "error" in data:
        return data
    raw = (data.get("pulldown_options") or {}).get(input.kind)
    options = [
        {"id": as_int(option.get("id")), "name": option.get("name"), "tour_count": as_int(option.get("tour_count"))}
        for option in (raw if isinstance(raw, list) else [])
        if isinstance(option, dict)
    ]
    return {"kind": input.kind, "options": options, "query": query_of(input)}


async def search_tours_service(input: SearchBusToursInput) -> dict[str, Any]:
    """Search mountain bus tours with filters."""
    params = _bus_params(input, default_month=False)
    params["page"] = str(input.page)

    parsed_days = parse_days(input.day)
    count: int | None
    if parsed_days is not None and len(parsed_days) > 1:
        # Multi-day: fan out one request per day, then merge the tour lists.
        async def fetch_for_day(d: int) -> dict[str, Any]:
            day_params = dict(params, day=str(d))
            return await get_json(f"{API_BASE}/tour_search", params=day_params)

        results = await gather_limited(fetch_for_day, parsed_days)
        items: list[dict[str, Any]] = []
        total = 0
        known = False
        for res in results:
            if "error" in res:
                return res
            day_items = dict_items(res.get("tour"))
            if day_items:
                items.extend(day_items)
                day_count = as_int(res.get("count"))
                if day_count is not None:
                    total += day_count
                    known = True
        count = total if known else None
    else:
        if parsed_days is not None and len(parsed_days) == 1:
            params["day"] = str(parsed_days[0])
        data = await get_json(f"{API_BASE}/tour_search", params=params)
        if "error" in data:
            return data
        items = dict_items(data.get("tour"))
        count = as_int(data.get("count"))

    return envelope(items=_collect_tours(input, items), count=count, page=input.page, query=query_of(input))


async def get_tour_detail_service(input: GetBusTourDetailInput) -> dict[str, Any]:
    """Fetch full details for one or many mountain bus tours."""
    if isinstance(input.course_no, list):

        async def fetch_one(c_no: int) -> dict[str, Any]:
            return await get_json(f"{API_BASE}/tour_detail", params={"course_no": str(c_no)})

        results = await gather_limited(fetch_one, input.course_no)
        return envelope(items=results, count=len(results), page=None, query=query_of(input))
    return await get_json(f"{API_BASE}/tour_detail", params={"course_no": str(input.course_no)})
