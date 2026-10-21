"""MCP tools for general Mainichi Travel tours and calendar schedule.

Thin wrappers: exact tool signatures define the public MCP schema; each tool
maps args → Input model → service → JSON string. No business logic here.
"""

import json
from typing import Annotated, Optional
from pydantic import Field

from maitabi_mcp_server.core.enums import TravelType
from maitabi_mcp_server.core.inputs import (
    GetGeneralTourDetailInput,
    GetTourCalendarInput,
    SearchGeneralToursInput,
)
from maitabi_mcp_server.services.general import (
    get_general_tour_detail_service,
    get_tour_calendar_service,
    search_general_tours_service,
)


def _dumps(data: dict) -> str:
    """Serialize a service dict to the public JSON wire format."""
    return json.dumps(data, ensure_ascii=False, indent=2)


def register_general_tools(mcp) -> None:
    """Register general tour and calendar tools with FastMCP instance."""

    @mcp.tool()
    async def search_general_tours(
        travel_type: Annotated[
            TravelType,
            Field(
                description="Category ID: 1=Domestic Mountain (default), 2=Domestic Travel, 3=Mountain Bus, 4=Overseas Mountain, 5=Overseas Travel"
            ),
        ] = TravelType.DOMESTIC_MOUNTAIN,
        keyword: Annotated[
            Optional[str],
            Field(
                min_length=1,
                max_length=100,
                description="Search keyword in Japanese (e.g., '富士山', '京都')",
            ),
        ] = None,
        year_month: Annotated[
            Optional[str],
            Field(
                pattern=r"^\d{4}-(?:0[1-9]|1[0-2])$",
                description="Departure year-month string in 'YYYY-MM' format (e.g., '2026-08')",
            ),
        ] = None,
        day: Annotated[
            Optional[int | list[int] | str],
            Field(description="Departure day of month (1-31). Can be a single int, a list of ints, or a string range (e.g., '14-16, 20')."),
        ] = None,
        page: Annotated[int, Field(ge=1, description="Page number (1-based)")] = 1,
        min_price: Annotated[
            Optional[int],
            Field(description="Minimum price in JPY (e.g., 10000). Filters the results before returning."),
        ] = None,
        max_price: Annotated[
            Optional[int],
            Field(description="Maximum price in JPY (e.g., 50000). Filters the results before returning."),
        ] = None,
        require_available_seats: Annotated[
            bool,
            Field(description="If True, filters out full/closed tours (満席, 受付終了)."),
        ] = False,
        list_order: Annotated[
            Optional[str],
            Field(
                description="Sort order: 'startDateAsc' (departure earliest), 'saikouStatus' (departure status), 'yoyakuStatus' (availability), 'priceAsc' (price low to high), 'priceDesc' (price high to low)"
            ),
        ] = None,
        category_nos1: Annotated[
            Optional[list[int]],
            Field(
                description="Subcategory Nos for Style/Duration (e.g. [36] for Day trip, [259] for Overnight)"
            ),
        ] = None,
        category_nos2: Annotated[
            Optional[list[int]],
            Field(
                description="Subcategory Nos for Difficulty/Shoes (e.g. [363] for Grade 1 / Introduction)"
            ),
        ] = None,
        category_nos3: Annotated[
            Optional[list[int]],
            Field(
                description="Subcategory Nos for Departure Region (e.g. [13] for Kanto, [15] for Tokai)"
            ),
        ] = None,
        category_nos4: Annotated[
            Optional[list[int]],
            Field(
                description="Subcategory Nos for Themes/Tours"
            ),
        ] = None,
        category_nos5: Annotated[
            Optional[list[int]],
            Field(
                description="Subcategory Nos for Guides"
            ),
        ] = None,
    ) -> str:
        """Search general travel tours and mountain climbing packages on www.maitabi.jp.

        Returns a JSON string containing matching tours, total count, pagination, sorting, and categories.
        """
        input_data = SearchGeneralToursInput(
            travel_type=travel_type,
            keyword=keyword,
            year_month=year_month,
            day=day,
            min_price=min_price,
            max_price=max_price,
            require_available_seats=require_available_seats,
            page=page,
            list_order=list_order,
            category_nos1=category_nos1,
            category_nos2=category_nos2,
            category_nos3=category_nos3,
            category_nos4=category_nos4,
            category_nos5=category_nos5,
        )
        return _dumps(await search_general_tours_service(input_data))

    @mcp.tool()
    async def get_general_tour_detail(
        course_no: Annotated[
            int | list[int],
            Field(
                description="Tour course number(s) on www.maitabi.jp (e.g., 1723, 24865). Can be a single int or list of ints for batch fetching.",
            ),
        ],
    ) -> str:
        """Fetch complete details, itinerary, pricing, and booking information for a general tour on www.maitabi.jp.

        Returns a JSON string containing tour itinerary, meal conditions, price matrix, lodging, and booking links.
        """
        return _dumps(
            await get_general_tour_detail_service(
                GetGeneralTourDetailInput(course_no=course_no)
            )
        )

    @mcp.tool()
    async def get_tour_calendar(
        year: Annotated[
            int, Field(ge=2000, le=2100, description="Year (e.g., 2026)")
        ],
        month: Annotated[int, Field(ge=1, le=12, description="Month (1-12)")],
        travel_type: Annotated[
            Optional[TravelType],
            Field(
                description="Optional category ID filter: 1=Domestic Mountain, 2=Domestic Travel, 3=Mountain Bus, 4=Overseas Mountain, 5=Overseas Travel"
            ),
        ] = None,
    ) -> str:
        """Fetch monthly departure calendar and tour schedule matrix on www.maitabi.jp for a given year and month.

        Returns a JSON string with daily departure schedule matrix, tour availability, and calendar dates.
        """
        return _dumps(
            await get_tour_calendar_service(
                GetTourCalendarInput(year=year, month=month, travel_type=travel_type)
            )
        )
