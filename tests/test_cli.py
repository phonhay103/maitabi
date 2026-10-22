"""Tests for the `maitabi` CLI parser — no network access."""

import pytest

from maitabi.cli.parser import build_parser


def _group(name: str):
    parser = build_parser()
    domains = next(a for a in parser._actions if a.dest == "domain")
    return domains.choices[name]


def _commands(domain: str) -> set[str]:
    commands = next(a for a in _group(domain)._actions if a.dest == "command")
    return set(commands.choices)


def test_domains_are_bus_general_and_mcp():
    parser = build_parser()
    domains = next(a for a in parser._actions if a.dest == "domain")
    assert set(domains.choices) == {"bus", "general", "mcp"}


def test_bus_commands():
    assert _commands("bus") == {
        "list-filters",
        "list-district-groups",
        "search-tours",
        "get-tour-detail",
    }


def test_general_commands():
    assert _commands("general") == {"search-tours", "get-tour-detail", "get-calendar"}


def test_search_tours_flags():
    args = build_parser().parse_args(
        [
            "bus",
            "search-tours",
            "--departure",
            "1",
            "--month",
            "8",
            "--area",
            "18",
            "--day",
            "14-16, 20",
            "--max-price",
            "20000",
            "--require-available-seats",
        ]
    )
    assert (args.domain, args.command) == ("bus", "search-tours")
    assert args.departure == 1
    assert args.month == 8
    assert args.area == 18
    assert args.day == "14-16, 20"
    assert args.max_price == 20000
    assert args.require_available_seats is True


def test_kebab_case_maps_to_snake_dest():
    args = build_parser().parse_args(
        ["bus", "search-tours", "--return-day", "1", "--bus-sheet", "2", "--course-cd", "S104C21"]
    )
    assert args.return_day == 1
    assert args.bus_sheet == 2
    assert args.course_cd == "S104C21"


def test_get_tour_detail_requires_course_no():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["bus", "get-tour-detail"])
    args = build_parser().parse_args(["bus", "get-tour-detail", "--course-no", "14241,8518"])
    assert args.course_no == "14241,8518"


def test_general_tours_category_flags():
    args = build_parser().parse_args(
        [
            "general",
            "search-tours",
            "--travel-type",
            "1",
            "--year-month",
            "2026-08",
            "--category-nos3",
            "13,15",
            "--list-order",
            "priceAsc",
        ]
    )
    assert (args.domain, args.command) == ("general", "search-tours")
    assert args.travel_type == 1
    assert args.year_month == "2026-08"
    assert args.category_nos3 == "13,15"
    assert args.list_order == "priceAsc"


def test_calendar_requires_year_month():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["general", "get-calendar", "--year", "2026"])
    args = build_parser().parse_args(["general", "get-calendar", "--year", "2026", "--month", "8"])
    assert (args.year, args.month) == (2026, 8)


def test_mcp_subcommand_takes_transport_flags():
    args = build_parser().parse_args(["mcp", "--transport", "streamable-http", "--port", "9000"])
    assert (args.domain, args.transport, args.port) == ("mcp", "streamable-http", 9000)
