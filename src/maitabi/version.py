"""The installed distribution version.

Single source of truth stays `pyproject.toml`; this module only reads the
metadata of the installed package, so `maitabi --version`, the MCP
`serverInfo`, and PyPI can never disagree.
"""

from importlib.metadata import PackageNotFoundError, version


def get_version() -> str:
    """Installed version, or a marker when running from an uninstalled tree."""
    try:
        return version("maitabi")
    except PackageNotFoundError:  # pragma: no cover - only in a bare source tree
        return "0.0.0+unknown"
