---
name: maitabi-cli
description: Use the `maitabi` CLI to search mountain bus tours, general trekking tours, and departure calendars from Maitabi (bus.maitabi.jp & www.maitabi.jp). Use when the user wants terminal commands, shell scripts, or JSON piped to jq — no MCP client or raw HTTP needed.
---

# Maitabi CLI Skill

One command covers the whole site: `maitabi <bus|general> <command>`. Output is JSON on stdout. `maitabi mcp` starts the MCP server.

## 1. Install

```bash
uvx maitabi --help                 # no install, always the published version
uv tool install maitabi && maitabi --help
pip install maitabi                # inside a virtualenv

# Docker (CLI and MCP server share one image)
docker pull phonhay103/maitabi
docker run --rm phonhay103/maitabi --help                    # CLI
docker run -i --rm phonhay103/maitabi mcp                    # MCP server, stdio
```

## 2. Global flags

Every data subcommand accepts:

| Flag | Effect |
|------|--------|
| `--pretty` | Pretty-print JSON (indent=2) |
| `--output FILE` | Write JSON to FILE instead of stdout |

## 3. Commands

### `maitabi bus` — mountain bus tours (`api.bus.maitabi.jp`)

```bash
maitabi bus list-filters --departure 1 --month 8 --pretty
maitabi bus list-district-groups --departure 1 --month 8
maitabi bus list-filter-master --kind district --month 11   # one master list, small payload
maitabi bus list-filter-master --kind style --month 11 --area 18
maitabi bus search-tours --departure 1 --month 11 --area 18 --page 1 --pretty
maitabi bus search-tours --month 11 --day '14-16, 20' --max-price 20000 --require-available-seats
maitabi bus search-tours --month 12 --style 6 --return-day 1 --bus-sheet 1 --keyword '立山'
maitabi bus get-tour-detail --course-no 14241 --pretty
maitabi bus get-tour-detail --course-no 14241,8518 --output details.json
```

Flags: `--departure 1|2|3` (default 1), `--month 1-12`, `--day 'D|list|range'`, `--area ID`, `--style 1-7`, `--return-day 1-5`, `--bus-sheet 1-6`, `--stay1/2/3 ID`, `--course-cd CODE`, `--keyword TEXT`, `--page N`, `--min-price`, `--max-price`, `--require-available-seats`. `list-filter-master` adds the required `--kind style|bus_sheet|return_day|district`.

### `maitabi general` — tours & calendar (`www.maitabi.jp`)

```bash
maitabi general search-tours --travel-type 1 --keyword '富士山' --year-month 2026-11 --pretty
maitabi general search-tours --travel-type 1 --day '14-16, 20' --list-order priceAsc --category-nos3 '13,15'
maitabi general get-tour-detail --course-no 1723 --pretty
maitabi general get-calendar --year 2026 --month 11 --travel-type 1
```

Flags: `--travel-type 1-5` (default 1), `--keyword`, `--year-month YYYY-MM`, `--day`, `--page`, `--min-price`, `--max-price`, `--require-available-seats`, `--list-order startDateAsc|saikouStatus|yoyakuStatus|priceAsc|priceDesc`, `--category-nos1..5 'ID,ID'`.

### `maitabi mcp` — MCP server

```bash
maitabi mcp                                  # stdio (what MCP clients expect)
maitabi mcp --transport streamable-http --port 8000
```

## 4. Output

Search commands return one envelope:

```json
{
  "count": 191,
  "page": 1,
  "items": [{ "course_no": 14241, "course_cd": "S104C21", "date": "2026年09月12日(土)", "title": "...", "price": "15,500円", "status": "受付中", "detail_url": "https://bus.maitabi.jp/detail.html?course_no=14241&year=2026&month=9" }],
  "query": { "departure": 1, "month": 11, "page": 1 }
}
```

- `count` is the upstream total for the query, before client-side price/availability filters.
- `count`/`page` are `null` when upstream does not report them; `items` is always a list.
- Batch `get-tour-detail` returns the same envelope with `page: null`; a single course returns the detail object.
- `status` is domain-native: Japanese string for bus, numeric code for general (1/2 bookable, 3 closed).
- `list-filter-master` returns `{kind, options: [{id, name, tour_count}], query}`; `tour_count` is filter-aware, so `0` means unavailable for that combination.

`general get-tour-detail` returns one object (no envelope): core keys first, then the upstream record, then the parsed page:

```json
{
  "course_no": 25461,
  "title": "…",
  "description": "full tour description",
  "itinerary": [{"day": 1, "schedule": "…", "lodging": ""}],
  "conditions": {"duration": "0泊1日", "min_participants": 10, "tour_conductor": true,
                 "local_staff": true, "meals": {"breakfast": 0, "lunch": 0, "dinner": 0},
                 "departure_area": "関東", "purposes": ["現地発着ツアー"], "notes": "…"},
  "departures": [{"date": "2026-11-01", "price": 3776, "departure_status": "催行決定",
                  "booking_status": "受付中", "booking_url": "https://www.travel-answer.ne.jp/…"}],
  "phone_reservation": true,
  "source_url": "https://www.maitabi.jp/detail.php?courseNo=25461"
}
```

General detail comes from the rendered page (no API exists); a `warnings` array appears if a table was missing, and `error` + `source_url` if the layout changed.

Pipe tips:

```bash
maitabi bus search-tours --month 11 | jq '.items[] | {course_no, date, price, status}'
maitabi general search-tours --travel-type 1 | jq '.count, (.items | length)'
```

## 5. Filter ID reference

See `references/filter-mapping.md` for departure/area/style/return-day/seat/lodge ID tables.

## 6. Troubleshooting

- `maitabi: command not found` → `uv tool install maitabi`, or run `uvx maitabi ...`.
- Empty `items` → widen filters (drop `--day`/`--area`/price caps) or check `--month` (backend requires month).
- Network errors appear as `{"error": ..., "detail": ...}` JSON with exit code 1 — retry, don't change filters.
- `{"error": "Rate limited by www.maitabi.jp (60 requests/min per IP)", ...}` → `general` commands are capped at 60 req/min per IP. Wait ~60s and retry manually, e.g. `sleep 60 && maitabi general get-calendar --year 2026 --month 11`. Large `--day` ranges fan out into parallel requests and hit the cap faster.
