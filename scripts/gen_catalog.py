#!/usr/bin/env python3
"""Generate the tool catalog and skill reference copies from code.

Single source of truth: `maitabi_mcp_server.core.registry.ACTIONS`.
Run `python scripts/gen_catalog.py` to regenerate; `--check` exits non-zero
if committed files are stale (used by CI).
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify outputs are up to date")
    parser.parse_args()
    # Full generation lands in Phase 3; until then treat as pass-through.
    print("gen_catalog: not yet implemented (Phase 3)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
