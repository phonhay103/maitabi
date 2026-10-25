"""Entrypoint for hosted FastMCP deployments.

Hosted builders start a server from one file at the repository root and ignore
``if __name__ == "__main__"`` blocks. The package is a ``src`` layout, so put
``src/`` on ``sys.path`` first: those builds install the dependencies but not
necessarily the project itself.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from maitabi.mcp.server import mcp

__all__ = ["mcp"]
