# Evaluations

A live, read-only check that the server is usable by an LLM that has **only the
8 tools** — no skill, no README, no source. It measures the thing the tool
descriptions are for: can a model discover the right IDs, chain the calls, and
read the payload without guessing?

Ten questions, each answer a single verified value:

```bash
# from the mcp-builder skill's scripts/ directory, with ANTHROPIC_API_KEY set
python evaluation.py /path/to/maitabi-mcp-server/evals/maitabi_evaluation.xml \
  --command uv --args run --directory /path/to/maitabi-mcp-server maitabi mcp \
  --output /tmp/maitabi-eval.json
```

Against the hosted endpoint instead of stdio:

```bash
python evaluation.py evals/maitabi_evaluation.xml \
  --transport http --url https://maitabi.fastmcp.app/mcp
```

## Reading the result

- `<response>` must equal `<answer>` exactly (numbers and Japanese text are
  compared as strings).
- `NOT_FOUND` means the model gave up: the tool set, a description, or an
  error message did not carry enough information. Treat it as a defect in the
  descriptions, not in the model.
- `<feedback>` names the tools the model found confusing. Only act on it when
  the same point shows up in a real run — the descriptions are contract-tested,
  so speculative rewrites cost a fixture regeneration.

## Re-baselining (required before every `v*` tag)

Tour counts, prices and availability move with the season, so the answers pinned
to November 2026 are a snapshot, not a constant. Before tagging:

1. Re-answer each question with the same tools (the CLI is convenient:
   `maitabi bus list-district-groups --month 11`).
2. Update `<answer>` where the data moved, and the verified date in the XML
   header comment.
3. Record the answer changes in `CHANGELOG.md` under the release heading.

Questions that are pure ID lookups (style names, seat-type counts) should not
move; if one does, the upstream schema changed and the services need a look.
