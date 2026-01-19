# SPDX-License-Identifier: Apache-2.0
"""Offline mode test for the governance bridge."""

import builtins
import subprocess
import sys

import pytest


def test_governance_bridge_offline(monkeypatch):
    orig_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "openai_agents":
            raise ModuleNotFoundError(name)
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alpha_factory_v1.demos.solving_agi_governance.openai_agents_bridge",
            "-N",
            "10",
            "-r",
            "20",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "mean cooperation" in result.stdout.lower()
