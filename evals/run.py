#!/usr/bin/env python3
"""Run the live evaluation suite against any OpenAI-compatible chat endpoint.

The mcp-builder reference harness (`scripts/evaluation.py`) talks to the
Anthropic API directly. This runner does the same job with the stack this repo
already depends on — `fastmcp`'s client plus `httpx` — so a local LiteLLM proxy,
OpenRouter, or any `/chat/completions` endpoint can drive the ten questions.

Each question gets a fresh model conversation but shares one MCP session, so the
run measures the tools' discoverability, not the model's memory: nothing from a
previous question leaks in.

    MAITABI_EVAL_API_KEY=... uv run python evals/run.py --model gemini-3.5-flash

Exit code: 0 when every answer matches, 1 otherwise.
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from fastmcp import Client
from fastmcp.client.transports import StdioTransport, StreamableHttpTransport

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVAL_FILE = Path(__file__).resolve().parent / "maitabi_evaluation.xml"
DEFAULT_BASE_URL = "http://127.0.0.1:4000/v1"
DEFAULT_MODEL = "gemini-3.5-flash"
MAX_TURNS = 14

SYSTEM_PROMPT = """You are answering questions about Maitabi, a Japanese tour operator, \
using only the tools you are given. Do not answer from prior knowledge.

Work step by step. Follow the tool descriptions: they say which IDs exist, where \
to discover them, and how to read the payload. If a payload contains "error", read \
`retry_hint` and wait instead of repeating the same query.

When you are done, reply with:
<summary>the steps you took and which tools you used</summary>
<feedback>how clear the tool names, parameters and descriptions were; be specific about anything that made you guess</feedback>
<response>only the exact value asked for</response>

The <response> must be a single value: a number, an ID, or the exact text requested. \
If the tools cannot answer, use <response>NOT_FOUND</response>.
"""


def parse_eval_file(path: Path) -> list[dict[str, str]]:
    """Read `qa_pair` elements without pulling in an XML dependency."""
    import xml.etree.ElementTree as ET

    # The suite is a repo-owned fixture, not user input: no entity expansion risk.
    root = ET.parse(path).getroot()  # noqa: S314
    pairs: list[dict[str, str]] = []
    for pair in root.findall(".//qa_pair"):
        question = (pair.findtext("question") or "").strip()
        answer = (pair.findtext("answer") or "").strip()
        if question and answer:
            pairs.append({"question": question, "answer": answer})
    if not pairs:
        raise SystemExit(f"no qa_pair entries found in {path}")
    return pairs


def normalize(value: str) -> str:
    """Compare answers as text: collapse whitespace, drop wrapping quotes."""
    text = re.sub(r"\s+", " ", value).strip()
    return text.strip("\"'`「」").strip()


def extract_tag(text: str, tag: str) -> str | None:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL)
    return match.group(1).strip() if match else None


def tool_specs(tools: list[Any]) -> list[dict[str, Any]]:
    """MCP tool metadata → OpenAI function-calling schema.

    Over the wire this is `mcp.types.Tool` (`inputSchema`); in-process FastMCP
    objects expose the same dict as `parameters`.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": getattr(tool, "inputSchema", None) or tool.parameters,
            },
        }
        for tool in tools
    ]


class ChatModel:
    """Minimal `/chat/completions` client (no provider SDK)."""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=httpx.Timeout(120.0))
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._model = model

    def close(self) -> None:
        self._client.close()

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        """One chat turn, retrying the endpoint's own throttling (not ours)."""
        payload = {
            "model": self._model,
            "messages": messages,
            "tools": tools,
            "temperature": 0,
            "max_tokens": 2048,
        }
        last_error: Exception | None = None
        for attempt in range(6):
            try:
                response = self._client.post("/chat/completions", headers=self._headers, json=payload)
                if response.status_code == 429 or response.status_code >= 500:
                    wait = float(response.headers.get("retry-after") or [5, 15, 30, 45, 60, 60][attempt])
                    reason = " ".join(response.text.split())[:160]
                    print(f"      endpoint returned {response.status_code}, waiting {wait:.0f}s: {reason}", flush=True)
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return response.json()["choices"][0]["message"]
            except httpx.RequestError as exc:
                last_error = exc
                time.sleep(2 * (attempt + 1))
        raise SystemExit(f"chat endpoint kept failing after 6 attempts: {last_error}")


def tool_output(result: Any) -> str:
    """What the model sees for one tool call: the payload, or the error text."""
    if result.is_error:
        payload = result.structured_content or {}
        return f"ERROR: {payload.get('error', 'tool failed')} | {payload.get('retry_hint', '')}".strip()
    return json.dumps(result.structured_content, ensure_ascii=False, separators=(",", ":"))


async def answer_question(
    mcp: Client, chat: ChatModel, tools: list[dict[str, Any]], question: str
) -> tuple[str | None, str | None, int, int, list[dict[str, Any]]]:
    """Drive one question to a final answer.

    Returns (response, feedback, turns, tool_calls, messages) — the transcript is
    what makes a failure diagnosable without rerunning it.
    """
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    calls = 0
    nudges = 0
    repeated = 0
    last_call: tuple[str, str] | None = None
    for turn in range(1, MAX_TURNS + 1):
        message = chat.complete(messages, tools)
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            text = message.get("content") or ""
            if not text.strip() and nudges < 2:
                nudges += 1
                messages.append({"role": "assistant", "content": ""})
                messages.append(
                    {
                        "role": "user",
                        "content": "Reply now. End with the value inside <response></response>; do not call another tool.",
                    }
                )
                continue
            return extract_tag(text, "response"), extract_tag(text, "feedback"), turn, calls, messages

        # Echo the assistant turn verbatim: Gemini/LiteLLM attaches a
        # thought_signature the next request must carry back.
        messages.append({"role": "assistant", "content": message.get("content"), "tool_calls": tool_calls})
        for call in tool_calls:
            calls += 1
            name = call["function"]["name"]
            try:
                arguments = json.loads(call["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                messages.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": "ERROR: arguments were not valid JSON"}
                )
                continue
            signature = (name, json.dumps(arguments, sort_keys=True, ensure_ascii=False))
            repeated = repeated + 1 if signature == last_call else 0
            last_call = signature
            result = await mcp.call_tool(name, arguments)
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": tool_output(result)})

        if repeated >= 2 and nudges < 2:
            nudges += 1
            repeated = 0
            messages.append(
                {
                    "role": "user",
                    "content": "Those results are already in the conversation. Do not call that same tool again: "
                    "answer now, ending with the value inside <response></response>.",
                }
            )

    return None, None, MAX_TURNS, calls, messages


async def run(args: argparse.Namespace) -> int:
    api_key = os.environ.get(args.api_key_env) or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit(f"set {args.api_key_env} (a scoped endpoint key, never the admin/master one)")

    if args.transcript_dir:
        args.transcript_dir.mkdir(parents=True, exist_ok=True)
    pairs = parse_eval_file(args.eval_file)
    chat = ChatModel(args.base_url, api_key, args.model)
    if args.url:
        transport: StdioTransport | StreamableHttpTransport = StreamableHttpTransport(args.url)
    else:
        transport = StdioTransport(command=args.command, args=args.command_args, cwd=str(ROOT))

    results: list[dict[str, Any]] = []
    try:
        async with Client(transport) as mcp:
            tools = tool_specs(await mcp.list_tools())
            print(f"{len(tools)} tools · model {args.model} · {len(pairs)} questions\n")
            for index, pair in enumerate(pairs, start=1):
                if index > 1 and args.pause:
                    time.sleep(args.pause)
                response, feedback, turns, calls, transcript = await answer_question(mcp, chat, tools, pair["question"])
                passed = response is not None and normalize(response) == normalize(pair["answer"])
                results.append(
                    {
                        "question": pair["question"],
                        "expected": pair["answer"],
                        "actual": response,
                        "passed": passed,
                        "turns": turns,
                        "tool_calls": calls,
                        "feedback": feedback,
                    }
                )
                if args.transcript_dir and not passed:
                    name = f"q{index:02d}.json"
                    (args.transcript_dir / name).write_text(
                        json.dumps(transcript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                    )
                mark = "PASS" if passed else "FAIL"
                print(f"[{index:02d}] {mark}  {turns:2d} turns / {calls:2d} calls  {pair['question'][:70]}")
                if not passed:
                    print(f"      expected {pair['answer']!r}, got {response!r}")
    finally:
        chat.close()

    passed_count = sum(1 for result in results if result["passed"])
    print(f"\n{passed_count}/{len(results)} passed")
    failures = [result for result in results if not result["passed"]]
    for result in failures:
        if result["feedback"]:
            print(f"\nfeedback on {result['question'][:60]}:\n  {result['feedback']}")

    if args.output:
        args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.output}")

    return 0 if passed_count == len(results) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-file", type=Path, default=DEFAULT_EVAL_FILE, help="XML suite to run")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("MAITABI_EVAL_BASE_URL", DEFAULT_BASE_URL),
        help="OpenAI-compatible /v1 base URL",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("MAITABI_EVAL_MODEL", DEFAULT_MODEL),
        help="Model id served by that endpoint",
    )
    parser.add_argument(
        "--api-key-env",
        default="MAITABI_EVAL_API_KEY",
        help="Environment variable holding the endpoint key (never passed on argv)",
    )
    parser.add_argument("--command", default="uv", help="stdio: command that starts the MCP server")
    parser.add_argument(
        "--command-args",
        nargs="+",
        default=["run", "maitabi", "mcp"],
        help="stdio: arguments for --command",
    )
    parser.add_argument("--url", help="streamable HTTP: MCP endpoint URL (overrides --command)")
    parser.add_argument("--output", type=Path, help="write the full report as JSON")
    parser.add_argument("--transcript-dir", type=Path, help="write each failed question's messages here")
    parser.add_argument(
        "--pause",
        type=float,
        default=float(os.environ.get("MAITABI_EVAL_PAUSE", "0")),
        help="seconds to wait between questions (throttled endpoints)",
    )
    return asyncio.run(run(parser.parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
