---
name: maitabi-mcp
description: Search Maitabi mountain bus tours, trekking tours, and departure calendars using already-connected MCP tools (list_filters, search_tours, get_tour_detail, search_general_tours, get_general_tour_detail, get_tour_calendar). Use when the user asks about bus departures, lodge packages, trekking itineraries, prices, availability, or course numbers.
---

# Maitabi MCP Skill

The 7 Maitabi tools below are already available in the MCP client. This skill tells you which tool to call, in what order, and how to read the results.

## When to use

Use this skill when the user asks about mountain bus departures (`bus.maitabi.jp`), lodge packages, guided trekking tours (`www.maitabi.jp`), departure calendars, prices, live availability, or tour details by `course_no`.

## When NOT to use

- Terminal commands or shell scripts → `maitabi-cli` skill.
- Raw HTTP / curl extraction → `maitabi-bus-extractor` skill.

## 1. Tools (7)

### Mountain bus (`bus.maitabi.jp`)

- **`list_filters`** — filter dropdown options, lodges, tour counts. Cascading: counts update with other filters. Args: `departure` (1=Tokyo, 2=Osaka/Kyoto, 3=Nagoya), `month` 1-12, `day`, `area`, `style` 1-7, `return_day` 1-5, `bus_sheet` 1-6, `stay1/2/3`, `course_cd`, `keyword`.
- **`list_district_groups`** — area/district groups + counts. Same args as `list_filters`.
- **`search_tours`** — search bus tours + lodge packages. Same filters plus `day` as int/list/range string (e.g. `'14-16, 20'`), `page`, `min_price`/`max_price` (JPY), `require_available_seats` (drops 満席/受付終了).
- **`get_tour_detail`** — full itinerary/schedule/pricing by `course_no` (int or list for batch).

### General tours (`www.maitabi.jp`)

- **`search_general_tours`** — categories `travel_type`: 1=Domestic Mountain, 2=Domestic Travel, 3=Mountain Bus, 4=Overseas Mountain, 5=Overseas Travel. Args: `keyword`, `year_month` (`YYYY-MM`), `day`, `page`, `min_price`/`max_price`, `require_available_seats`, `list_order` (`startDateAsc`, `saikouStatus`, `yoyakuStatus`, `priceAsc`, `priceDesc`), `category_nos1-5` (lists).
- **`get_general_tour_detail`** — itinerary/meals/guide/booking by `course_no` (int or list).
- **`get_tour_calendar`** — monthly departure matrix for `year`/`month`, optional `travel_type`.

## 2. Typical flows

1. Discover: `list_filters` (departure+month) → pick `area`/`style` IDs.
2. Search: `search_tours` (bus) or `search_general_tours` (trekking) with `require_available_seats=true` when user wants bookable tours.
3. Detail: `get_tour_detail` / `get_general_tour_detail` with `course_no` from results.
4. Calendar: `get_tour_calendar` for month overview before narrowing days.

## 3. Output

Tools return JSON strings with `detail_url` links included:

```json
{
  "count": 23,
  "page": "1",
  "tour": [{ "course_no": 14241, "course_cd": "S104C21", "date": "2026年09月12日(土)", "title": "...", "price": "15,500円", "status": "受付中", "detail_url": "https://bus.maitabi.jp/detail.html?course_no=14241&year=2026&month=9" }],
  "param": { "departure": "1", "page": "1", "month": "9" }
}
```

Done when the payload has `count`/`tour`/`param` (or the detail fields for `get_*_detail`).

## 4. Filter ID reference

See `references/filter-mapping.md` for departure/area/style/return-day/seat/lodge ID tables.

## 5. Troubleshooting

- Empty results → widen filters; `month` is required by backend (defaults to current month).
- `{"error": ...}` payload → upstream/network issue, retry before changing filters.
- `{"error": "Rate limited by www.maitabi.jp (60 requests/min per IP)", ...}` → general tools (`search_general_tours`, `get_tour_calendar`) are capped at 60 req/min per IP. Wait ~60s and retry manually — do not change filters. Large `day` ranges fan out into parallel requests and hit the cap faster, so prefer narrow day ranges.
