"""Single source of truth for the eight Maitabi actions.

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

from maitabi.core.inputs import (
    GetBusTourDetailInput,
    GetGeneralTourDetailInput,
    GetTourCalendarInput,
    ListDistrictGroupsInput,
    ListFilterMasterInput,
    ListFiltersInput,
    SearchBusToursInput,
    SearchGeneralToursInput,
)
from maitabi.services.bus import (
    get_tour_detail_service,
    list_district_groups_service,
    list_filter_master_service,
    list_filters_service,
    search_tours_service,
)
from maitabi.services.general import get_tour_calendar_service, search_general_tours_service
from maitabi.services.general_detail import get_general_tour_detail_service


@dataclass(frozen=True)
class Action:
    """One callable capability exposed over MCP and CLI alike."""

    domain: str  # upstream family: "bus" (api.bus.maitabi.jp) or "general" (www.maitabi.jp)
    tool: str  # MCP tool name (snake_case, domain-prefixed)
    title: str  # MCP tool title (the service prefix lives here, not in `tool`)
    command: str  # CLI subcommand (kebab_case)
    input_model: type[BaseModel]  # parameter source of truth
    service: Callable[[Any], Awaitable[dict[str, Any]]]  # async core function
    endpoint: str  # upstream endpoint (catalog/documentation)
    doc: str  # MCP tool description (verbatim wire text)
    help: str  # CLI subcommand help (one line)


ACTIONS: tuple[Action, ...] = (
    Action(
        domain="bus",
        tool="bus_list_filters",
        title="Maitabi: list bus tour filter options",
        command="list-filters",
        input_model=ListFiltersInput,
        service=list_filters_service,
        endpoint="GET /tour_course",
        doc=(
            "Fetch available filter dropdown options, departure areas, tour styles, mountain lodges, "
            "and tour counts for Maitabi bus tours.\n\n"
            "Supports cascading filtering\u2014options and counts update dynamically based on other "
            "selected filters. This is the large, everything-at-once call: prefer "
            "bus_list_filter_master when you need only one group."
        ),
        help="Fetch bus tour filter options and tour counts",
    ),
    Action(
        domain="bus",
        tool="bus_list_district_groups",
        title="Maitabi: list bus area and district groups",
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
        domain="bus",
        tool="bus_search_tours",
        title="Maitabi: search mountain bus tours",
        command="search-tours",
        input_model=SearchBusToursInput,
        service=search_tours_service,
        endpoint="GET /tour_search",
        doc=(
            "Search mountain bus tours and lodge packages on Maitabi (bus.maitabi.jp) with detailed "
            "filter criteria.\n\n"
            "Returns the search envelope: count (upstream total, before the price and availability "
            "filters), page, items with course_no, title, date, price in JPY, status and detail_url, "
            "and the query actually sent. Pass course_no to bus_get_tour_detail for the itinerary."
        ),
        help="Search mountain bus tours with filters",
    ),
    Action(
        domain="bus",
        tool="bus_get_tour_detail",
        title="Maitabi: bus tour detail",
        command="get-tour-detail",
        input_model=GetBusTourDetailInput,
        service=get_tour_detail_service,
        endpoint="GET /tour_detail",
        doc=(
            "Fetch detailed information, schedule, pricing, and bus stops for a specific Maitabi "
            "mountain bus tour by course_no.\n\n"
            "Returns the detail object for a single course_no (itinerary, bus stops, seat options, "
            "pricing, lodging), or the batch envelope with page: null when course_no is a list; an "
            "item in that list can carry its own error."
        ),
        help="Fetch bus tour detail by course_no",
    ),
    Action(
        domain="general",
        tool="general_search_tours",
        title="Maitabi: search general tours",
        command="search-tours",
        input_model=SearchGeneralToursInput,
        service=search_general_tours_service,
        endpoint="GET /category_search",
        doc=(
            "Search general travel tours and mountain climbing packages on www.maitabi.jp.\n\n"
            "Returns the search envelope: count (upstream total), page, items with course_no, title, "
            "date, price in JPY, a numeric status (1/2 bookable, 3 closed) and detail_url, plus the "
            "query actually sent. Capped at 60 requests/min per IP."
        ),
        help="Search general tours on www.maitabi.jp",
    ),
    Action(
        domain="general",
        tool="general_get_tour_detail",
        title="Maitabi: general tour detail",
        command="get-tour-detail",
        input_model=GetGeneralTourDetailInput,
        service=get_general_tour_detail_service,
        endpoint="GET /detail.php?courseNo={course_no}",
        doc=(
            "Fetch the full page for one general tour on www.maitabi.jp: day-by-day itinerary, travel "
            "conditions (minimum participants, tour conductor, meals), every departure date with price "
            "and booking status, the full description, and the booking link.\n\n"
            "www.maitabi.jp publishes no detail API, so this reads the rendered detail page: the tour "
            "record comes from the page's embedded JSON and the three tables from its markup. One "
            "object per single course_no, an envelope for a list. Capped at 60 requests/min per IP."
        ),
        help="Fetch general tour detail by courseNo",
    ),
    Action(
        domain="bus",
        tool="bus_list_filter_master",
        title="Maitabi: list one filter master list",
        command="list-filter-master",
        input_model=ListFilterMasterInput,
        service=list_filter_master_service,
        endpoint="GET /{kind}",
        doc=(
            "Fetch one cascading master list for mountain bus tours: tour styles, bus seat types, return-day "
            "options, or area/district groups.\n\n"
            "Same data as bus_list_filters but one group at a time, with a much smaller payload. Counts stay "
            "filter-aware: they reflect the other filters passed in, so ids with tour_count 0 are unavailable "
            "for that combination."
        ),
        help="Fetch one master list (style, bus_sheet, return_day, district)",
    ),
    Action(
        domain="general",
        tool="general_get_calendar",
        title="Maitabi: monthly departure calendar",
        command="get-calendar",
        input_model=GetTourCalendarInput,
        service=get_tour_calendar_service,
        endpoint="GET /calendar/{year}/{month}",
        doc=(
            "Fetch monthly departure calendar and tour schedule matrix on www.maitabi.jp for a given "
            "year and month.\n\n"
            "Returns the daily departure matrix with tour availability. Use it to see which days have "
            "departures before searching a range; narrow with travel_type because the full matrix is "
            "large. Capped at 60 requests/min per IP."
        ),
        help="Fetch monthly departure calendar matrix",
    ),
)

DOMAINS: tuple[str, ...] = ("bus", "general")
ACTION_BY_KEY = {(action.domain, action.command): action for action in ACTIONS}
ACTION_BY_TOOL = {action.tool: action for action in ACTIONS}
