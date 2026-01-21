#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Quick dependency check for tests.

This lightweight helper verifies that ``numpy``, ``yaml`` and ``pandas``
along with a few core packages are installed.  It is intended as a fast
pre-flight check before running the full environment
validation or the test suite.

When any package is missing the script prints a message
and exits with an error, instructing the user to run
``python check_env.py --auto-install`` for the complete
setup.
"""

from __future__ import annotations

import importlib.util
import sys

REQUIRED = ["numpy", "pytest", "yaml", "pandas"]


def main() -> int:
    missing: list[str] = []
    for pkg in REQUIRED:
        if importlib.util.find_spec(pkg) is None:
            missing.append(pkg)
    if missing:
        print("Missing packages:", ", ".join(missing))
        print("Run 'python check_env.py --auto-install' to install them.")
        return 1
    print("All required packages available.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
