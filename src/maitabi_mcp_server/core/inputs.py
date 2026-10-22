"""Pydantic input models — single source of truth for tool/CLI parameters.

Field descriptions here are the canonical MCP schema descriptions: the MCP
tools and the CLI parser are both generated from these models (see
`mcp/tools.py` and `cli/parser.py`), so editing a description or constraint
in this file updates every interface at once.
"""

from typing import Annotated

from pydantic import BaseModel, Field

from maitabi_mcp_server.core.enums import (
    BusSeatType,
    DeparturePoint,
    ReturnDayOption,
    TourStyle,
    TravelType,
)


class BusFilterBase(BaseModel):
    """Filter fields shared by every mountain-bus list/search input."""

    departure: Annotated[
        DeparturePoint,
        Field(
            default=DeparturePoint.TOKYO,
            description="Departure point: 1=Tokyo (Takebashi/Shinjuku), 2=Osaka/Kyoto, 3=Nagoya",
        ),
    ]
    month: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            le=12,
            description="Departure month (1-12). Defaults to current month if omitted.",
        ),
    ]
    day: Annotated[
        int | None,
        Field(default=None, ge=1, le=31, description="Departure day (1-31)"),
    ] = None
    area: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            description="Area/direction ID (e.g., 18=Tateyama Murodo, 10=Kamikochi, 0=All)",
        ),
    ] = None
    style: Annotated[
        TourStyle | None,
        Field(
            default=None,
            description="Tour style: 1=Round-trip bus, 2=Outbound bus, 3=Inbound bus, 4=Round-trip lodge, 5=Outbound lodge, 6=Overnight day-trip, 7=Taxi plan",
        ),
    ] = None
    return_day: Annotated[
        ReturnDayOption | None,
        Field(
            default=None,
            description="Return date option: 1=1 day after departure, 2=2 days after, 3=3 days after, 4=4 days after, 5=5 days after",
        ),
    ] = None
    bus_sheet: Annotated[
        BusSeatType | None,
        Field(
            default=None,
            description="Bus seat type: 1=Standard, 2=Premium, 3=Outbound Premium / Inbound Standard, 4=Outbound Standard / Inbound Premium, 5=Double seat, 6=Taxi",
        ),
    ] = None
    stay1: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            description="Mountain lodge ID for night 1 (e.g., 5=Enzanso, 2=Nishiho Sanso)",
        ),
    ] = None
    stay2: Annotated[
        int | None,
        Field(default=None, ge=1, description="Mountain lodge ID for night 2"),
    ] = None
    stay3: Annotated[
        int | None,
        Field(default=None, ge=1, description="Mountain lodge ID for night 3"),
    ] = None
    course_cd: Annotated[
        str | None,
        Field(
            default=None,
            min_length=1,
            max_length=50,
            description="Maitabi course code (e.g., 'S104C21')",
        ),
    ] = None
    keyword: Annotated[
        str | None,
        Field(
            default=None,
            min_length=1,
            max_length=100,
            description="Search keyword in Japanese (e.g., '立山', '上高地')",
        ),
    ] = None


class ListFiltersInput(BusFilterBase):
    """Input schema for fetching bus tour filter options."""

    # Inherits every shared filter field unchanged.


class ListDistrictGroupsInput(BusFilterBase):
    """Input schema for fetching mountain area/district groups."""

    # Inherits every shared filter field unchanged.


class SearchBusToursInput(BusFilterBase):
    """Input schema for searching mountain bus tours."""

    # month omits the "defaults to current month" note: the search endpoint
    # passes the month through untouched instead of substituting it.
    month: Annotated[
        int | None,
        Field(default=None, ge=1, le=12, description="Departure month (1-12)"),
    ]
    # day accepts int / list / range string; only search fans out per day, so
    # widening the inherited int-only field is deliberate.
    day: Annotated[  # ty: ignore[invalid-attribute-override]
        int | list[int] | str | None,
        Field(
            default=None,
            description="Departure day (1-31). Can be a single int, a list of ints, or a string range (e.g., '14-16, 20').",
        ),
    ] = None
    min_price: Annotated[
        int | None,
        Field(
            default=None,
            description="Minimum price in JPY (e.g., 10000). Filters the results before returning.",
        ),
    ] = None
    max_price: Annotated[
        int | None,
        Field(
            default=None,
            description="Maximum price in JPY (e.g., 20000). Filters the results before returning.",
        ),
    ] = None
    require_available_seats: Annotated[
        bool,
        Field(default=False, description="If True, filters out full/closed tours (満席, 受付終了)."),
    ] = False
    page: Annotated[int, Field(default=1, ge=1, description="Page number (1-based)")] = 1


class GetBusTourDetailInput(BaseModel):
    """Input schema for fetching bus tour detail by course number."""

    course_no: Annotated[
        int | list[int],
        Field(
            description="Internal course number(s) on bus.maitabi.jp (e.g., 14241, 8518). Can be a single int or list of ints for batch fetching.",
        ),
    ]


class SearchGeneralToursInput(BaseModel):
    """Input schema for searching general tours."""

    travel_type: Annotated[
        TravelType,
        Field(
            default=TravelType.DOMESTIC_MOUNTAIN,
            description="Category ID: 1=Domestic Mountain (default), 2=Domestic Travel, 3=Mountain Bus, 4=Overseas Mountain, 5=Overseas Travel",
        ),
    ]
    keyword: Annotated[
        str | None,
        Field(
            default=None,
            min_length=1,
            max_length=100,
            description="Search keyword in Japanese (e.g., '富士山', '京都')",
        ),
    ] = None
    year_month: Annotated[
        str | None,
        Field(
            default=None,
            pattern=r"^\d{4}-(?:0[1-9]|1[0-2])$",
            description="Departure year-month string in 'YYYY-MM' format (e.g., '2026-08')",
        ),
    ] = None
    day: Annotated[
        int | list[int] | str | None,
        Field(
            default=None,
            description="Departure day of month (1-31). Can be a single int, a list of ints, or a string range (e.g., '14-16, 20').",
        ),
    ] = None
    page: Annotated[int, Field(default=1, ge=1, description="Page number (1-based)")] = 1
    min_price: Annotated[
        int | None,
        Field(
            default=None,
            description="Minimum price in JPY (e.g., 10000). Filters the results before returning.",
        ),
    ] = None
    max_price: Annotated[
        int | None,
        Field(
            default=None,
            description="Maximum price in JPY (e.g., 50000). Filters the results before returning.",
        ),
    ] = None
    require_available_seats: Annotated[
        bool,
        Field(default=False, description="If True, filters out full/closed tours (満席, 受付終了)."),
    ] = False
    list_order: Annotated[
        str | None,
        Field(
            default=None,
            description="Sort order: 'startDateAsc' (departure earliest), 'saikouStatus' (departure status), 'yoyakuStatus' (availability), 'priceAsc' (price low to high), 'priceDesc' (price high to low)",
        ),
    ] = None
    category_nos1: Annotated[
        list[int] | None,
        Field(
            default=None,
            description="Subcategory Nos for Style/Duration (e.g. [36] for Day trip, [259] for Overnight)",
        ),
    ] = None
    category_nos2: Annotated[
        list[int] | None,
        Field(
            default=None,
            description="Subcategory Nos for Difficulty/Shoes (e.g. [363] for Grade 1 / Introduction)",
        ),
    ] = None
    category_nos3: Annotated[
        list[int] | None,
        Field(
            default=None,
            description="Subcategory Nos for Departure Region (e.g. [13] for Kanto, [15] for Tokai)",
        ),
    ] = None
    category_nos4: Annotated[
        list[int] | None,
        Field(
            default=None,
            description="Subcategory Nos for Themes/Tours",
        ),
    ] = None
    category_nos5: Annotated[
        list[int] | None,
        Field(
            default=None,
            description="Subcategory Nos for Guides",
        ),
    ] = None


class GetGeneralTourDetailInput(BaseModel):
    """Input schema for fetching general tour detail by course number."""

    course_no: Annotated[
        int | list[int],
        Field(
            description="Tour course number(s) on www.maitabi.jp (e.g., 1723, 24865). Can be a single int or list of ints for batch fetching.",
        ),
    ]


class GetTourCalendarInput(BaseModel):
    """Input schema for fetching tour schedule calendar."""

    year: Annotated[
        int,
        Field(ge=2000, le=2100, description="Year (e.g., 2026)"),
    ]
    month: Annotated[
        int,
        Field(ge=1, le=12, description="Month (1-12)"),
    ]
    travel_type: Annotated[
        TravelType | None,
        Field(
            default=None,
            description="Optional category ID filter: 1=Domestic Mountain, 2=Domestic Travel, 3=Mountain Bus, 4=Overseas Mountain, 5=Overseas Travel",
        ),
    ] = None
