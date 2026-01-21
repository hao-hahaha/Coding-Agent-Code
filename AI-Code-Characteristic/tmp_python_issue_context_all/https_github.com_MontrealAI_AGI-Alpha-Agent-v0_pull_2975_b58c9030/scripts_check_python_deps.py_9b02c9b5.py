#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Quick dependency check for tests.

This lightweight helper verifies that ``numpy``, ``yaml`` and ``pandas``
along with a few core packages are installed.  It is intended as a fast
pre-flight check before running the full environment validation or the
test suite.

The check now calls ``python -m pip show`` for each package instead of
importing the module.  When any package is missing the script prints a
clear message instructing the user to run ``python check_env.py
--auto-install`` and exits with a non-zero status.
"""

from __future__ import annotations

import subprocess
import sys

REQUIRED = ["numpy", "pytest", "pyyaml", "pandas"]


def _pkg_installed(pkg: str) -> bool:
    """Return ``True`` when ``pkg`` is installed.

    The check uses ``python -m pip show`` for reliability when namespace
    packages are involved.
    """

    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", pkg],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def main() -> int:
    missing: list[str] = [pkg for pkg in REQUIRED if not _pkg_installed(pkg)]
    if missing:
        print("Missing packages:", ", ".join(missing))
        print("Run 'python check_env.py --auto-install' to install them.")
        return 1
    print("All required packages available.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
