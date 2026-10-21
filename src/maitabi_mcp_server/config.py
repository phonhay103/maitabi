"""Configuration constants for Maitabi MCP Server.

Base URLs are env-overridable so tests and mirrors can repoint the clients
without touching service code.
"""

import os

API_BASE = os.getenv("MAITABI_API_BASE", "https://api.bus.maitabi.jp")
WEB_BASE = os.getenv("MAITABI_WEB_BASE", "https://bus.maitabi.jp")
MAIN_BASE = os.getenv("MAITABI_MAIN_BASE", "https://www.maitabi.jp")
