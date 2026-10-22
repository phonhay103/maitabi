"""Support `python -m maitabi` — same entrypoint as the `maitabi` script."""

from maitabi.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
