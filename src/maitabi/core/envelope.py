"""The uniform result envelope shared by every search/collection endpoint.

Contract (stable since 1.0.0 — additive changes only):

- `count`: total matches across all pages, or null when upstream does not say.
  Never `len(items)`, which would silently become wrong once pagination bites.
- `page`: the requested page, or null for endpoints that do not paginate.
- `items`: always a list, empty rather than absent.
- `query`: the parameters actually sent, typed (ints stay ints).

Single-resource endpoints (tour detail, filter options, calendar matrix) return
their own object instead of an envelope: a list of one would only add a level
of indexing without adding information. Errors are always
`{"error", "detail", "retry_hint"?}`.
"""

from enum import IntEnum
from typing import Any

from pydantic import BaseModel

from maitabi.core.days import parse_days


def as_int(value: object) -> int | None:
    """Coerce an upstream numeric string to int, or None when it is not one."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def dict_items(raw: object) -> list[dict[str, Any]]:
    """Coerce an upstream list into a list of dict items, dropping anything else."""
    return [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []


def query_of(model: BaseModel) -> dict[str, Any]:
    """The effective parameters of a request, typed and without empty values."""
    out: dict[str, Any] = {}
    for name, value in model.model_dump(exclude_none=True).items():
        if isinstance(value, IntEnum):
            value = int(value)
        if value is False or value in ("", [], {}):
            continue  # not sent upstream, so not part of the query
        out[name] = value
    if "day" in out:
        # Search models accept "14-16, 20"; report the days actually requested.
        days = parse_days(out["day"])
        if days is not None:
            out["day"] = days
    return out


def envelope(
    *,
    items: list[Any],
    count: int | None,
    page: int | None,
    query: dict[str, Any],
) -> dict[str, Any]:
    """Build the uniform result envelope."""
    return {"count": count, "page": page, "items": items, "query": query}
