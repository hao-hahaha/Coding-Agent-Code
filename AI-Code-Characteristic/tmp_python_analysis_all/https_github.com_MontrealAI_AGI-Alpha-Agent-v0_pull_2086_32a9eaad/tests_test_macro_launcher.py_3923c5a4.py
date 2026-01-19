# SPDX-License-Identifier: Apache-2.0
"""Tests for the Macro-Sentinel Docker launcher."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(
    "alpha_factory_v1/demos/macro_sentinel/macro_launcher.py"
)


@pytest.mark.skipif(
    not SCRIPT.exists(), reason="script missing"
)
def test_macro_launcher_no_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """`OPENAI_API_KEY` disables the offline profile."""
    compose_calls: list[list[str]] = []

    def fake_run(cmd: list[str], *a, **k) -> subprocess.CompletedProcess[str]:
        if cmd[:2] == ["docker", "compose"]:
            compose_calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")

    mod = __import__(
        "alpha_factory_v1.demos.macro_sentinel.macro_launcher", fromlist=["main"]
    )
    mod.main([])

    cmd_str = " ".join(" ".join(c) for c in compose_calls)
    assert "--profile offline" not in cmd_str


@pytest.mark.skipif(
    not SCRIPT.exists(), reason="script missing"
)
def test_macro_launcher_health_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Health gate should hit the expected endpoint."""
    curl_calls: list[list[str]] = []

    def fake_run(cmd: list[str], *a, **k) -> subprocess.CompletedProcess[str]:
        if cmd[0] == "curl":
            curl_calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")

    mod = __import__(
        "alpha_factory_v1.demos.macro_sentinel.macro_launcher", fromlist=["main"]
    )
    mod.main([])

    urls = " ".join(" ".join(c) for c in curl_calls)
    assert "http://localhost:7864/healthz" in urls
