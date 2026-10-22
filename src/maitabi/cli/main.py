"""Entrypoint for the `maitabi` CLI.

Usage: `maitabi <bus|general> <command>` or `maitabi mcp [--transport ...]`.

Exit codes: 0 OK · 1 upstream/network error · 2 input error
(argparse rejects bad flags with 2 as well).
"""

from maitabi.cli.commands import EXIT_OK, run_action
from maitabi.cli.parser import build_parser
from maitabi.registry import ACTION_BY_KEY


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.domain:
        parser.print_help()
        return EXIT_OK
    if args.domain == "mcp":
        # Imported lazily: the CLI must stay importable without fastmcp.
        from maitabi.mcp.server import run

        run(transport=args.transport, host=args.host, port=args.port, path=args.path)
        return EXIT_OK
    if not args.command:
        args._group.print_help()
        return EXIT_OK
    action = ACTION_BY_KEY.get((args.domain, args.command))
    if action is None:  # pragma: no cover - argparse restricts choices
        parser.error(f"unknown command: {args.domain} {args.command}")
    return run_action(action, args)


if __name__ == "__main__":
    raise SystemExit(main())
