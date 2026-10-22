"""Argparse definition for the `maitabi` CLI — generated from core models.

Two levels: `maitabi <domain> <command>`, where the domain is the upstream
family (`bus` = api.bus.maitabi.jp, `general` = www.maitabi.jp) and the
command mirrors the MCP tool name minus its domain prefix. `maitabi mcp`
starts the MCP server, so one executable covers both interfaces.

Every subcommand comes from `registry.ACTIONS` and every flag from the
action's Pydantic `model_fields`, so CLI flags cannot drift from the MCP
schema. No network or parsing logic lives here — see `commands.py` and
`services/`. Must NOT import fastmcp/mcp/server/mcp so the CLI stays
importable without MCP dependencies installed.
"""

import argparse
from typing import Any

from pydantic.fields import FieldInfo

from maitabi.cli.fields import plan_field
from maitabi.mcp_args import add_mcp_args
from maitabi.registry import ACTIONS, DOMAINS
from maitabi.version import get_version

DOMAIN_HELP = {
    "bus": "Mountain bus tours (api.bus.maitabi.jp)",
    "general": "General tours & calendar (www.maitabi.jp)",
}


def _add_field(p: argparse.ArgumentParser, name: str, info: FieldInfo) -> None:
    plan = plan_field(name, info)
    kwargs: dict[str, Any] = {"dest": name, "help": info.description}
    if plan.metavar is not None:
        kwargs["metavar"] = plan.metavar
    if plan.store_true:
        kwargs["action"] = "store_true"
        kwargs["default"] = plan.default
    else:
        kwargs["type"] = plan.arg_type
        kwargs["default"] = plan.default
        if plan.choices is not None:
            kwargs["choices"] = plan.choices
        if plan.required:
            kwargs["required"] = True
    p.add_argument(plan.flag, **kwargs)


def _add_output_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON with indent=2")
    p.add_argument(
        "--output", type=str, default=None, metavar="FILE", help="Write JSON output to FILE instead of stdout"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maitabi",
        description="Maitabi CLI — bus tours, general tours, and the MCP server in one command",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {get_version()}")
    domains = parser.add_subparsers(dest="domain", metavar="<group>")

    for domain in DOMAINS:
        group = domains.add_parser(domain, help=DOMAIN_HELP[domain])
        group.set_defaults(_group=group)
        commands = group.add_subparsers(dest="command", metavar="<command>")
        for action in (a for a in ACTIONS if a.domain == domain):
            p = commands.add_parser(action.command, help=action.help)
            for name, info in action.input_model.model_fields.items():
                _add_field(p, name, info)
            _add_output_args(p)

    mcp_parser = domains.add_parser("mcp", help="Run the MCP server (stdio, sse, streamable-http)")
    add_mcp_args(mcp_parser)

    return parser
