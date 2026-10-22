---
name: maitabi-mcp
description: Search Maitabi mountain bus tours, trekking tours, and departure calendars using already-connected MCP tools (bus_list_filters, bus_list_filter_master, bus_search_tours, bus_get_tour_detail, general_search_tours, general_get_tour_detail, general_get_calendar). Use when the user asks about bus departures, lodge packages, trekking itineraries, prices, availability, or course numbers.
---

# Maitabi MCP Skill

The 7 Maitabi tools below are already available in the MCP client. This skill tells you which tool to call, in what order, and how to read the results. Tool names are domain-prefixed: `bus_*` reads `api.bus.maitabi.jp`, `general_*` reads `www.maitabi.jp`.

## When to use

Use this skill when the user asks about mountain bus departures (`bus.maitabi.jp`), lodge packages, guided trekking tours (`www.maitabi.jp`), departure calendars, prices, live availability, or tour details by `course_no`.

## When NOT to use

- Terminal commands or shell scripts → `maitabi-cli` skill.
- Raw HTTP / curl extraction → `maitabi-bus-extractor` skill.

## 1. Tools (8)

### Mountain bus (`api.bus.maitabi.jp`)

- **`bus_list_filters`** — filter dropdown options, lodges, tour counts. Cascading: counts update with other filters. Args: `departure` (1=Tokyo, 2=Osaka/Kyoto, 3=Nagoya), `month` 1-12, `day`, `area`, `style` 1-7, `return_day` 1-5, `bus_sheet` 1-6, `stay1/2/3`, `course_cd`, `keyword`.
- **`bus_list_district_groups`** — area/district groups + counts. Same args as `bus_list_filters`.
- **`bus_list_filter_master`** — one master list only (`kind`: `style` | `bus_sheet` | `return_day` | `district`), same filters, much smaller payload than `bus_list_filters`.
- **`bus_search_tours`** — search bus tours + lodge packages. Same filters plus `day` as int/list/range string (e.g. `'14-16, 20'`), `page`, `min_price`/`max_price` (JPY), `require_available_seats` (drops 満席/受付終了).
- **`bus_get_tour_detail`** — full itinerary/schedule/pricing by `course_no` (int or list for batch).

### General tours (`www.maitabi.jp`)

- **`general_search_tours`** — categories `travel_type`: 1=Domestic Mountain, 2=Domestic Travel, 3=Mountain Bus, 4=Overseas Mountain, 5=Overseas Travel. Args: `keyword`, `year_month` (`YYYY-MM`), `day`, `page`, `min_price`/`max_price`, `require_available_seats`, `list_order` (`startDateAsc`, `saikouStatus`, `yoyakuStatus`, `priceAsc`, `priceDesc`), `category_nos1-5` (lists).
- **`general_get_tour_detail`** — full page by `course_no` (int or list): `description`, `itinerary[]`, `conditions{min_participants, tour_conductor, local_staff, meals, …}`, `departures[{date, price, departure_status, booking_status, booking_url}]` plus `phone_reservation` and `source_url`.
- **`general_get_calendar`** — monthly departure matrix for `year`/`month`, optional `travel_type`.

## 2. Typical flows

1. Discover: `bus_list_filters` (departure+month) → pick `area`/`style` IDs.
2. Search: `bus_search_tours` or `general_search_tours` with `require_available_seats=true` when the user wants bookable tours.
3. Detail: `*_get_tour_detail` with `course_no` from results.
4. Calendar: `general_get_calendar` for a month overview before narrowing days.

## 3. Output

Search tools return one envelope; every item carries `detail_url`:

```json
{
  "count": 191,
  "page": 1,
  "items": [{ "course_no": 14241, "course_cd": "S104C21", "date": "2026年09月12日(土)", "title": "...", "price": "15,500円", "status": "受付中", "detail_url": "https://bus.maitabi.jp/detail.html?course_no=14241&year=2026&month=9" }],
  "query": { "departure": 1, "month": 9, "page": 1 }
}
```

Rules worth knowing:

- `count` is the upstream total for the query, **before** the client-side price/availability filters — `items` can be shorter on the current page.
- `count`/`page` are `null` when upstream does not report them; `items` is always a list.
- Batch detail (`course_no` as a list) returns the same envelope with `page: null`.
- Single detail, filter options, and the calendar return their own objects, not an envelope.
- `status` is domain-native: Japanese string for bus, numeric code for general (1/2 bookable, 3 closed).
- `bus_list_filter_master` returns `{kind, options, query}`; `tour_count: 0` means that id is unavailable under the current filters.
- `general_get_tour_detail` returns a single object, not an envelope. www.maitabi.jp has no detail API, so it reads the rendered page; `warnings` names any missing table, and `error` + `source_url` means the layout changed.

## 4. Filter ID reference

See `references/filter-mapping.md` for departure/area/style/return-day/seat/lodge ID tables.

## 5. Troubleshooting

- Empty `items` → widen filters; `month` is required by the backend (defaults to current month).
- `{"error": ...}` payload → upstream/network issue, retry before changing filters.
- `{"error": "Rate limited by www.maitabi.jp (60 requests/min per IP)", ...}` → `general_*` tools are capped at 60 req/min per IP. Wait ~60s and retry manually — do not change filters. Large `day` ranges fan out into parallel requests and hit the cap faster, so prefer narrow day ranges.
