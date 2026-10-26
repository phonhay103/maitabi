# Evaluations

A live, read-only check that the server is usable by an LLM that has **only the
8 tools** — no skill, no README, no source. It measures the thing the tool
descriptions are for: can a model discover the right IDs, chain the calls, and
read the payload without guessing?

Ten questions, each answer a single verified value.

## Run it

```bash
# key comes from the environment, never argv; any OpenAI-compatible /v1 endpoint works
MAITABI_EVAL_API_KEY=... uv run python evals/run.py --model gemini-3.5-flash
```

Defaults: `--base-url http://127.0.0.1:4000/v1` (a local LiteLLM proxy),
`--model gemini-3.5-flash`, stdio server via `uv run maitabi mcp`. Point it at the
hosted endpoint with `--url https://maitabi.fastmcp.app/mcp`.

Useful flags:

| Flag | Why |
|---|---|
| `--eval-file` | run a subset (e.g. one edited question) |
| `--output report.json` | keep the per-question turns, call counts and verdicts |
| `--transcript-dir /tmp/tr` | dump the failed questions' full message history |

Exit code is `0` only when every answer matches. A model that loops without
answering, answers from memory, or returns `NOT_FOUND` all count as failures.

Size and quota both matter. One page of `general_search_tours` is ~49k characters
(~16k tokens), so an endpoint with an 8k-token-per-minute cap (Groq's free tier,
for example) rejects the request outright instead of answering — that is a model
limit, not a tool failure, but it is why the runner needs a large-context model.

Last verified run: **10/10** on `deepseek/deepseek-v4.1-flash`, 2026-10-26, 24
tool calls total. `openai/gpt-oss-120b` answered 9/10 (its context cap rejected
the general-search payload); `gemini-3.5-flash` exhausted its 20-request daily
free quota before finishing.


The mcp-builder reference harness (`scripts/evaluation.py` in the
`mcp-builder` skill) also works if an Anthropic key is available; it asks the
same questions and produces the same `<response>`/`<feedback>` structure.

## Reading the result

- `NOT_FOUND` means the model gave up: the tool set, a description, or an error
  message did not carry enough information. Treat it as a description defect.
- `<feedback>` names what made the model guess. The first full run already paid
  for itself: it caught the `area` filter pointing at the wrong ID space and
  `course_cd` matching nothing upstream.
- A repeated identical tool call (visible in the transcript) is a model quirk,
  not a tool defect — retry with another model before changing a description.

## Re-baselining (required before every `v*` tag)

Tour counts, prices and availability move with the season, so answers pinned to
November 2026 are a snapshot, not a constant. Before tagging:

1. Re-answer each question with the same tools (the CLI is convenient:
   `maitabi bus list-district-groups --month 11`).
2. Update `<answer>` where the data moved, and the verified date in the XML
   header comment.
3. Record the answer changes in `CHANGELOG.md` under the release heading.

Questions that are pure ID lookups (style names, seat-type counts) should not
move; if one does, the upstream schema changed and the services need a look.
