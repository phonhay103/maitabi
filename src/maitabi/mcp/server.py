"""MCP server: factory, transport argument parsing, `main()` and `run()`.

Started either as `maitabi mcp` (the CLI subcommand) or directly via
`python -m maitabi.mcp.server`. Both paths share `mcp_args.add_mcp_args`.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from maitabi.mcp.tools import register_tools
from maitabi.services.http import close_http_client


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncGenerator[None]:
    try:
        yield
    finally:
        await close_http_client()


def create_mcp() -> FastMCP:
    """Build a fully wired FastMCP instance (fresh per call)."""
    mcp = FastMCP("maitabi", lifespan=app_lifespan)
    register_tools(mcp)
    return mcp


# Default instance for tests and for `python -m maitabi.mcp.server`.
mcp = create_mcp()


def run(*, transport: str = "stdio", host: str | None = None, port: int = 8000, path: str = "/mcp") -> None:
    """Serve over the chosen transport (blocks for stdio and HTTP alike)."""
    from maitabi.mcp_args import DEFAULT_HOST

    if transport == "stdio":
        import logging

        # Silence standard logs to prevent noise on stderr that confuses client IDEs
        logging.basicConfig(level=logging.WARNING)
        for logger_name in ["mcp", "fastmcp", "uvicorn", "anyio"]:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
        mcp.run(transport="stdio", show_banner=False)
    elif transport == "streamable-http":
        mcp.run(transport="streamable-http", host=host or DEFAULT_HOST, port=port, path=path)
    elif transport == "sse":
        mcp.run(transport="sse", host=host or DEFAULT_HOST, port=port)
    else:  # pragma: no cover - argparse restricts choices
        raise ValueError(f"unknown transport: {transport}")


def main(argv: list[str] | None = None) -> int:
    """Standalone entrypoint (`python -m maitabi.mcp.server`)."""
    import argparse

    from maitabi.mcp_args import add_mcp_args

    parser = argparse.ArgumentParser(prog="maitabi mcp", description="Maitabi MCP Server")
    add_mcp_args(parser)
    args = parser.parse_args(argv)
    run(transport=args.transport, host=args.host, port=args.port, path=args.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
