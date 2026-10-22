"""Tests for the `maitabi` CLI parser — no network access."""

from maitabi_mcp_server.cli.parser import build_parser


def test_all_seven_subcommands_exist():
    parser = build_parser()
    actions = next(a for a in parser._actions if a.dest == "command")
    assert set(actions.choices) == {
        "list-filters",
        "list-district-groups",
        "search-tours",
        "get-tour-detail",
        "search-general-tours",
        "get-general-tour-detail",
        "get-tour-calendar",
    }


def test_search_tours_flags():
    args = build_parser().parse_args(
        [
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
    assert args.departure == 1
    assert args.month == 8
    assert args.area == 18
    assert args.day == "14-16, 20"
    assert args.max_price == 20000
    assert args.require_available_seats is True


def test_kebab_case_maps_to_snake_dest():
    args = build_parser().parse_args(
        ["search-tours", "--return-day", "1", "--bus-sheet", "2", "--course-cd", "S104C21"]
    )
    assert args.return_day == 1
    assert args.bus_sheet == 2
    assert args.course_cd == "S104C21"


def test_get_tour_detail_requires_course_no():
    import pytest

    with pytest.raises(SystemExit):
        build_parser().parse_args(["get-tour-detail"])
    args = build_parser().parse_args(["get-tour-detail", "--course-no", "14241,8518"])
    assert args.course_no == "14241,8518"


def test_general_tours_category_flags():
    args = build_parser().parse_args(
        [
            "search-general-tours",
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
    assert args.travel_type == 1
    assert args.year_month == "2026-08"
    assert args.category_nos3 == "13,15"
    assert args.list_order == "priceAsc"


def test_calendar_requires_year_month():
    import pytest

    with pytest.raises(SystemExit):
        build_parser().parse_args(["get-tour-calendar", "--year", "2026"])
    args = build_parser().parse_args(["get-tour-calendar", "--year", "2026", "--month", "8"])
    assert (args.year, args.month) == (2026, 8)
