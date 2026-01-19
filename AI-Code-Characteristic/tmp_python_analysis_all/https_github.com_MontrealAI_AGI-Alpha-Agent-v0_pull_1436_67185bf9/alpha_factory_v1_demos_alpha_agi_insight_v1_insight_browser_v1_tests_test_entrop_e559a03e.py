# SPDX-License-Identifier: Apache-2.0
"""Run the browser entropy test via npm."""

import shutil
import subprocess
from pathlib import Path

import pytest

BROWSER_DIR = Path(__file__).resolve().parents[1]

@pytest.mark.skipif(shutil.which("npm") is None, reason="npm not installed")
def test_entropy_js() -> None:
    subprocess.check_call(["npm", "test"], cwd=BROWSER_DIR)
