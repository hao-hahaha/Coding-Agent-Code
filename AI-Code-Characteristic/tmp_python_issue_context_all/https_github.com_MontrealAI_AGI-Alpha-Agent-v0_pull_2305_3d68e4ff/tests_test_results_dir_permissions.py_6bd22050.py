# SPDX-License-Identifier: Apache-2.0
"""Regression tests for results directory permissions."""

from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

os.environ.setdefault("API_RATE_LIMIT", "1000")


def test_existing_results_dir_permissions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure permissions are tightened when directory already exists."""
    path = tmp_path / "results"
    path.mkdir(mode=0o755)
    monkeypatch.setenv("SIM_RESULTS_DIR", str(path))

    from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import api_server

    api_server = importlib.reload(api_server)

    assert path.exists()
    assert (path.stat().st_mode & 0o777) == 0o700
