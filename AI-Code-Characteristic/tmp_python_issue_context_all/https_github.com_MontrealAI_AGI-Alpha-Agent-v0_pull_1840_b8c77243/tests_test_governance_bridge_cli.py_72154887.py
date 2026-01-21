# SPDX-License-Identifier: Apache-2.0
"""Ensure the governance-bridge CLI is available."""

import importlib.util
import subprocess

import pytest


@pytest.mark.skipif(
    importlib.util.find_spec("openai_agents") is None,
    reason="openai_agents not installed",
)
def test_governance_bridge_help() -> None:
    """Verify the console script prints usage information."""
    result = subprocess.run(
        ["governance-bridge", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()
