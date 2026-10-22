"""MCP server entrypoint: factory, transport argument parsing, `main()`."""

import argparse
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from maitabi_mcp_server.mcp.tools import register_tools
from maitabi_mcp_server.services.http import close_http_client


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncGenerator[None]:
    try:
        yield
    finally:
        await close_http_client()


# Binding all interfaces is intentional: the HTTP/SSE transports exist to be
# reached from outside the process (container or LAN), not only from localhost.
DEFAULT_HOST = "0.0.0.0"  # noqa: S104


def create_mcp() -> FastMCP:
    """Build a fully wired FastMCP instance (fresh per call)."""
    mcp = FastMCP("maitabi-mcp-server", lifespan=app_lifespan)
    register_tools(mcp)
    return mcp


# Default instance for `maitabi-mcp-server` / tests.
mcp = create_mcp()


def main() -> None:
    parser = argparse.ArgumentParser(description="Maitabi MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        help="Transport protocol: 'stdio', 'sse', or 'streamable-http'. Default: stdio",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", DEFAULT_HOST),
        help="Host address for HTTP/SSE transport. Default: 0.0.0.0",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Port number for HTTP/SSE transport. Default: 8000",
    )
    parser.add_argument(
        "--path",
        default=os.getenv("MCP_PATH", "/mcp"),
        help="Path for Streamable HTTP transport. Default: /mcp",
    )

    args = parser.parse_args()

    if args.transport == "stdio":
        import logging

        # Silence all standard logs to prevent noise on stderr that confuses client IDEs
        logging.basicConfig(level=logging.WARNING)
        for logger_name in ["mcp", "fastmcp", "uvicorn", "anyio"]:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
        mcp.run(transport="stdio", show_banner=False)
    elif args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port, path=args.path)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
