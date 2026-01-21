# SPDX-License-Identifier: Apache-2.0
"""Run the browser entropy test via npm."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

BROWSER_DIR = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(
    shutil.which("npm") is None,
    reason="npm not installed",
)  # type: ignore[misc]
def test_entropy_js() -> None:
    cmd = ["npm", "test"]
    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        cmd.append("--offline")
    subprocess.check_call(cmd, cwd=BROWSER_DIR)
