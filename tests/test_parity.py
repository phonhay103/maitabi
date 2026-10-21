"""Parity contract: MCP tools <-> CLI subcommands <-> core services.

Guards the "Must-Match" invariant mechanically: adding/removing/renaming an
action in one layer without the others fails here instead of drifting silently.
No network access.
"""

import asyncio

from maitabi_mcp_server.cli.parser import build_parser
from maitabi_mcp_server.mcp.server import mcp
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

# action -> (mcp_tool, cli_subcommand, service callable)
EXPECTED_ACTIONS = {
    "list_filters": ("list_filters", "list-filters", list_filters_service),
    "list_district_groups": (
        "list_district_groups",
        "list-district-groups",
        list_district_groups_service,
    ),
    "search_tours": ("search_tours", "search-tours", search_tours_service),
    "get_tour_detail": ("get_tour_detail", "get-tour-detail", get_tour_detail_service),
    "search_general_tours": (
        "search_general_tours",
        "search-general-tours",
        search_general_tours_service,
    ),
    "get_general_tour_detail": (
        "get_general_tour_detail",
        "get-general-tour-detail",
        get_general_tour_detail_service,
    ),
    "get_tour_calendar": ("get_tour_calendar", "get-tour-calendar", get_tour_calendar_service),
}


def _mcp_tool_names() -> set[str]:
    return set(asyncio.run(_list_tool_names()))


async def _list_tool_names() -> set[str]:
    tools = await mcp.list_tools()
    return {t.name for t in tools}


def _cli_subcommands() -> set[str]:
    parser = build_parser()
    action = next(a for a in parser._actions if a.dest == "command")
    return set(action.choices)


def test_mcp_tools_match_expected():
    assert _mcp_tool_names() == {mcp_tool for mcp_tool, _, _ in EXPECTED_ACTIONS.values()}


def test_cli_subcommands_match_expected():
    assert _cli_subcommands() == {sub for _, sub, _ in EXPECTED_ACTIONS.values()}


def test_mcp_cli_names_stay_in_sync():
    """Every MCP snake_case tool has a matching kebab_case CLI subcommand."""
    mcp_tools = _mcp_tool_names()
    cli_subs = _cli_subcommands()
    for tool in mcp_tools:
        assert tool.replace("_", "-") in cli_subs, f"MCP tool {tool} has no CLI subcommand"
    for sub in cli_subs:
        assert sub.replace("-", "_") in mcp_tools, f"CLI subcommand {sub} has no MCP tool"
