# SPDX-License-Identifier: Apache-2.0
"""Verify old results are evicted when MAX_RESULTS is exceeded."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

pytest.importorskip("fastapi")


def test_max_results_eviction(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIM_RESULTS_DIR", str(tmp_path))
    monkeypatch.setenv("MAX_RESULTS", "2")
    from src.interface import api_server

    api = importlib.reload(api_server)

    for i in range(3):
        res = api.ResultsResponse(id=f"id{i}", forecast=[], population=None)
        api._save_result(res)

    assert len(api._simulations) == 2
    assert list(api._simulations.keys()) == ["id1", "id2"]
    assert not (tmp_path / "id0.json").exists()

