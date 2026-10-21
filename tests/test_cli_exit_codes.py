"""CLI exit-code contract: 0 OK · 1 upstream/network error · 2 input error.

Fully mocked — no network. argparse rejects bad flags with 2 natively; the
command layer maps error payloads to 1 and validation failures to 2.
"""

import pytest
import respx
from httpx import Response

from maitabi_mcp_server.cli.main import main


@respx.mock
def test_success_returns_0(capsys):
    respx.get("https://api.bus.maitabi.jp/tour_search").mock(
        return_value=Response(200, json={"count": "0", "tour": [], "param": {}})
    )
    assert main(["search-tours", "--month", "9"]) == 0
    assert '"tour"' in capsys.readouterr().out


@respx.mock
def test_upstream_500_returns_1(capsys):
    respx.get("https://api.bus.maitabi.jp/tour_search").mock(
        return_value=Response(500, text="boom")
    )
    assert main(["search-tours", "--month", "9"]) == 1
    assert "Upstream service returned error: 500" in capsys.readouterr().out


@respx.mock
def test_rate_limit_returns_1():
    respx.get(url__regex=r"https://www\.maitabi\.jp/api/v1/category_search.*").mock(
        return_value=Response(200, json={"errors": {"message": "Too Many Attempts."}})
    )
    assert main(["search-general-tours"]) == 1


def test_model_validation_error_returns_2(capsys):
    # month=13 violates the model's le=12 — input error, no request made.
    assert main(["search-tours", "--month", "13"]) == 2
    assert "invalid arguments" in capsys.readouterr().err


def test_bad_csv_returns_2(capsys):
    assert main(["get-tour-detail", "--course-no", "abc"]) == 2
    assert "invalid arguments" in capsys.readouterr().err


def test_argparse_bad_flag_returns_2():
    # --day is typed int for list-filters; ranges are a search-tours feature.
    with pytest.raises(SystemExit) as exc:
        main(["list-filters", "--day", "14-16"])
    assert exc.value.code == 2


def test_missing_required_flag_returns_2():
    with pytest.raises(SystemExit) as exc:
        main(["get-tour-calendar", "--year", "2026"])
    assert exc.value.code == 2


def test_no_command_prints_help_and_returns_0(capsys):
    assert main([]) == 0
    assert "search-tours" in capsys.readouterr().out
