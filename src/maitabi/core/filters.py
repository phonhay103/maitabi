"""Result post-processing shared by bus and general search services.

These helpers run on upstream payloads AFTER the HTTP call: price-range
filtering, availability filtering, and `detail_url` enrichment. They keep the
exact wire semantics that both the MCP tools and the CLI expose.
"""

from datetime import datetime

from maitabi.config import MAIN_BASE, WEB_BASE

# Upstream statuses that mean "not bookable" per domain.
#
# bus.maitabi.jp reports Japanese strings; www.maitabi.jp reports numbers where
# 1 = maru-double, 2 = maru, 3 = batsu (closed). Only the explicit closed values
# code must never make an existing tour disappear from results.
BUS_CLOSED_STATUSES: tuple[object, ...] = ("満席", "受付終了", "")
GENERAL_CLOSED_STATUSES: tuple[object, ...] = (3,)


def parse_price_jpy(raw: object) -> int | None:
    """Parse an upstream price string ('15,500円~') into an int, or None.

    Upstream prices carry ',' thousands separators, the 円 suffix, and a
    trailing fullwidth tilde (\uff5e) for ranges. Unparseable values yield None
    (never 0) so callers can distinguish "no price" from a real zero.
    """
    cleaned = str(raw).replace(",", "").replace("円", "").replace("\uff5e", "").strip()
    return int(cleaned) if cleaned.isdigit() else None


def within_price_range(price_jpy: int | None, min_price: int | None, max_price: int | None) -> bool:
    """True when price fits [min_price, max_price]. Unknown price (None) always fits."""
    if price_jpy is None:
        return True
    if min_price is not None and price_jpy < min_price:
        return False
    return not (max_price is not None and price_jpy > max_price)


def is_open_status(status: object, closed_statuses: tuple[object, ...]) -> bool:
    """True when an upstream status (string or numeric code) is still bookable."""
    return status not in closed_statuses


def derive_bus_detail_url(course_no: int | str, date_str: str, fallback_month: int | None = None) -> str:
    """Build the bus.maitabi.jp detail link, deriving year/month from the date field.

    Upstream `date` looks like '2026年09月12日(土)'. When it can't be parsed,
    fall back to the current year and the search month (or current month).
    """
    now = datetime.now()
    year, month = now.year, fallback_month or now.month
    if "年" in date_str and "月" in date_str:
        parts = date_str.split("年")
        if len(parts) == 2:
            y_str = parts[0]
            m_str = parts[1].split("月")[0]
            if y_str.isdigit() and m_str.isdigit():
                year, month = int(y_str), int(m_str)
    return f"{WEB_BASE}/detail.html?course_no={course_no}&year={year}&month={month}"


def derive_general_detail_url(course_no: int | str) -> str:
    """Build the www.maitabi.jp detail link (no date derivation needed)."""
    return f"{MAIN_BASE}/detail.php?courseNo={course_no}"
