---
name: maitabi-bus-extractor
description: Extract mountain bus tour, alpine trekking, and general tour data from Maitabi (bus.maitabi.jp & www.maitabi.jp) using only raw HTTP requests (curl or any HTTP client). No MCP server, no CLI, no Python package required. Supports filter modeling, REST endpoint querying, and standardized JSON output.
---

# Maitabi Bus Extractor Skill

## 1. Overview

This skill works with **plain HTTP only**. You build URL query strings, issue `GET` requests with `curl` (or any HTTP client in any language), and parse the JSON responses. Nothing to install — no MCP client, no `maitabi` CLI, no Python package.

> Need a different interface? The `maitabi-cli` skill covers the `maitabi` terminal command and the `maitabi-mcp` skill covers MCP client tools. This skill is standalone and does not depend on either.

## 2. 3-Layer Architecture

### Layer 1: `build_query(filters)`
- Convert user filters into exact URL query parameters (see §4).
- `month` (1-12) is required by the backend — always include it to avoid HTTP 500.

### Layer 2: `fetch_list(query)`
- `GET` the endpoints in §5 with `curl -L -s` (follow redirects).
- Two base hosts:
  - `https://api.bus.maitabi.jp` — mountain bus tours (毎日あるぺん号).
  - `https://www.maitabi.jp/api/v1` — general travel/trekking tours (毎日新聞旅行).

### Layer 3: `parse_list(payload)`
- Responses are JSON. Normalize each item to:
  - `course_no`/`courseNo`, `course_cd`/`courseCd`, `title`/`courseName`, `date`/`saikouDate`, `price`, `status`/`saikouStatus`, plus pagination (`count`, `page`, `param`/`data`).
- www items nest the presentable fields under `tTravel` and report statuses as numbers (`1`/`2` bookable, `3` closed), unlike the bus domain's Japanese strings.
- Append `detail_url` yourself:
  - Bus: `https://bus.maitabi.jp/detail.html?course_no={course_no}&year={YYYY}&month={M}` (derive YYYY/MM from the `date` field, e.g. `2026年09月12日(土)` → year=2026, month=9).
  - General: `https://www.maitabi.jp/detail.php?courseNo={courseNo}`.
- Post-filter client-side when needed: price range (strip `,`/`円`/`～` then compare ints), availability (drop `満席`, `受付終了`, `キャンセル待ち`, `催行中止`, empty).

## 3. Domains & Travel Categories

| Domain | Host | `travel_type` |
|--------|------|---------------|
| Mountain Bus (毎日あるぺん号) | `api.bus.maitabi.jp` / `bus.maitabi.jp` | 3 |
| Domestic Mountain (国内登山・トレッキング) | `www.maitabi.jp` | 1 |
| Domestic Travel (国内旅行・ハイキング) | `www.maitabi.jp` | 2 |
| Overseas Mountain (海外登山・トレッキング) | `www.maitabi.jp` | 4 |
| Overseas Travel (海外旅行) | `www.maitabi.jp` | 5 |

## 4. Filter Schema

### Mountain bus query params (`api.bus.maitabi.jp`)

```
departure={1|2|3}&month={1..12}&day={1..31}&area={id}&style={1..7}&return_day={1..5}&bus_sheet={1..6}&stay1={id}&stay2={id}&stay3={id}&course_cd={code}&keyword={text}&page={N}
```

| Param | Meaning / values |
| :--- | :--- |
| `departure` | `1`=東京 Tokyo, `2`=大阪・京都 Osaka/Kyoto, `3`=名古屋 Nagoya |
| `month` | `1`-`12` — **required** |
| `day` | `1`-`31` (one request per day; fan out for ranges) |
| `area` | Area ID (`0`=All, `18`=立山（室堂）, `10`=上高地, …) |
| `style` | `1`=Round-trip bus, `2`=Outbound, `3`=Inbound, `4`=Round-trip+lodge, `5`=Outbound+lodge, `6`=Night bus (夜行日帰り/往復夜行), `7`=Taxi |
| `return_day` | `1`=1 day after … `5`=5 days after |
| `bus_sheet` | `1`=Standard, `2`=Premium, `3`=Outbound Premium/Inbound Standard, `4`=Outbound Standard/Inbound Premium, `5`=Double, `6`=Taxi |
| `stay1/2/3` | Mountain lodge IDs |
| `course_cd` | Course code (e.g. `S104C21`) |
| `keyword` | Japanese keyword (e.g. `立山`, URL-encode it) |
| `page` | Page number (1-based) |

### General tour query params (`www.maitabi.jp/api/v1/category_search`)

```
travelType={1..5}&keyword={text}&startDateYearMonthMin={YYYY-MM}&startDateDayMin={D}&page={N}&listOrder={order}&categoryNos1[]={id}&...&categoryNos5[]={id}
```

`listOrder`: `startDateAsc`, `saikouStatus`, `yoyakuStatus`, `priceAsc`, `priceDesc`. `categoryNos1-5`: repeatable subcategory IDs (style/duration, difficulty, departure region, themes, guides).

## 5. Endpoints & cURL

### `GET /tour_course` — bus filter options + counts

```bash
curl -L -s 'https://api.bus.maitabi.jp/tour_course?departure=1&month=8'
curl -L -s 'https://api.bus.maitabi.jp/tour_course?departure=1&month=8&day=10&area=18'
```

### `GET /district_group` — area groups + counts

```bash
curl -L -s 'https://api.bus.maitabi.jp/district_group?departure=1&month=8'
```

### `GET /tour_search` — search bus tours

```bash
curl -L -s 'https://api.bus.maitabi.jp/tour_search?departure=1&month=8&area=18&page=1'
curl -L -s 'https://api.bus.maitabi.jp/tour_search?departure=1&month=8&style=6&return_day=1&page=1'
```

### `GET /tour_detail` — mountain-bus tour detail (bus courses only)

```bash
curl -L -s 'https://api.bus.maitabi.jp/tour_detail?course_no=14241'
```

Bus courses only. A www course number (e.g. 25461) returns HTTP 500 with a Laravel `Undefined offset: 0` page — there is no JSON detail endpoint for general tours.

### `GET /{kind}` — one master list (style, bus_sheet, return_day, district)

```bash
# kind = style | bus_sheet | return_day | district
curl -L -s 'https://api.bus.maitabi.jp/district?departure=1&month=11&area=18'
```

Returns `{"pulldown_options": {"<kind>": [{"id", "name", "tour_count"}]}, "param": {...}}`.
Same data as `/tour_course`, one group at a time and a much smaller payload. Counts are filter-aware: `tour_count: 0` means that id has no tours under the other filters you sent.

### `GET /detail.php?courseNo={n}` — general tour detail (HTML, no API)

www.maitabi.jp has no detail endpoint; the page is the only source, and it is more structured than it looks:

```bash
curl -L -s 'https://www.maitabi.jp/detail.php?courseNo=25461'
```

1. It embeds the tour record as a JS literal, identical in shape to a `category_search` item:

   ```js
   const detailData = {"details":[{ "courseNo":25461, "tTravel":{ "point":"…description…" }, ... }]}
   ```

   Extract it with a JSON parser starting right after `const detailData = ` (use a raw JSON decoder; do not regex the object). This gives title, description, price, statuses, lodges.
2. Three `<table>` elements carry the rest — itinerary (`日 / 予定`), travel conditions (`日数 / 旅行条件 / 食事条件 / その他 / 出発地 / 旅行代金 / ホテル / 旅行目的`), and departures (`出発日 / 旅行代金 / 催行状況 / 予約状況 / 予約受付`). Match columns by their Japanese header text, never by position — column order is not guaranteed.
3. The monthly calendar under the departures table is rendered client-side (jsrender) from `/api/v1/calendar/{year}/{month}`; the page itself only ships the template.

### `GET /api/v1/category_search` — search general tours

```bash
curl -L -s 'https://www.maitabi.jp/api/v1/category_search?travelType=1&keyword=%E7%AB%8B%E5%B1%B1&startDateYearMonthMin=2026-08&page=1'
```

### `GET /api/v1/calendar/{year}/{month}` — monthly matrix

```bash
curl -L -s 'https://www.maitabi.jp/api/v1/calendar/2026/8?travelType=1'
```

### Rate limits

- `www.maitabi.jp` endpoints are capped at **60 requests/min per IP** (see `x-ratelimit-limit` / `x-ratelimit-remaining` response headers). Over the cap you get HTTP 200 with body `{"errors": {"code": 0, "message": "Too Many Attempts."}}` — wait ~60s and re-run the request manually. Fanning out one request per day for large ranges hits the cap fast, so keep ranges narrow.
- `api.bus.maitabi.jp` endpoints show no rate-limit headers at normal usage levels.

## 6. Standard output

Normalize every extraction to:

```json
{
  "count": 23,
  "page": "1",
  "tour": [{ "travel_type": 3, "course_cd": "S104C21", "course_no": 14241, "date": "2026年09月12日(土)", "title": "...", "tour_day": "1日", "price": "15,500円", "status": "受付中", "phone_reserve": 0, "detail_url": "https://bus.maitabi.jp/detail.html?course_no=14241&year=2026&month=9" }],
  "param": { "departure": "1", "page": "1", "month": "9", "day": "12" }
}
```

## 7. Reference

Full ID tables (departure/area/style/return-day/seat/lodges): [filter-mapping.md](references/filter-mapping.md).
