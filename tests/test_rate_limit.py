"""Tests for www.maitabi.jp rate-limit detection — fully mocked, no network."""

import pytest
import respx
from httpx import Response

from maitabi.core.errors import RATE_LIMIT_ERROR
from maitabi.core.inputs import GetTourCalendarInput, SearchGeneralToursInput
from maitabi.services.general import (
    get_tour_calendar_service,
    search_general_tours_service,
)

THROTTLE_BODY = {"errors": {"code": 0, "message": "Too Many Attempts."}}


@respx.mock
@pytest.mark.asyncio
async def test_calendar_throttle_returns_clear_error():
    respx.get(url__regex=r"https://www\.maitabi\.jp/api/v1/calendar/.*").mock(
        return_value=Response(200, json=THROTTLE_BODY)
    )
    out = await get_tour_calendar_service(GetTourCalendarInput(year=2026, month=8))
    assert out["error"] == RATE_LIMIT_ERROR
    assert out["detail"] == "Too Many Attempts."
    assert "retry_hint" in out


@respx.mock
@pytest.mark.asyncio
async def test_search_throttle_fails_fast_on_batch():
    route = respx.get(url__regex=r"https://www\.maitabi\.jp/api/v1/category_search.*")
    route.mock(
        side_effect=[
            Response(200, json={"data": [{"courseNo": 1}]}),
            Response(200, json=THROTTLE_BODY),
        ]
    )
    out = await search_general_tours_service(SearchGeneralToursInput(day="14-15"))
    assert out["error"] == RATE_LIMIT_ERROR


@respx.mock
@pytest.mark.asyncio
async def test_normal_body_passes_through():
    respx.get(url__regex=r"https://www\.maitabi\.jp/api/v1/calendar/.*").mock(
        return_value=Response(200, json={"data": {"days": []}})
    )
    out = await get_tour_calendar_service(GetTourCalendarInput(year=2026, month=8))
    assert "error" not in out
    assert out["data"] == {"days": []}
