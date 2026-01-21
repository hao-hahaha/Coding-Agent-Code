import os
import time

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("API_RATE_LIMIT", "1000")


from typing import Any, cast


def make_client() -> TestClient:
    from src.interface import api_server

    return TestClient(cast(Any, api_server.app))


def test_api_endpoints() -> None:
    client = make_client()
    headers = {"Authorization": "Bearer test-token"}

    resp = client.post(
        "/simulate",
        json={"horizon": 1, "pop_size": 2, "generations": 1},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    sim_id = data.get("id")
    assert isinstance(sim_id, str) and sim_id

    for _ in range(100):
        r = client.get(f"/results/{sim_id}", headers=headers)
        if r.status_code == 200:
            results = r.json()
            break
        time.sleep(0.05)
    else:
        raise AssertionError("Timed out waiting for results")

    assert isinstance(results, dict)
    assert "forecast" in results and isinstance(results["forecast"], list)
    assert "population" in results and isinstance(results["population"], list)

    runs = client.get("/runs", headers=headers)
    assert runs.status_code == 200
    runs_data = runs.json()
    assert isinstance(runs_data, dict)
    assert "ids" in runs_data and isinstance(runs_data["ids"], list)
    assert sim_id in runs_data["ids"]
