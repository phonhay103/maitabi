"""Entrypoint for the `maitabi` CLI (optional wrapper; default distribution is MCP).

Exit codes: 0 OK · 1 upstream/network error · 2 input error
(argparse rejects bad flags with 2 as well).
"""

from maitabi_mcp_server.cli.commands import EXIT_OK, run_action
from maitabi_mcp_server.cli.parser import build_parser
from maitabi_mcp_server.registry import ACTION_BY_COMMAND


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return EXIT_OK
    action = ACTION_BY_COMMAND.get(args.command)
    if action is None:  # pragma: no cover - argparse restricts choices
        parser.error(f"unknown command: {args.command}")
    return run_action(action, args)


if __name__ == "__main__":
    raise SystemExit(main())
