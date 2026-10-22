"""Import isolation: CLI must not require MCP deps; core must not import wrappers."""

import sys


def test_cli_imports_without_mcp_deps():
    blocked = {"fastmcp", "mcp"}
    import builtins

    orig = builtins.__import__

    def guard(name, *args, **kwargs):
        if name.split(".")[0] in blocked:
            raise ImportError(f"blocked for isolation test: {name}")
        return orig(name, *args, **kwargs)

    for mod in [m for m in list(sys.modules) if m.split(".")[0] in blocked or m.startswith("maitabi.cli")]:
        del sys.modules[mod]
    builtins.__import__ = guard
    try:
        import maitabi.cli.commands
        import maitabi.cli.main
        import maitabi.cli.parser  # noqa: F401
    finally:
        builtins.__import__ = orig


def test_core_services_do_not_import_wrappers():
    import subprocess

    code = (
        "import maitabi.services.bus as b, "
        "maitabi.services.general as g; "
        "mods = set(b.__dict__.get('__name__', '')) ; "
        "import sys; "
        "bad = [m for m in sys.modules if 'maitabi.mcp' in m "
        "or 'maitabi.tools' in m "
        "or 'maitabi.cli' in m or m.split('.')[0] in ('fastmcp','mcp')]; "
        "assert not bad, bad; print('core isolation OK')"
    )
    # The interpreter path and code string are test-owned literals, not input.
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)  # noqa: S603
    assert r.returncode == 0, r.stderr
    assert "core isolation OK" in r.stdout
