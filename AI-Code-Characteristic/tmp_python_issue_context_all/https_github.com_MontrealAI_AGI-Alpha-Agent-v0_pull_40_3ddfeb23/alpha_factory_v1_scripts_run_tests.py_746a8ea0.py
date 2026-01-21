#!/usr/bin/env python3
"""Run Alpha-Factory unit tests.

This helper prefers *pytest* if installed, falling back to
``python -m unittest`` when necessary. A test path can be optionally
specified.
"""
from __future__ import annotations
import importlib.util
import subprocess
import sys
from pathlib import Path


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "tests"
    if importlib.util.find_spec("pytest"):
        cmd = [sys.executable, "-m", "pytest", str(target)]
    else:
        cmd = [sys.executable, "-m", "unittest", "discover", str(target)]
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
