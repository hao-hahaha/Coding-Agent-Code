# SPDX-License-Identifier: Apache-2.0
"""Unit test for agent_aiga_entrypoint FastAPI service."""

from typing import Any, cast

import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.mark.usefixtures("non_network")
def test_health_endpoint() -> None:
    """Verify /health returns expected metrics."""
    module = importlib.import_module("alpha_factory_v1.demos.aiga_meta_evolution.agent_aiga_entrypoint")
    client = TestClient(cast(Any, module.app))

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data) >= {"status", "generations", "best_fitness"}
