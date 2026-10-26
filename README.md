# Maitabi (Python)

[![Hosted MCP server](https://img.shields.io/badge/MCP_server-online-2ea44f)](https://maitabi.fastmcp.app/mcp) [![Connect](https://img.shields.io/badge/connect-Horizon-6e56cf)](https://horizon.prefect.io/connect/eyJuYW1lIjoibWFpdGFiaSIsInRpdGxlIjoibWFpdGFiaSIsImRlc2NyaXB0aW9uIjoiIiwicmVtb3RlcyI6W3sidXJsIjoiaHR0cHM6Ly9tYWl0YWJpLmZhc3RtY3AuYXBwL21jcCIsInR5cGUiOiJodHRwIn1dfQ)

Search **Maitabi (まいたび — 毎日新聞旅行 / 毎日あるぺん号)** from one package: mountain bus tours (`bus.maitabi.jp`), general travel and trekking tours, and departure calendars (`www.maitabi.jp`). It ships as a CLI, an MCP server, and three agent skills — all driven by the same eight actions.

> Unofficial client. Not affiliated with 毎日新聞旅行.

| Interface | Use it when | Start with |
|---|---|---|
| **CLI** | you want commands, scripts, or JSON for `jq` | `uvx maitabi --help` |
| **MCP server** | you want the tools inside an MCP client | `uvx maitabi mcp` |
| **Hosted MCP** | you want the same tools without installing anything (OAuth) | <https://maitabi.fastmcp.app/mcp> |
| **Skills** | you want an agent to know the workflows | `npx skills add phonhay103/maitabi -g` |

## Install

```bash
uv tool install maitabi     # installs the `maitabi` command on your PATH
uv tool upgrade maitabi     # later, to update it
maitabi --version           # confirm which version is running
```

Nothing installed? `uvx maitabi ...` runs the same published version on demand, e.g. `uvx maitabi bus search-tours --month 11`.

## Quick start (CLI)

```bash
# Mountain bus tours
maitabi bus search-tours --month 11 --area 18 --pretty

# General trekking tours
maitabi general search-tours --travel-type 1 --keyword '富士山' --year-month 2026-11

# One tour in full
maitabi bus get-tour-detail --course-no 14241

# Monthly departure matrix
maitabi general get-calendar --year 2026 --month 11 --travel-type 1
```

Every data command accepts `--pretty` and `--output FILE`.

## Output contract

Search commands return one envelope; every item carries a `detail_url`:

```json
{
  "count": 191,
  "page": 1,
  "items": [
    {
      "course_no": 14241,
      "course_cd": "S104C21",
      "date": "2026年09月12日(土)",
      "title": "立山室堂ライン往復ツアー",
      "price": "15,500円",
      "status": "受付中",
      "detail_url": "https://bus.maitabi.jp/detail.html?course_no=14241&year=2026&month=9"
    }
  ],
  "query": { "departure": 1, "month": 11, "page": 1 }
}
```

- `count` is the upstream total for the query, **before** the client-side price/availability filters; `items` can be shorter on the current page.
- `count` and `page` are `null` when upstream does not report them; `items` is always a list.
- Batch detail (`--course-no 14241,8518`) returns the same envelope with `page: null`; a single course returns the detail object itself.
- Filter options, district groups, and the calendar return their own objects — a list of one would add indexing without information.
- `status` is domain-native: a Japanese string for bus, a numeric code for general (1/2 bookable, 3 closed).
- Errors are always `{"error": ..., "detail": ...}`, never a partial envelope.

The contract only grows: new fields appear, existing ones are never renamed or removed within a major version.

## Tools (8)

Full parameter reference (MCP args, CLI flags, defaults, endpoints): **[`docs/TOOL_CATALOG.md`](docs/TOOL_CATALOG.md)** — generated from the code, so it cannot drift.

### Mountain bus (`api.bus.maitabi.jp`)

| MCP tool | CLI | What it does |
|---|---|---|
| `bus_list_filters` | `maitabi bus list-filters` | filter options, lodges, tour counts (cascading) |
| `bus_list_district_groups` | `maitabi bus list-district-groups` | area/district groups + counts |
| `bus_list_filter_master` | `maitabi bus list-filter-master` | one master list (`--kind style\|bus_sheet\|return_day\|district`), small payload |
| `bus_search_tours` | `maitabi bus search-tours` | search tours and lodge packages |
| `bus_get_tour_detail` | `maitabi bus get-tour-detail` | full itinerary by `course_no` (single or batch) |

### General tours & calendar (`www.maitabi.jp`)

| MCP tool | CLI | What it does |
|---|---|---|
| `general_search_tours` | `maitabi general search-tours` | search by `travel_type` 1-5, keyword, dates, categories |
| `general_get_tour_detail` | `maitabi general get-tour-detail` | itinerary, conditions, every departure + booking link |
| `general_get_calendar` | `maitabi general get-calendar` | monthly departure matrix |

## One deliberate exception to "API only"

`www.maitabi.jp` publishes no tour-detail API — `api/v1` serves only `category_search` and `calendar/{year}/{month}`, and `api.bus.maitabi.jp` only knows mountain-bus courses. So `general_get_tour_detail` reads the rendered detail page, in a way that keeps the fragile surface small:

- the tour record itself (title, description, price, statuses) comes from a JSON literal the page embeds (`const detailData = {...}`), parsed as JSON — no prose is scraped;
- only three `<table>` elements are read from the markup: itinerary, travel conditions, and the departure/price matrix. Columns are matched by their Japanese headers, not by position.

If the page ever loses that structure the tool returns an error naming `source_url` instead of a hollow object, and the offline fixtures in `tests/fixtures/` fail first.

## MCP server

One executable, one subcommand. `mcp` speaks `stdio` by default, or `sse` / `streamable-http`:

```bash
uvx maitabi mcp                                  # stdio — what MCP clients expect
uvx maitabi mcp --transport streamable-http --port 8000
docker run -i --rm phonhay103/maitabi mcp        # same thing in a container
```

Client configuration (`mcpServers` key):

```json
{
  "mcpServers": {
    "maitabi": {
      "command": "uvx",
      "args": ["maitabi", "mcp"]
    }
  }
}
```

Docker variant:

```json
{
  "mcpServers": {
    "maitabi": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "phonhay103/maitabi:latest", "mcp"]
    }
  }
}
```

Local checkout, no install:

```json
{
  "mcpServers": {
    "maitabi": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/maitabi", "maitabi", "mcp"]
    }
  }
}
```

Tools are named `<domain>_<command>`: `bus_*` reads `api.bus.maitabi.jp`, `general_*` reads `www.maitabi.jp`.

Every tool is read-only (`readOnlyHint`, `idempotentHint`, `destructiveHint: false`), carries a `Maitabi: …` title, and returns its payload twice: the text block is the same JSON the CLI prints, and `structuredContent` is that object already parsed. A payload carrying `error` is reported as `isError: true` with the `retry_hint`, so a rate-limited call does not look like an empty result. The server also sends short `instructions` on `initialize`: the discovery → search → detail flow, the envelope shape, and the 60 req/min cap on `general_*`.

See [`CHANGELOG.md`](CHANGELOG.md) for what changed in each release, and [`evals/`](evals/) for the live evaluation suite that checks the tools are usable without the skills.

### Gemini (web app)

Add the hosted endpoint as a custom app at <https://gemini.google.com/customize/connectors> — Gemini runs the OAuth flow itself, so there is no client ID or secret to paste:

1. Open **Customize → Connectors**, or **Settings → Connected Apps → Custom apps** on the older UI. If the "Add a custom app" field is missing, switch the **Chat / Spark** toggle to Spark first.
2. **Add a custom app**, paste `https://maitabi.fastmcp.app/mcp`, click **Next**.
3. Approve the Google Account link, then sign in on the server's OAuth page.
4. In a Spark chat, type `@` and pick the app. Gemini asks permission for each tool call.

Google still limits custom apps to a personal Google Account (not work or school), 18+, US, English, Keep Activity on, and a plan that includes Gemini Spark.

### ChatGPT (web app)

Add the hosted endpoint as a plugin at <https://chatgpt.com/plugins> — the OAuth client registers itself, so any client ID or secret field stays empty:

1. Open **Plugins → + → Add custom MCP server** (some accounts still say **Create custom MCP server**; developer mode is no longer needed).
2. Name it `Maitabi`, then under **Connection → Server URL** paste `https://maitabi.fastmcp.app/mcp`.
3. Set **Authentication → OAuth**, tick "I understand and want to continue", and click **Create as a plugin**. ChatGPT reads the tool list from the server.
4. Install the plugin, start a chat, type `@` and pick it. Each write action asks for confirmation.

Custom MCP servers are created on the web only, and a work workspace can withhold the permission — on Business and Enterprise/Edu an admin owns that switch.

## Agent skills

```bash
npx skills add phonhay103/maitabi -g     # all three
npx skills add phonhay103/maitabi --list # inspect first
```

- **`maitabi-cli`** — terminal workflows and JSON piping.
- **`maitabi-mcp`** — how to call the already-connected tools: which tool, in what order, how to read results.
- **`maitabi-bus-extractor`** — raw HTTP/curl for both hosts, standalone. No CLI, no MCP.

## Rate limits

| Host | Limit | Applies to |
|---|---|---|
| `www.maitabi.jp` | 60 requests/min per IP | general tours + calendar |
| `api.bus.maitabi.jp` | none observed at normal usage | mountain bus tours |

When the cap is hit, the result is `{"error": "Rate limited by www.maitabi.jp ...", "retry_hint": "wait ~60s and retry manually"}`. There is no auto-retry. Narrow `--day` ranges help, since each day fans out into a parallel request (bounded at 5).

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Upstream/network error (payload contains `error`, incl. rate limiting) |
| 2 | Input error (bad flag value or failed validation) |

## Development

```bash
make install        # uv sync
make dev            # MCP server over stdio
make test           # offline suite (no network)
make smoke          # live check against the production API
make catalog        # regenerate docs/TOOL_CATALOG.md + skill reference copies
make catalog-check  # what CI runs — fails on stale generated files
make docker-build   # 2-stage image (Python 3.14)
make build          # wheel + sdist
```

Architecture, in one paragraph: parameters live once in `core/inputs.py`; endpoint logic lives in `services/`; `registry.py` declares one `Action` per capability (domain, MCP tool name, CLI command, input model, service, endpoint, docs); both adapters and the catalog are generated from that table, so the CLI, the MCP schema, and the documentation cannot disagree. See [`AGENTS.md`](AGENTS.md).

## Links

- PyPI: <https://pypi.org/project/maitabi/>
- Docker Hub: <https://hub.docker.com/r/phonhay103/maitabi>
- Source: <https://github.com/phonhay103/maitabi>
