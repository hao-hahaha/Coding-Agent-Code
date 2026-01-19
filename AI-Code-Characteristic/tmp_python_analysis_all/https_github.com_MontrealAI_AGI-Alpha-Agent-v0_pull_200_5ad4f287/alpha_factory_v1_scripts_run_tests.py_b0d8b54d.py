#!/usr/bin/env python3
"""Run Alpha-Factory unit tests.

This helper prefers :mod:`pytest` if installed, falling back to
``python -m unittest`` when necessary. A test path can be optionally
specified. The module also exposes :func:`run_tests` for programmatic
use.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


def run_tests(target: Path) -> int:
    """Execute tests under ``target``.

    ``pytest`` is preferred when available; otherwise ``unittest`` is used.
    The exit status of the invoked command is returned.
    """
    if importlib.util.find_spec("pytest"):
        cmd = [sys.executable, "-m", "pytest", str(target)]
    else:
        cmd = [sys.executable, "-m", "unittest", "discover", str(target)]
    return subprocess.call(cmd)


def main() -> None:
    script_dir = Path(__file__).resolve().parents[1]
    repo_root = script_dir.parent
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if not target.is_absolute():
            guess = script_dir / target
            if not guess.exists():
                guess = repo_root / target
            target = guess
    else:
        target = script_dir / "tests"
    if not target.exists():
        raise SystemExit(f"Test path {target} not found")

    raise SystemExit(run_tests(target))


if __name__ == "__main__":
    main()
