"""CLI command dispatch — one generic handler over the action registry.

Flow: argparse namespace → Pydantic Input (CSV/string flags coerced per
`fields.plan_field`) → `asyncio.run(service())` → JSON to stdout or
`--output` file. Exit codes: 0 OK, 1 upstream/network error, 2 input error.
Must NOT import fastmcp/mcp/server/mcp.
"""

import argparse
import asyncio
import json
import sys

from pydantic import ValidationError

from maitabi_mcp_server.cli.fields import plan_field
from maitabi_mcp_server.registry import Action
from maitabi_mcp_server.services.http import close_http_client

EXIT_OK = 0
EXIT_UPSTREAM_ERROR = 1
EXIT_INPUT_ERROR = 2


def _emit(data: dict, args: argparse.Namespace) -> None:
    """Serialize the service dict to the CLI's JSON wire format.

    Always indent=2 / ensure_ascii=False — byte-identical to the historic
    output (services used to pre-serialize with the same settings), so
    `--pretty` stays a compat no-op.
    """
    text = json.dumps(data, ensure_ascii=False, indent=2)
    output = getattr(args, "output", None)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)


async def _run(service_coro) -> dict:
    try:
        return await service_coro
    finally:
        await close_http_client()


def build_input(action: Action, args: argparse.Namespace):
    """Map the parsed namespace onto the action's Input model.

    Every model field exists as a flag (both are generated from the same
    model), so this mapping is total; string flags are coerced per plan.
    """
    kwargs = {}
    for name, info in action.input_model.model_fields.items():
        raw = getattr(args, name, None)
        plan = plan_field(name, info)
        if plan.coerce is not None and isinstance(raw, str):
            raw = plan.coerce(raw)
        kwargs[name] = raw
    return action.input_model(**kwargs)


def run_action(action: Action, args: argparse.Namespace) -> int:
    """Execute one action and return its process exit code."""
    try:
        payload = build_input(action, args)
    except (ValidationError, ValueError) as exc:
        print(f"maitabi: invalid arguments for {action.command}: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    data = asyncio.run(_run(action.service(payload)))
    _emit(data, args)
    return EXIT_UPSTREAM_ERROR if "error" in data else EXIT_OK
