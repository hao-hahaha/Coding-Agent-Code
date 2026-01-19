import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("API_RATE_LIMIT", "1000")


def test_root_serves_index() -> None:
    from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import api_server

    client = TestClient(api_server.app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert '<div id="root"></div>' in resp.text
