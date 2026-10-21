"""MCP tools for Maitabi mountain bus tours.

Thin wrappers: exact tool signatures define the public MCP schema; each tool
maps args → Input model → service → JSON string. No business logic here.
"""

import json
from typing import Annotated, Optional
from pydantic import Field

from maitabi_mcp_server.core.enums import (
    BusSeatType,
    DeparturePoint,
    ReturnDayOption,
    TourStyle,
)
from maitabi_mcp_server.core.inputs import (
    GetBusTourDetailInput,
    ListDistrictGroupsInput,
    ListFiltersInput,
    SearchBusToursInput,
)
from maitabi_mcp_server.services.bus import (
    get_tour_detail_service,
    list_district_groups_service,
    list_filters_service,
    search_tours_service,
)


def _dumps(data: dict) -> str:
    """Serialize a service dict to the public JSON wire format."""
    return json.dumps(data, ensure_ascii=False, indent=2)


def register_bus_tools(mcp) -> None:
    """Register mountain bus tour tools with FastMCP instance."""

    @mcp.tool()
    async def list_filters(
        departure: Annotated[
            DeparturePoint,
            Field(
                description="Departure point: 1=Tokyo (Takebashi/Shinjuku), 2=Osaka/Kyoto, 3=Nagoya"
            ),
        ] = DeparturePoint.TOKYO,
        month: Annotated[
            Optional[int],
            Field(
                ge=1,
                le=12,
                description="Departure month (1-12). Defaults to current month if omitted.",
            ),
        ] = None,
        day: Annotated[
            Optional[int],
            Field(ge=1, le=31, description="Departure day (1-31)"),
        ] = None,
        area: Annotated[
            Optional[int],
            Field(
                ge=0,
                description="Area/direction ID (e.g., 18=Tateyama Murodo, 10=Kamikochi, 0=All)",
            ),
        ] = None,
        style: Annotated[
            Optional[TourStyle],
            Field(
                description="Tour style: 1=Round-trip bus, 2=Outbound bus, 3=Inbound bus, 4=Round-trip lodge, 5=Outbound lodge, 6=Overnight day-trip, 7=Taxi plan"
            ),
        ] = None,
        return_day: Annotated[
            Optional[ReturnDayOption],
            Field(
                description="Return date option: 1=1 day after departure, 2=2 days after, 3=3 days after, 4=4 days after, 5=5 days after"
            ),
        ] = None,
        bus_sheet: Annotated[
            Optional[BusSeatType],
            Field(
                description="Bus seat type: 1=Standard, 2=Premium, 3=Outbound Premium / Inbound Standard, 4=Outbound Standard / Inbound Premium, 5=Double seat, 6=Taxi"
            ),
        ] = None,
        stay1: Annotated[
            Optional[int],
            Field(
                ge=1,
                description="Mountain lodge ID for night 1 (e.g., 5=Enzanso, 2=Nishiho Sanso)",
            ),
        ] = None,
        stay2: Annotated[
            Optional[int],
            Field(ge=1, description="Mountain lodge ID for night 2"),
        ] = None,
        stay3: Annotated[
            Optional[int],
            Field(ge=1, description="Mountain lodge ID for night 3"),
        ] = None,
        course_cd: Annotated[
            Optional[str],
            Field(
                min_length=1,
                max_length=50,
                description="Maitabi course code (e.g., 'S104C21')",
            ),
        ] = None,
        keyword: Annotated[
            Optional[str],
            Field(
                min_length=1,
                max_length=100,
                description="Search keyword in Japanese (e.g., '立山', '上高地')",
            ),
        ] = None,
    ) -> str:
        """Fetch available filter dropdown options, departure areas, tour styles, mountain lodges, and tour counts for Maitabi bus tours.

        Supports cascading filtering—options and counts update dynamically based on other selected filters.
        """
        return _dumps(
            await list_filters_service(
                ListFiltersInput(
                    departure=departure,
                    month=month,
                    day=day,
                    area=area,
                    style=style,
                    return_day=return_day,
                    bus_sheet=bus_sheet,
                    stay1=stay1,
                    stay2=stay2,
                    stay3=stay3,
                    course_cd=course_cd,
                    keyword=keyword,
                )
            )
        )

    @mcp.tool()
    async def list_district_groups(
        departure: Annotated[
            DeparturePoint,
            Field(
                description="Departure point: 1=Tokyo (Takebashi/Shinjuku), 2=Osaka/Kyoto, 3=Nagoya"
            ),
        ] = DeparturePoint.TOKYO,
        month: Annotated[
            Optional[int],
            Field(
                ge=1,
                le=12,
                description="Departure month (1-12). Defaults to current month if omitted.",
            ),
        ] = None,
        day: Annotated[
            Optional[int],
            Field(ge=1, le=31, description="Departure day (1-31)"),
        ] = None,
        area: Annotated[
            Optional[int],
            Field(
                ge=0,
                description="Area/direction ID (e.g., 18=Tateyama Murodo, 10=Kamikochi, 0=All)",
            ),
        ] = None,
        style: Annotated[
            Optional[TourStyle],
            Field(
                description="Tour style: 1=Round-trip bus, 2=Outbound bus, 3=Inbound bus, 4=Round-trip lodge, 5=Outbound lodge, 6=Overnight day-trip, 7=Taxi plan"
            ),
        ] = None,
        return_day: Annotated[
            Optional[ReturnDayOption],
            Field(
                description="Return date option: 1=1 day after departure, 2=2 days after, 3=3 days after, 4=4 days after, 5=5 days after"
            ),
        ] = None,
        bus_sheet: Annotated[
            Optional[BusSeatType],
            Field(
                description="Bus seat type: 1=Standard, 2=Premium, 3=Outbound Premium / Inbound Standard, 4=Outbound Standard / Inbound Premium, 5=Double seat, 6=Taxi"
            ),
        ] = None,
        stay1: Annotated[
            Optional[int],
            Field(
                ge=1,
                description="Mountain lodge ID for night 1 (e.g., 5=Enzanso, 2=Nishiho Sanso)",
            ),
        ] = None,
        stay2: Annotated[
            Optional[int],
            Field(ge=1, description="Mountain lodge ID for night 2"),
        ] = None,
        stay3: Annotated[
            Optional[int],
            Field(ge=1, description="Mountain lodge ID for night 3"),
        ] = None,
        course_cd: Annotated[
            Optional[str],
            Field(
                min_length=1,
                max_length=50,
                description="Maitabi course code (e.g., 'S104C21')",
            ),
        ] = None,
        keyword: Annotated[
            Optional[str],
            Field(
                min_length=1,
                max_length=100,
                description="Search keyword in Japanese (e.g., '立山', '上高地')",
            ),
        ] = None,
    ) -> str:
        """Fetch mountain area/district groups and tour counts for Maitabi mountain bus tours.

        Supports cascading filtering—district groups and counts update dynamically based on other selected filters.
        """
        return _dumps(
            await list_district_groups_service(
                ListDistrictGroupsInput(
                    departure=departure,
                    month=month,
                    day=day,
                    area=area,
                    style=style,
                    return_day=return_day,
                    bus_sheet=bus_sheet,
                    stay1=stay1,
                    stay2=stay2,
                    stay3=stay3,
                    course_cd=course_cd,
                    keyword=keyword,
                )
            )
        )

    @mcp.tool()
    async def search_tours(
        departure: Annotated[
            DeparturePoint,
            Field(
                description="Departure point: 1=Tokyo (Takebashi/Shinjuku), 2=Osaka/Kyoto, 3=Nagoya"
            ),
        ] = DeparturePoint.TOKYO,
        month: Annotated[
            Optional[int],
            Field(ge=1, le=12, description="Departure month (1-12)"),
        ] = None,
        day: Annotated[
            Optional[int | list[int] | str],
            Field(description="Departure day (1-31). Can be a single int, a list of ints, or a string range (e.g., '14-16, 20')."),
        ] = None,
        area: Annotated[
            Optional[int],
            Field(
                ge=0,
                description="Area/direction ID (e.g., 18=Tateyama Murodo, 10=Kamikochi, 0=All)",
            ),
        ] = None,
        style: Annotated[
            Optional[TourStyle],
            Field(
                description="Tour style: 1=Round-trip bus, 2=Outbound bus, 3=Inbound bus, 4=Round-trip lodge, 5=Outbound lodge, 6=Overnight day-trip, 7=Taxi plan"
            ),
        ] = None,
        return_day: Annotated[
            Optional[ReturnDayOption],
            Field(
                description="Return date option: 1=1 day after departure, 2=2 days after, 3=3 days after, 4=4 days after, 5=5 days after"
            ),
        ] = None,
        bus_sheet: Annotated[
            Optional[BusSeatType],
            Field(
                description="Bus seat type: 1=Standard, 2=Premium, 3=Outbound Premium / Inbound Standard, 4=Outbound Standard / Inbound Premium, 5=Double seat, 6=Taxi"
            ),
        ] = None,
        stay1: Annotated[
            Optional[int],
            Field(
                ge=1,
                description="Mountain lodge ID for night 1 (e.g., 5=Enzanso, 2=Nishiho Sanso)",
            ),
        ] = None,
        stay2: Annotated[
            Optional[int],
            Field(ge=1, description="Mountain lodge ID for night 2"),
        ] = None,
        stay3: Annotated[
            Optional[int],
            Field(ge=1, description="Mountain lodge ID for night 3"),
        ] = None,
        course_cd: Annotated[
            Optional[str],
            Field(
                min_length=1,
                max_length=50,
                description="Maitabi course code (e.g., 'S104C21')",
            ),
        ] = None,
        keyword: Annotated[
            Optional[str],
            Field(
                min_length=1,
                max_length=100,
                description="Search keyword in Japanese (e.g., '立山', '上高地')",
            ),
        ] = None,
        min_price: Annotated[
            Optional[int],
            Field(description="Minimum price in JPY (e.g., 10000). Filters the results before returning."),
        ] = None,
        max_price: Annotated[
            Optional[int],
            Field(description="Maximum price in JPY (e.g., 20000). Filters the results before returning."),
        ] = None,
        require_available_seats: Annotated[
            bool,
            Field(default=False, description="If True, filters out full/closed tours (満席, 受付終了)."),
        ] = False,
        page: Annotated[
            int, Field(ge=1, description="Page number (1-based)")
        ] = 1,
    ) -> str:
        """Search mountain bus tours and lodge packages on Maitabi (bus.maitabi.jp) with detailed filter criteria.

        Returns a JSON string containing matching bus tours, seat options, pricing, departure dates, and course numbers.
        """
        input_data = SearchBusToursInput(
            departure=departure,
            month=month,
            day=day,
            area=area,
            style=style,
            return_day=return_day,
            bus_sheet=bus_sheet,
            stay1=stay1,
            stay2=stay2,
            stay3=stay3,
            min_price=min_price,
            course_cd=course_cd,
            keyword=keyword,
            max_price=max_price,
            require_available_seats=require_available_seats,
            page=page,
        )
        return _dumps(await search_tours_service(input_data))

    @mcp.tool()
    async def get_tour_detail(
        course_no: Annotated[
            int | list[int],
            Field(
                description="Internal course number(s) on bus.maitabi.jp (e.g., 14241, 8518). Can be a single int or list of ints for batch fetching.",
            ),
        ],
    ) -> str:
        """Fetch detailed information, schedule, pricing, and bus stops for a specific Maitabi mountain bus tour by course_no.

        Returns a JSON string containing complete tour itinerary, bus departure points, seat options, pricing, and lodging info.
        """
        return _dumps(
            await get_tour_detail_service(GetBusTourDetailInput(course_no=course_no))
        )
