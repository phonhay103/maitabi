# Changelog

All notable changes to this project. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html): the JSON output
contract only grows within a major version.

## [Unreleased]

## [1.3.0]

### Added

- MCP tools now return `structuredContent` alongside the text block, so clients
  read the payload without reparsing JSON. The text block is byte-identical to
  the CLI output.
- MCP tools declare a read-only annotation set (`readOnlyHint`,
  `destructiveHint: false`, `idempotentHint`, `openWorldHint`), a `Maitabi: …`
  title, domain tags, and an object `outputSchema`.
- `initialize` returns server `instructions`: the discovery → search → detail
  flow, the envelope shape, and the 60 req/min cap on `general_*`.
- `evals/` holds a live, read-only evaluation suite for the published server,
  plus `evals/run.py`, an OpenAI-compatible runner (the mcp-builder harness needs
  an Anthropic key). First run: 10/10 on `deepseek/deepseek-v4.1-flash`.
- 4xx upstream errors carry a `retry_hint` pointing at the inputs; 5xx keeps the
  existing shape. This is additive to the error contract.

### Changed

- `list_order` is a `Literal`, so an unknown sort order is an input error
  instead of being forwarded.
- Field and tool descriptions name where IDs come from
  (`area` → `bus_list_district_groups`, `stay*` → `bus_list_filters`,
  `course_no` → a search result) and state each general tool's rate limit.
- A call whose payload is the shared error shape now reports `isError: true`
  instead of looking successful to the model.

### Fixed

- The action count in `docs/TOOL_CATALOG.md`, the registry docstring, the README
  and the MCP skill were hardcoded to seven after the eighth action shipped.
  The generator now prints `len(ACTIONS)`.
- Literal string choices (`kind`) rendered as `int {…}` in the catalog.
- The `area` description pointed at `bus_list_district_groups`, whose group IDs
  are display buckets that return zero results when used as `area`. It now names
  `bus_list_filter_master(kind='district')`, and the district-groups tool says
  plainly that its IDs are not the search filter.
- The evaluation suite exposed that `course_cd` matches nothing upstream, so the
  field is documented as deprecated in favour of `keyword`.
