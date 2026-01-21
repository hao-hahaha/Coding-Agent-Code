# SPDX-License-Identifier: Apache-2.0
"""Ensure the governance-sim CLI runs."""

import sys
import subprocess

import pytest


@pytest.mark.skipif(sys.platform.startswith("win"), reason="governance-sim not supported on Windows")
def test_governance_sim_cli() -> None:
    """Verify the console script prints a result."""
    result = subprocess.run(
        ["governance-sim", "-N", "10", "-r", "20"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "mean cooperation" in result.stdout.lower()
