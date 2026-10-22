"""Parity contract: MCP tools <-> CLI subcommands <-> core services.

Guards the "Must-Match" invariant mechanically: an MCP tool name is
`<domain>_<command-with-underscores>`, so adding/removing/renaming an action in
one layer without the others fails here instead of drifting silently.
No network access.
"""

import asyncio

from maitabi.cli.parser import build_parser
from maitabi.mcp.server import mcp
from maitabi.services.bus import (
    get_tour_detail_service,
    list_district_groups_service,
    list_filter_master_service,
    list_filters_service,
    search_tours_service,
)
from maitabi.services.general import get_tour_calendar_service, search_general_tours_service
from maitabi.services.general_detail import get_general_tour_detail_service

# (domain, cli command) -> (mcp_tool, service callable)
EXPECTED_ACTIONS = {
    ("bus", "list-filters"): ("bus_list_filters", list_filters_service),
    ("bus", "list-district-groups"): ("bus_list_district_groups", list_district_groups_service),
    ("bus", "search-tours"): ("bus_search_tours", search_tours_service),
    ("bus", "get-tour-detail"): ("bus_get_tour_detail", get_tour_detail_service),
    ("bus", "list-filter-master"): ("bus_list_filter_master", list_filter_master_service),
    ("general", "search-tours"): ("general_search_tours", search_general_tours_service),
    ("general", "get-tour-detail"): ("general_get_tour_detail", get_general_tour_detail_service),
    ("general", "get-calendar"): ("general_get_calendar", get_tour_calendar_service),
}


def _mcp_tool_names() -> set[str]:
    return set(asyncio.run(_list_tool_names()))


async def _list_tool_names() -> set[str]:
    tools = await mcp.list_tools()
    return {t.name for t in tools}


def _cli_commands() -> set[tuple[str, str]]:
    """Every (domain, command) pair the CLI exposes, excluding `mcp`."""
    parser = build_parser()
    domains = next(a for a in parser._actions if a.dest == "domain")
    pairs: set[tuple[str, str]] = set()
    for domain, group in domains.choices.items():
        if domain == "mcp":
            continue
        commands = next(a for a in group._actions if a.dest == "command")
        pairs.update((domain, command) for command in commands.choices)
    return pairs


def test_mcp_tools_match_expected():
    assert _mcp_tool_names() == {tool for tool, _ in EXPECTED_ACTIONS.values()}


def test_cli_commands_match_expected():
    assert _cli_commands() == set(EXPECTED_ACTIONS)


def test_mcp_names_are_domain_prefixed_cli_names():
    """MCP tool == "<domain>_" + command with dashes turned into underscores."""
    for tool in _mcp_tool_names():
        domain, _, rest = tool.partition("_")
        assert domain in {"bus", "general"}, f"tool {tool} has no domain prefix"
        assert (domain, rest.replace("_", "-")) in _cli_commands()


def test_mcp_server_is_reachable_from_the_cli():
    parser = build_parser()
    domains = next(a for a in parser._actions if a.dest == "domain")
    assert "mcp" in domains.choices
