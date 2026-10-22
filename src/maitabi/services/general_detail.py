"""Detail service for general tours (www.maitabi.jp).

www.maitabi.jp exposes no tour-detail API: `api/v1` only serves
`category_search` and `calendar/{year}/{month}`, and `api.bus.maitabi.jp`
only knows mountain-bus courses. The detail page is therefore the only source,
and it is read in two well-defined steps:

1. the page embeds the tour record as a JSON literal
   (`const detailData = {"details": [...]}`) whose item has exactly the
   `category_search` shape — reused verbatim via `normalize_item()`;
2. three <table> elements carry the itinerary, the travel conditions, and the
   departure/price matrix — parsed by Japanese column header, never by position.

No prose is scraped: titles, description, price and statuses come from the
JSON. If the embedded record disappears the service fails loudly instead of
returning a hollow object.
"""

import json
import re
from typing import Any

from maitabi.core.envelope import envelope, query_of
from maitabi.core.filters import derive_general_detail_url, parse_price_jpy
from maitabi.core.inputs import GetGeneralTourDetailInput
from maitabi.services.general import normalize_item
from maitabi.services.html_tables import Cell, Table, extract_tables, find_key_value_table, find_table
from maitabi.services.http import gather_limited, get_html

_DETAIL_DATA_RE = re.compile(r"const\s+detailData\s*=\s*")
_DATE_RE = re.compile(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日")

# The same core keys every search item exposes, in the order they should print.
_CORE_KEYS = ("course_no", "course_cd", "title", "date", "price", "status", "detail_url")


class DetailLayoutError(Exception):
    """The page no longer carries the structure this parser depends on."""


def _to_int(raw: object) -> int | None:
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return None


def _extract_detail_data(html: str) -> dict[str, Any]:
    """The embedded tour record (`detailData.details[0]`)."""
    match = _DETAIL_DATA_RE.search(html)
    if not match:
        raise DetailLayoutError("embedded `const detailData` JSON not found")
    try:
        payload, _ = json.JSONDecoder().raw_decode(html, match.end())
    except json.JSONDecodeError as e:  # pragma: no cover - defensive
        raise DetailLayoutError(f"embedded `detailData` is not valid JSON: {e}") from e
    details = payload.get("details") if isinstance(payload, dict) else None
    if not isinstance(details, list) or not details or not isinstance(details[0], dict):
        raise DetailLayoutError("embedded `detailData.details[0]` is missing")
    return details[0]


def _parse_itinerary(tables: list[Table]) -> list[dict[str, Any]] | None:
    """Day-by-day schedule: the `日 / 予定` table."""
    table = find_table(tables, "日", "予定")
    if table is None:
        return None
    days: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for row in table.rows:
        if not row:
            continue
        if row[0].tag == "th":
            current = {
                "day": _to_int(row[0].clean()),
                "schedule": row[1].clean() if len(row) > 1 else "",
                "lodging": "",
            }
            days.append(current)
            continue
        # Continuation row: "宿泊 :<lodging>" (empty for day trips).
        match = re.match(r"宿泊\s*[\uff1a:]\s*(.*)", row[0].clean())
        if match and current is not None:
            current["lodging"] = match.group(1).strip()
    return days


def _flag(raw: str) -> bool | None:
    """`あり`/`なし` → True/False; anything else stays unknown."""
    if raw == "あり":
        return True
    if raw == "なし":
        return False
    return None


def _parse_conditions(tables: list[Table]) -> dict[str, Any] | None:
    """`日数 / 旅行条件 / 食事条件 / その他` key-value table."""
    table = find_key_value_table(tables, "旅行条件", "食事条件")
    if table is None:
        return None
    cells: dict[str, Cell] = {row[0].clean(): row[1] for row in table.rows if len(row) >= 2 and row[0].tag == "th"}

    def text(label: str) -> str | None:
        cell = cells.get(label)
        return cell.clean() if cell else None

    conditions = text("旅行条件") or ""
    meals_text = text("食事条件") or ""

    def meal(label: str) -> int | None:
        match = re.search(rf"{label}\s*[\uff1a:]\s*(\d+)\s*回", meals_text)
        return int(match.group(1)) if match else None

    def field_value(label: str) -> str | None:
        match = re.search(rf"{label}\s*[\uff1a:]\s*([^\s/\uff0f]+)", conditions)
        if match is None:
            return None
        return str(match.group(1))

    min_match = re.search(r"最少催行人数\s*[\uff1a:]\s*(\d+)\s*人", conditions)
    purposes = cells["旅行目的"].spans if "旅行目的" in cells else []

    return {
        "duration": text("日数"),
        "min_participants": int(min_match.group(1)) if min_match else None,
        "tour_conductor": _flag(field_value("添乗員") or ""),
        "local_staff": _flag(field_value("現地係員") or ""),
        "meals": {
            "breakfast": meal("朝食"),
            "lunch": meal("昼食"),
            "dinner": meal("夕食"),
        },
        "departure_area": text("出発地"),
        "price_label": text("旅行代金"),
        "hotel": text("ホテル"),
        "purposes": purposes,
        "notes": text("その他"),
    }


def _parse_departures(tables: list[Table]) -> list[dict[str, Any]] | None:
    """Departure/price matrix: `出発日 / 旅行代金 / 催行状況 / 予約状況 / 予約受付`."""
    table = find_table(tables, "出発日", "旅行代金")
    if table is None:
        return None
    departures: list[dict[str, Any]] = []
    for row in table.rows:
        date_cell = table.cell(row, "出発日")
        if date_cell is None:
            continue
        price_cell = table.cell(row, "旅行代金")
        status_cell = table.cell(row, "催行状況")
        booking_cell = table.cell(row, "予約状況")
        action_cell = table.cell(row, "予約受付")
        label = date_cell.clean()
        match = _DATE_RE.search(label)
        iso_date = f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}" if match else None
        price_label = price_cell.clean() if price_cell else None
        departures.append(
            {
                "date": iso_date,
                "date_label": label,
                "price": parse_price_jpy(price_label) if price_label is not None else None,
                "price_label": price_label,
                "departure_status": status_cell.clean() if status_cell else None,
                "booking_status": booking_cell.clean() if booking_cell else None,
                "booking_url": action_cell.links[0] if action_cell and action_cell.links else None,
            }
        )
    return departures


def parse_detail_page(html: str) -> dict[str, Any]:
    """Turn one `detail.php` page into the documented detail object."""
    record = normalize_item(_extract_detail_data(html))
    # Core keys first so `maitabi ... --pretty` reads top-down; the upstream
    # keys stay alongside, never replaced.
    item: dict[str, Any] = {key: record[key] for key in _CORE_KEYS if key in record}
    item.update({key: value for key, value in record.items() if key not in item})
    tables = extract_tables(html)

    warnings: list[str] = []
    itinerary = _parse_itinerary(tables)
    if itinerary is None:
        warnings.append("itinerary table not found")
    conditions = _parse_conditions(tables)
    if conditions is None:
        warnings.append("conditions table not found")
    departures = _parse_departures(tables)
    if departures is None:
        warnings.append("departure table not found")

    travel = item.get("tTravel") or {}
    item["description"] = travel.get("point") or None
    item["itinerary"] = itinerary
    item["conditions"] = conditions
    item["departures"] = departures
    denwa = _to_int(item.get("denwaStatus"))
    item["phone_reservation"] = None if denwa is None else denwa == 1
    course_no = item.get("course_no")
    item["source_url"] = derive_general_detail_url(course_no) if isinstance(course_no, (int, str)) else None
    if warnings:
        item["warnings"] = warnings
    return item


async def _fetch_detail(course_no: int) -> dict[str, Any]:
    """Fetch and parse one detail page; never raises."""
    url = derive_general_detail_url(course_no)
    page = await get_html(url)
    if not isinstance(page, str):
        return page
    try:
        return parse_detail_page(page)
    except DetailLayoutError as e:
        return {
            "error": "Could not read the general tour detail page",
            "detail": f"{e} ({url})",
            "source_url": url,
        }


async def get_general_tour_detail_service(input: GetGeneralTourDetailInput) -> dict[str, Any]:
    """Fetch complete details for one general tour, or many as an envelope."""
    if isinstance(input.course_no, list):
        results = await gather_limited(_fetch_detail, input.course_no)
        return envelope(items=results, count=len(results), page=None, query=query_of(input))
    return await _fetch_detail(input.course_no)
