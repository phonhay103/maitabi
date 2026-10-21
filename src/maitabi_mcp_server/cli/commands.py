"""CLI command handlers — thin wrappers over core services/models.

Each handler: argparse namespace -> Pydantic Input -> `asyncio.run(service())`
-> print JSON to stdout (or --output file). No business logic here.
Must NOT import fastmcp/mcp/server/tools.
"""

import argparse
import asyncio
import json

from maitabi_mcp_server.core.enums import (
    BusSeatType,
    DeparturePoint,
    ReturnDayOption,
    TourStyle,
    TravelType,
)
from maitabi_mcp_server.core.inputs import (
    GetBusTourDetailInput,
    GetGeneralTourDetailInput,
    GetTourCalendarInput,
    ListDistrictGroupsInput,
    ListFiltersInput,
    SearchBusToursInput,
    SearchGeneralToursInput,
)
from maitabi_mcp_server.services.bus import (
    get_tour_detail_service,
    list_district_groups_service,
    list_filters_service,
    search_tours_service,
)
from maitabi_mcp_server.services.general import (
    get_general_tour_detail_service,
    get_tour_calendar_service,
    search_general_tours_service,
)
from maitabi_mcp_server.services.http import close_http_client


def _emit(data: dict, args: argparse.Namespace) -> None:
    """Serialize the service dict to the CLI's JSON wire format.

    Always indent=2 / ensure_ascii=False — byte-identical to the historic
    output (services used to pre-serialize with the same settings), so
    `--pretty` stays a compat no-op.
    """
    text = json.dumps(data, ensure_ascii=False, indent=2)
    output = getattr(args, "output", None)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)


async def _run(service_coro) -> dict:
    try:
        return await service_coro
    finally:
        await close_http_client()


def _parse_course_nos(raw: str) -> int | list[int]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    nums = [int(p) for p in parts]
    if len(nums) == 1:
        return nums[0]
    return nums


def _parse_id_list(raw: str | None) -> list[int] | None:
    if not raw:
        return None
    return [int(p.strip()) for p in raw.split(",") if p.strip()]


def _optional_enum(enum_cls, value):
    return enum_cls(value) if value is not None else None


def cmd_list_filters(args: argparse.Namespace) -> None:
    payload = ListFiltersInput(
        departure=DeparturePoint(args.departure),
        month=args.month,
        day=args.day if args.day is None else (int(args.day) if args.day.isdigit() else args.day),
        area=args.area,
        style=_optional_enum(TourStyle, args.style),
        return_day=_optional_enum(ReturnDayOption, args.return_day),
        bus_sheet=_optional_enum(BusSeatType, args.bus_sheet),
        stay1=args.stay1,
        stay2=args.stay2,
        stay3=args.stay3,
        course_cd=args.course_cd,
        keyword=args.keyword,
    )
    _emit(asyncio.run(_run(list_filters_service(payload))), args)


def cmd_list_district_groups(args: argparse.Namespace) -> None:
    payload = ListDistrictGroupsInput(
        departure=DeparturePoint(args.departure),
        month=args.month,
        day=args.day if args.day is None else (int(args.day) if args.day.isdigit() else args.day),
        area=args.area,
        style=_optional_enum(TourStyle, args.style),
        return_day=_optional_enum(ReturnDayOption, args.return_day),
        bus_sheet=_optional_enum(BusSeatType, args.bus_sheet),
        stay1=args.stay1,
        stay2=args.stay2,
        stay3=args.stay3,
        course_cd=args.course_cd,
        keyword=args.keyword,
    )
    _emit(asyncio.run(_run(list_district_groups_service(payload))), args)


def cmd_search_tours(args: argparse.Namespace) -> None:
    payload = SearchBusToursInput(
        departure=DeparturePoint(args.departure),
        month=args.month,
        day=args.day,
        area=args.area,
        style=_optional_enum(TourStyle, args.style),
        return_day=_optional_enum(ReturnDayOption, args.return_day),
        bus_sheet=_optional_enum(BusSeatType, args.bus_sheet),
        stay1=args.stay1,
        stay2=args.stay2,
        stay3=args.stay3,
        course_cd=args.course_cd,
        keyword=args.keyword,
        page=args.page,
        max_price=args.max_price,
        min_price=args.min_price,
        require_available_seats=args.require_available_seats,
    )
    _emit(asyncio.run(_run(search_tours_service(payload))), args)


def cmd_get_tour_detail(args: argparse.Namespace) -> None:
    payload = GetBusTourDetailInput(course_no=_parse_course_nos(args.course_no))
    _emit(asyncio.run(_run(get_tour_detail_service(payload))), args)


def cmd_search_general_tours(args: argparse.Namespace) -> None:
    payload = SearchGeneralToursInput(
        travel_type=TravelType(args.travel_type),
        keyword=args.keyword,
        year_month=args.year_month,
        day=args.day,
        min_price=args.min_price,
        max_price=args.max_price,
        require_available_seats=args.require_available_seats,
        page=args.page,
        list_order=args.list_order,
        category_nos1=_parse_id_list(args.category_nos1),
        category_nos2=_parse_id_list(args.category_nos2),
        category_nos3=_parse_id_list(args.category_nos3),
        category_nos4=_parse_id_list(args.category_nos4),
        category_nos5=_parse_id_list(args.category_nos5),
    )
    _emit(asyncio.run(_run(search_general_tours_service(payload))), args)


def cmd_get_general_tour_detail(args: argparse.Namespace) -> None:
    payload = GetGeneralTourDetailInput(course_no=_parse_course_nos(args.course_no))
    _emit(asyncio.run(_run(get_general_tour_detail_service(payload))), args)


def cmd_get_tour_calendar(args: argparse.Namespace) -> None:
    payload = GetTourCalendarInput(
        year=args.year,
        month=args.month,
        travel_type=_optional_enum(TravelType, args.travel_type),
    )
    _emit(asyncio.run(_run(get_tour_calendar_service(payload))), args)


COMMAND_HANDLERS = {
    "list-filters": cmd_list_filters,
    "list-district-groups": cmd_list_district_groups,
    "search-tours": cmd_search_tours,
    "get-tour-detail": cmd_get_tour_detail,
    "search-general-tours": cmd_search_general_tours,
    "get-general-tour-detail": cmd_get_general_tour_detail,
    "get-tour-calendar": cmd_get_tour_calendar,
}
