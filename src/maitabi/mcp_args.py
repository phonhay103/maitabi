"""Transport arguments shared by `maitabi mcp` and `python -m maitabi.mcp.server`.

Lives outside `mcp/` so the CLI can build the subparser without importing
fastmcp (the CLI must stay importable with MCP dependencies absent).
"""

import argparse
import os

from maitabi.version import get_version

# Binding all interfaces is intentional: the HTTP/SSE transports exist to be
# reached from outside the process (container or LAN), not only from localhost.
DEFAULT_HOST = "0.0.0.0"  # noqa: S104


def add_mcp_args(parser: argparse.ArgumentParser) -> None:
    """Add the MCP transport flags to a parser."""
    parser.add_argument("--version", action="version", version=f"%(prog)s {get_version()}")
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
