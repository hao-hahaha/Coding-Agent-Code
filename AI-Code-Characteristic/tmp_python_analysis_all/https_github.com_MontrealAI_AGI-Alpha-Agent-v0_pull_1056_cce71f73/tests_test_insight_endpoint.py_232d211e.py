import os
from typing import Any, cast

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("API_RATE_LIMIT", "1000")

from src.interface import api_server as api


def _make_client() -> TestClient:
    return TestClient(cast(Any, api.app))


def _setup_simulations() -> None:
    api._simulations.clear()
    api._simulations["a"] = api.ResultsResponse(
        id="a",
        forecast=[api.ForecastPoint(year=1, capability=0.1)],
        population=None,
    )
    api._simulations["b"] = api.ResultsResponse(
        id="b",
        forecast=[api.ForecastPoint(year=1, capability=0.9)],
        population=None,
    )


def test_insight_aggregates_results() -> None:
    _setup_simulations()
    client = _make_client()
    headers = {"Authorization": "Bearer test-token"}
    resp = client.post("/insight", json={"ids": ["a", "b"]}, headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"forecast": [{"year": 1, "capability": 0.5}]}


def test_insight_invalid_token() -> None:
    _setup_simulations()
    client = _make_client()
    resp = client.post("/insight", json={}, headers={"Authorization": "Bearer bad"})
    assert resp.status_code == 403


def test_insight_missing_ids() -> None:
    _setup_simulations()
    client = _make_client()
    headers = {"Authorization": "Bearer test-token"}
    resp = client.post("/insight", json={"ids": ["missing"]}, headers=headers)
    assert resp.status_code == 404
