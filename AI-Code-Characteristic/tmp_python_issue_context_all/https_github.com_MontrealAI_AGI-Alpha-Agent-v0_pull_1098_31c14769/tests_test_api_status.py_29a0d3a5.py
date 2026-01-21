# SPDX-License-Identifier: Apache-2.0
"""Verify the /status endpoint and CLI output."""

import importlib
import os
from typing import Any, cast
from unittest.mock import patch

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from click.testing import CliRunner

os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("API_RATE_LIMIT", "1000")


def _make_client() -> TestClient:
    from src.interface import api_server

    api_server = importlib.reload(api_server)
    return TestClient(cast(Any, api_server.app))


def test_status_endpoint() -> None:
    client = _make_client()
    headers = {"Authorization": "Bearer test-token"}
    resp = client.get("/status", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("agents")


def test_cli_agents_status_parses_mapping() -> None:
    from src.interface import cli

    payload = {"agents": {"agent1": {"last_beat": 1.0, "restarts": 0}}}

    class Dummy:
        status_code = 200

        def json(self) -> dict:
            return payload

    with patch.object(cli.requests, "get", return_value=Dummy()):
        result = CliRunner().invoke(cli.main, ["agents-status"])
    assert "agent1" in result.output
