"""Argparse definition for the `maitabi` CLI — generated from core models.

Every subcommand comes from `registry.ACTIONS` and every flag from the
action's Pydantic `model_fields`, so CLI flags cannot drift from the MCP
schema. No network or parsing logic lives here — see `commands.py` and
`services/`. Must NOT import fastmcp/mcp/server/mcp so the CLI stays
importable without MCP dependencies installed.
"""

import argparse

from maitabi_mcp_server.cli.fields import plan_field
from maitabi_mcp_server.registry import ACTIONS


def _add_field(p: argparse.ArgumentParser, name, info) -> None:
    plan = plan_field(name, info)
    kwargs: dict = {"dest": name, "help": info.description}
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
    p.add_argument("--pretty", action="store_true",
                   help="Pretty-print JSON with indent=2")
    p.add_argument("--output", type=str, default=None, metavar="FILE",
                   help="Write JSON output to FILE instead of stdout")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maitabi",
        description="Maitabi CLI — search mountain bus & general tours (same core as MCP server)",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    for action in ACTIONS:
        p = sub.add_parser(action.command, help=action.help)
        for name, info in action.input_model.model_fields.items():
            _add_field(p, name, info)
        _add_output_args(p)

    return parser
