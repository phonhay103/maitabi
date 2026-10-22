"""Single source of truth for the seven Maitabi actions.

One `Action` per capability: MCP tool name, CLI subcommand, Input model,
service callable, upstream endpoint, MCP tool description, and CLI help.
`mcp/tools.py`, `cli/parser.py`, `cli/commands.py`, and
`scripts/gen_catalog.py` all read this table — an action is added or
changed here once, and every interface follows.

Layering: registry wires `core/` (inputs) to `services/` (endpoints) only.
Adapters (mcp/*, cli/*) import this module; it never imports them, so the
CLI stays importable without fastmcp installed.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

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


@dataclass(frozen=True)
class Action:
    """One callable capability exposed over MCP and CLI alike."""

    tool: str  # MCP tool name (snake_case)
    command: str  # CLI subcommand (kebab_case)
    input_model: type[BaseModel]  # parameter source of truth
    service: Callable[[Any], Awaitable[dict[str, Any]]]  # async core function
    endpoint: str  # upstream endpoint (catalog/documentation)
    doc: str  # MCP tool description (verbatim wire text)
    help: str  # CLI subcommand help (one line)


ACTIONS: tuple[Action, ...] = (
    Action(
        tool="list_filters",
        command="list-filters",
        input_model=ListFiltersInput,
        service=list_filters_service,
        endpoint="GET /tour_course",
        doc=(
            "Fetch available filter dropdown options, departure areas, tour styles, mountain lodges, "
            "and tour counts for Maitabi bus tours.\n\n"
            "Supports cascading filtering\u2014options and counts update dynamically based on other "
            "selected filters."
        ),
        help="Fetch bus tour filter options and tour counts",
    ),
    Action(
        tool="list_district_groups",
        command="list-district-groups",
        input_model=ListDistrictGroupsInput,
        service=list_district_groups_service,
        endpoint="GET /district_group",
        doc=(
            "Fetch mountain area/district groups and tour counts for Maitabi mountain bus tours.\n\n"
            "Supports cascading filtering\u2014district groups and counts update dynamically based on "
            "other selected filters."
        ),
        help="Fetch area/district groups and tour counts",
    ),
    Action(
        tool="search_tours",
        command="search-tours",
        input_model=SearchBusToursInput,
        service=search_tours_service,
        endpoint="GET /tour_search",
        doc=(
            "Search mountain bus tours and lodge packages on Maitabi (bus.maitabi.jp) with detailed "
            "filter criteria.\n\n"
            "Returns a JSON string containing matching bus tours, seat options, pricing, departure "
            "dates, and course numbers."
        ),
        help="Search mountain bus tours with filters",
    ),
    Action(
        tool="get_tour_detail",
        command="get-tour-detail",
        input_model=GetBusTourDetailInput,
        service=get_tour_detail_service,
        endpoint="GET /tour_detail",
        doc=(
            "Fetch detailed information, schedule, pricing, and bus stops for a specific Maitabi "
            "mountain bus tour by course_no.\n\n"
            "Returns a JSON string containing complete tour itinerary, bus departure points, seat "
            "options, pricing, and lodging info."
        ),
        help="Fetch bus tour detail by course_no",
    ),
    Action(
        tool="search_general_tours",
        command="search-general-tours",
        input_model=SearchGeneralToursInput,
        service=search_general_tours_service,
        endpoint="GET /category_search",
        doc=(
            "Search general travel tours and mountain climbing packages on www.maitabi.jp.\n\n"
            "Returns a JSON string containing matching tours, total count, pagination, sorting, and "
            "categories."
        ),
        help="Search general tours on www.maitabi.jp",
    ),
    Action(
        tool="get_general_tour_detail",
        command="get-general-tour-detail",
        input_model=GetGeneralTourDetailInput,
        service=get_general_tour_detail_service,
        endpoint="GET /tour_detail",
        doc=(
            "Fetch complete details, itinerary, pricing, and booking information for a general tour "
            "on www.maitabi.jp.\n\n"
            "Returns a JSON string containing tour itinerary, meal conditions, price matrix, lodging, "
            "and booking links."
        ),
        help="Fetch general tour detail by courseNo",
    ),
    Action(
        tool="get_tour_calendar",
        command="get-tour-calendar",
        input_model=GetTourCalendarInput,
        service=get_tour_calendar_service,
        endpoint="GET /calendar/{year}/{month}",
        doc=(
            "Fetch monthly departure calendar and tour schedule matrix on www.maitabi.jp for a given "
            "year and month.\n\n"
            "Returns a JSON string with daily departure schedule matrix, tour availability, and "
            "calendar dates."
        ),
        help="Fetch monthly departure calendar matrix",
    ),
)

ACTION_BY_COMMAND = {action.command: action for action in ACTIONS}
ACTION_BY_TOOL = {action.tool: action for action in ACTIONS}
