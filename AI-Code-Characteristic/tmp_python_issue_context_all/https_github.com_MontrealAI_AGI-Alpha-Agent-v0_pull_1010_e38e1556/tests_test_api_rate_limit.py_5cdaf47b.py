# SPDX-License-Identifier: Apache-2.0

import importlib
import os
from typing import Any, cast

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("API_RATE_LIMIT", "1000")


def test_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_RATE_LIMIT", "2")
    from src.interface import api_server as api
    api = importlib.reload(api)
    client = TestClient(cast(Any, api.app))
    headers = {"Authorization": "Bearer test-token"}

    assert client.get("/runs", headers=headers).status_code == 200
    assert client.get("/runs", headers=headers).status_code == 200
    resp = client.get("/runs", headers=headers)
    assert resp.status_code == 429
