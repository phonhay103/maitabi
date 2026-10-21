---
name: maitabi-cli
description: Use the `maitabi` CLI to search mountain bus tours, general trekking tours, and departure calendars from Maitabi (bus.maitabi.jp & www.maitabi.jp). Use when the user wants terminal commands, shell scripts, or JSON piped to jq — no MCP client or raw HTTP needed.
---

# Maitabi CLI Skill

Use the `maitabi` command-line tool. It shares the same core as the MCP server, so results match MCP tool outputs. Output is JSON on stdout.

## 1. Install

```bash
# PyPI (default distribution includes MCP + CLI)
pip install maitabi-mcp-server
# or isolated envs
uvx maitabi --help
uv tool install maitabi-mcp-server && maitabi --help

# Docker (image contains both entrypoints)
docker pull phonhay103/maitabi-mcp-server:latest
docker run -i --rm phonhay103/maitabi-mcp-server:latest --help            # MCP entrypoint help
docker run -i --rm --entrypoint maitabi phonhay103/maitabi-mcp-server:latest --help  # CLI help
```

## 2. Global flags

Every subcommand accepts:

| Flag | Effect |
|------|--------|
| `--pretty` | Pretty-print JSON (indent=2) |
| `--output FILE` | Write JSON to FILE instead of stdout |

## 3. Commands (7, mirror MCP tools)

### `list-filters` — bus filter options + tour counts

```bash
maitabi list-filters --departure 1 --month 8 --pretty
maitabi list-filters --departure 1 --month 8 --day 10 --area 18
```

Flags: `--departure 1|2|3` (default 1), `--month 1-12`, `--day 'D|list|range'`, `--area ID`, `--style 1-7`, `--return-day 1-5`, `--bus-sheet 1-6`, `--stay1/2/3 ID`, `--course-cd CODE`, `--keyword TEXT`.

### `list-district-groups` — area groups + counts

```bash
maitabi list-district-groups --departure 1 --month 8 --pretty
```

Same filter flags as `list-filters`.

### `search-tours` — search mountain bus tours

```bash
maitabi search-tours --departure 1 --month 8 --area 18 --page 1 --pretty
maitabi search-tours --departure 1 --month 8 --day '14-16, 20' --max-price 20000 --require-available-seats
maitabi search-tours --departure 1 --month 8 --style 6 --return-day 1 --bus-sheet 1 --keyword '立山'
```

Extra flags: `--page N` (default 1), `--min-price JPY`, `--max-price JPY`, `--require-available-seats`.

### `get-tour-detail` — bus tour detail by course_no

```bash
maitabi get-tour-detail --course-no 14241 --pretty
maitabi get-tour-detail --course-no 14241,8518 --output details.json
```

### `search-general-tours` — general tours on www.maitabi.jp

```bash
maitabi search-general-tours --travel-type 1 --keyword '富士山' --year-month 2026-08 --pretty
maitabi search-general-tours --travel-type 1 --day '14-16, 20' --list-order priceAsc --category-nos3 '13,15'
```

Flags: `--travel-type 1-5` (default 1), `--keyword`, `--year-month YYYY-MM`, `--day`, `--page`, `--min-price`, `--max-price`, `--require-available-seats`, `--list-order startDateAsc|saikouStatus|yoyakuStatus|priceAsc|priceDesc`, `--category-nos1..5 'ID,ID'`.

### `get-general-tour-detail` — general tour detail

```bash
maitabi get-general-tour-detail --course-no 1723 --pretty
```

### `get-tour-calendar` — monthly departure matrix

```bash
maitabi get-tour-calendar --year 2026 --month 8 --pretty
maitabi get-tour-calendar --year 2026 --month 8 --travel-type 1
```

## 4. Output

JSON on stdout, same shape as MCP tools:

```json
{
  "count": 23,
  "page": "1",
  "tour": [{ "course_no": 14241, "course_cd": "S104C21", "date": "2026年09月12日(土)", "title": "...", "price": "15,500円", "status": "受付中", "detail_url": "https://bus.maitabi.jp/detail.html?course_no=14241&year=2026&month=9" }],
  "param": { "departure": "1", "page": "1", "month": "9" }
}
```

Pipe tips: `maitabi search-tours ... --output tours.json`, `maitabi search-tours ... | jq '.tour[] | {course_no, date, price, status}'`.

## 5. Filter ID reference

See `references/filter-mapping.md` for departure/area/style/return-day/seat/lodge ID tables.

## 6. Troubleshooting

- `maitabi: command not found` → reinstall (`pip install maitabi-mcp-server`) or use `uvx maitabi ...` / `python -m maitabi_mcp_server.cli ...`.
- Empty `tour: []` → widen filters (drop `--day`/`--area`/price caps) or check `--month` (backend requires month).
- Network errors appear as `{"error": ..., "detail": ...}` JSON — retry, don't change filters.
- `{"error": "Rate limited by www.maitabi.jp (60 requests/min per IP)", ...}` → `search-general-tours` and `get-tour-calendar` are capped at 60 req/min per IP. Wait ~60s and retry manually, e.g. `sleep 60 && maitabi get-tour-calendar --year 2026 --month 8`. Large `--day` ranges fan out into parallel requests and hit the cap faster.
