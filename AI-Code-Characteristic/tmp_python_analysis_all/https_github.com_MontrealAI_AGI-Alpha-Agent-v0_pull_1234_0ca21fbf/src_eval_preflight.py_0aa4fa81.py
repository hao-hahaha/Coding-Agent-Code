# SPDX-License-Identifier: Apache-2.0
"""Lightweight preflight checks for patches.

Compiles all tracked Python files and runs a minimal
unit test when available. Raises ``CalledProcessError``
on failure.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__ = ["run_preflight"]


def run_preflight(repo_dir: str | Path = ".") -> None:
    """Run compilation and smoke tests inside ``repo_dir``."""

    repo = Path(repo_dir)
    result = subprocess.run(
        ["git", "ls-files", "*.py"], capture_output=True, text=True, cwd=repo
    )
    files = [f for f in result.stdout.splitlines() if f]
    if files:
        subprocess.run([sys.executable, "-m", "py_compile", *files], check=True, cwd=repo)

    test_path = repo / "tests" / "basic_edit.py"
    if test_path.exists():
        subprocess.run(["pytest", "-q", str(test_path)], check=True, cwd=repo)


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    repo = Path(argv[0]) if argv else Path(".")
    run_preflight(repo)


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
