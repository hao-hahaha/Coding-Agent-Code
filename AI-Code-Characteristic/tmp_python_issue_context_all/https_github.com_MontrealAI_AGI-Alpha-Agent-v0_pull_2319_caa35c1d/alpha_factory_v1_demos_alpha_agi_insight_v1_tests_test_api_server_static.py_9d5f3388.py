# SPDX-License-Identifier: Apache-2.0
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
os.environ.setdefault("API_RATE_LIMIT", "1000")


def test_root_serves_index(monkeypatch: pytest.MonkeyPatch) -> None:
    from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import api_server

    monkeypatch.setenv("API_TOKEN", "secret")
    client = TestClient(api_server.app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert '<div id="root"></div>' in resp.text


def test_problem_json_404(monkeypatch: pytest.MonkeyPatch) -> None:
    from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import api_server

    monkeypatch.setenv("API_TOKEN", "secret")
    client = TestClient(api_server.app)
    headers = {"Authorization": "Bearer secret"}
    resp = client.get("/results/missing", headers=headers)
    assert resp.status_code == 404
    data = resp.json()
    assert data.get("type") == "about:blank"
    assert data.get("status") == 404
    assert "title" in data
