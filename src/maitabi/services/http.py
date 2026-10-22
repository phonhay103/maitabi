"""Shared HTTP client and request helper for Maitabi services.

One `get_json` handles both hosts: connection pooling, HTTP/network error
normalization, and www.maitabi.jp's HTTP-200 throttle-body detection.
"""

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, cast

import httpx

from maitabi.core.errors import (
    connection_error,
    is_rate_limited_body,
    rate_limit_error,
    upstream_http_error,
)

# Cap parallel per-day / per-course fan-out requests.
CONCURRENCY_LIMIT = 5

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Get or initialize the shared httpx.AsyncClient instance."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(15.0), follow_redirects=True)
    return _client


async def close_http_client() -> None:
    """Close the shared httpx.AsyncClient instance."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None


async def get_json(
    url: str,
    params: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
) -> dict[str, Any]:
    """GET `url`, parse JSON, and normalize every failure into an error payload.

    Never raises for upstream/network problems: errors come back as
    `{"error", "detail"[, "retry_hint"]}` dicts (see core/errors.py).
    www.maitabi.jp throttles with HTTP 200 + 'Too Many Attempts.' — surfaced
    clearly instead of passed through. No auto-retry.
    """
    client = get_http_client()
    try:
        # httpx keeps QueryParamTypes private; our mapping/sequence of pairs is
        # structurally what it accepts, so the cast is only to name that type.
        res = await client.get(url, params=cast(Any, params))
        res.raise_for_status()
        data = res.json()
    except httpx.HTTPStatusError as e:
        return upstream_http_error(e.response.status_code, str(e))
    except httpx.RequestError as e:
        return connection_error(str(e))
    if is_rate_limited_body(data):
        return rate_limit_error()
    return data


async def gather_limited[T, R](factory: Callable[[T], Awaitable[R]], items: Sequence[T]) -> list[R]:
    """Run `factory(item)` for each item with bounded concurrency, order kept.

    Used for per-day search fan-out and batch course_no fetching. `factory`
    takes one item and returns an awaited result (not a coroutine factory
    wrapping further params — see call sites).
    """
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def run_one(item: T) -> R:
        async with semaphore:
            return await factory(item)

    return await asyncio.gather(*(run_one(item) for item in items))
