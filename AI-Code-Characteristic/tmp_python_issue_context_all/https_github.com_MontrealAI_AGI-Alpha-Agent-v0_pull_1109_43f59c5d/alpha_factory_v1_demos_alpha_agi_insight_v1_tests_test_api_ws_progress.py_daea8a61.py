# SPDX-License-Identifier: Apache-2.0
"""WebSocket progress endpoint tests."""
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

# Ensure repository root is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("API_RATE_LIMIT", "1000")


def test_ws_progress_receives_updates() -> None:
    """A POST to /simulate should emit progress events over the WebSocket."""
    from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import api_server

    client = TestClient(api_server.app)
    headers = {"Authorization": "Bearer test-token"}

    with client.websocket_connect("/ws/progress", headers=headers) as ws:
        resp = client.post(
            "/simulate",
            json={"horizon": 1, "pop_size": 2, "generations": 1, "k": 5.0, "x0": 0.0},
            headers=headers,
        )
        assert resp.status_code == 200
        sim_id = resp.json()["id"]

        data = ws.receive_json()
        assert data["id"] == sim_id
        assert data["year"] == 1
        assert isinstance(data["capability"], float)
    # WebSocket context manager closes connection without exception
