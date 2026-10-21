# Maitabi MCP Server (Python)

An MCP (Model Context Protocol) server written in Python using FastMCP for searching and extracting mountain bus tour, alpine trekking, and general tour information from **Maitabi (まいたび - 毎日新聞旅行 / 毎日あるぺん号)** (`www.maitabi.jp`, `bus.maitabi.jp`, & `api.bus.maitabi.jp`).

Docker Hub Repository: [phonhay103/maitabi-mcp-server](https://hub.docker.com/r/phonhay103/maitabi-mcp-server)

## Tools Provided

Full parameter reference (MCP args, CLI flags, defaults, endpoints): **[`docs/TOOL_CATALOG.md`](docs/TOOL_CATALOG.md)** (generated from code — always current).

### Mountain Bus Tours (毎日あるぺん号 - `bus.maitabi.jp`)
- `list_filters`: Fetch available filter options, departure areas, tour styles, mountain lodges, and tour counts for mountain bus tours.
- `list_district_groups`: Fetch area/district groups and tour counts for mountain bus tours.
- `search_tours`: Search mountain bus tours with full filter support (departure, month, day, area, style, return date, bus seat, lodges, keyword, course code).
- `get_tour_detail`: Fetch complete bus tour details, schedules, comments, and pricing by `course_no`.

### General Travel & Trekking Tours (毎日新聞旅行 - `www.maitabi.jp`)
- `search_general_tours`: Search general Mainichi Travel tours across categories (`travel_type`: 1=Domestic Mountain Climbing/Trekking, 2=Domestic Travel/Hiking, 3=Mountain Bus, 4=Overseas Mountain Climbing/Trekking, 5=Overseas Travel) with keyword, date, and pagination filters.
- `get_general_tour_detail`: Fetch complete tour details, itinerary, meal condition, guide info, points of interest, and booking links for general tours by `courseNo`.
- `get_tour_calendar`: Fetch monthly departure schedule calendar and tour matrix on `www.maitabi.jp` for a given year and month.

---

## 1. MCP Server Usage

The MCP server is a runtime exposing 7 tools over `stdio`, `SSE`, or Streamable HTTP. This section is the canonical setup reference (entrypoints, transports, client config). Agent tool-call workflows live in the `maitabi-mcp` skill, which assumes the server here is already connected.

### Running the Server

#### Option A: Zero-setup via `uvx`
```bash
# From PyPI (once published)
uvx maitabi-mcp-server

# Directly from Git repository
uvx --from git+https://github.com/phonhay103/maitabi-mcp-server.git maitabi-mcp-server
```

#### Option B: Via Docker Image
```bash
docker pull phonhay103/maitabi-mcp-server:latest
docker run -i --rm phonhay103/maitabi-mcp-server:latest
```

### Configuration for MCP Clients (setup reference)

Add the following to your MCP client settings. Pick the key format your client expects:

#### 1. `mcpServers` key format (stdio)

##### Via `uvx` (Recommended):
```json
{
  "mcpServers": {
    "maitabi-pypi": {
      "command": "uvx",
      "args": ["maitabi-mcp-server"]
    }
  }
}
```

##### Via Docker:
```json
{
  "mcpServers": {
    "maitabi": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "phonhay103/maitabi-mcp-server:latest"
      ]
    }
  }
}
```

#### 2. `servers` key format (requires `"type": "stdio"`)

```json
{
    "servers": {
        "maitabi": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "phonhay103/maitabi-mcp-server:latest"
            ],
            "type": "stdio"
        },
        "maitabi-pypi": {
            "type": "stdio",
            "command": "uvx",
            "args": [
                "maitabi-mcp-server"
            ]
        }
    },
    "inputs": []
}
```

### Agent Skills ([vercel-labs/skills](https://github.com/vercel-labs/skills))

Install and use Agent Skills from this repository via `npx skills`:

```bash
# Install to current project
npx skills add phonhay103/maitabi-mcp-server

# Install globally
npx skills add phonhay103/maitabi-mcp-server -g

# List skills / Use without installing
npx skills add phonhay103/maitabi-mcp-server --list
npx skills use phonhay103/maitabi-mcp-server
```

**Available Skills:**
- **`maitabi-bus-extractor`** (`skills/maitabi-bus-extractor/SKILL.md`): Raw HTTP/curl extraction for mountain bus (`bus.maitabi.jp`) and general trekking tours (`www.maitabi.jp`). Standalone — no MCP or CLI needed.
- **`maitabi-cli`** (`skills/maitabi-cli/SKILL.md`): Terminal `maitabi ...` commands with JSON output. Same core as MCP.
- **`maitabi-mcp`** (`skills/maitabi-mcp/SKILL.md`): How to call the already-connected MCP tools (`search_tours`, `get_tour_detail`, ...) — tool choice, flows, args, output. Assumes the server from §1 is already configured; no install steps here.

---

## CLI Usage (Optional — Default Distribution Is MCP)

The `maitabi` CLI shares the same core services as the MCP server and prints identical JSON to stdout.

```bash
# Via uvx / pip
uvx maitabi --help
pip install maitabi-mcp-server && maitabi --help

# Via Docker (image contains both entrypoints)
docker run -i --rm --entrypoint maitabi phonhay103/maitabi-mcp-server:latest --help

# Examples
maitabi search-tours --departure 1 --month 8 --area 18 --page 1 --pretty
maitabi search-general-tours --travel-type 1 --keyword '富士山' --year-month 2026-08 --pretty
maitabi get-tour-detail --course-no 14241 --pretty
maitabi get-tour-calendar --year 2026 --month 8 --pretty
```

Every subcommand accepts `--pretty` (indented JSON) and `--output FILE`. See `make cli-help` for the full list, or [`docs/TOOL_CATALOG.md`](docs/TOOL_CATALOG.md) for all flags.

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Upstream/network error (result payload contains `error`, incl. rate limiting) |
| 2 | Input error (bad flag value or failed validation) |

Scripts can branch on these, e.g. `maitabi search-tours ... || echo "upstream issue" >&2`.

### Rate limits

| Host | Limit | Applies to |
|------|-------|------------|
| `www.maitabi.jp` | 60 requests/min per IP | General tours + calendar (MCP tools, CLI, or curl alike) |
| `api.bus.maitabi.jp` | None observed at normal usage | Mountain bus tours |

When the cap is hit, wrappers return `{"error": "Rate limited by www.maitabi.jp ...", "retry_hint": "wait ~60s and retry manually"}` instead of results. There is no auto-retry — wait and re-run. Narrow `day` ranges help, since each day fans out into a parallel request.

---

## 2. Development

### Makefile Commands

```bash
make help           # Show available Makefile targets
make install        # Install dependencies using uv
make dev            # Run the MCP server locally over stdio
make dev-http       # Run the MCP server locally over Streamable HTTP (Port 8000)
make test           # Run the offline test suite (pytest, no network)
make smoke          # LIVE smoke check against the production API
make catalog        # Regenerate docs/TOOL_CATALOG.md + skill reference copies
make catalog-check  # Fail if generated files are stale (what CI runs)
make docker-build   # Build 2-stage Docker image (Python 3.14)
make build          # Build Python package wheel & sdist
```

### Architecture (for contributors)

See [`AGENTS.md`](AGENTS.md). In short: parameters live once in `core/inputs.py`, services in `services/`, and both the MCP tools and the CLI parser are generated from `registry.py`; the tool catalog is generated from that by `scripts/gen_catalog.py`, so the interfaces cannot drift.

### Local Development Client Configuration

To test a local checkout with an MCP client:

```json
{
  "mcpServers": {
    "maitabi": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/maitabi-mcp-server",
        "maitabi-mcp-server"
      ]
    }
  }
}
```
