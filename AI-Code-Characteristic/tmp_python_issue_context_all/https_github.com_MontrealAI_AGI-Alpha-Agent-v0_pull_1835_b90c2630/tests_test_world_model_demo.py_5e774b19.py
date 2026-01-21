# SPDX-License-Identifier: Apache-2.0
"""Minimal test for alpha_asi_world_model_demo FastAPI app."""

from __future__ import annotations

import importlib
import os
from typing import Any, cast

import pytest

pytest.importorskip("torch")
from fastapi.testclient import TestClient  # noqa: E402


def test_agents_list_offline(non_network: None) -> None:
    """Verify /agents lists all required demo agents."""
    os.environ["NO_LLM"] = "1"
    os.environ.setdefault("ALPHA_ASI_SILENT", "1")
    os.environ.setdefault("ALPHA_ASI_MAX_STEPS", "1")

    mod = importlib.import_module("alpha_factory_v1.demos.alpha_asi_world_model.alpha_asi_world_model_demo")
    client = TestClient(cast(Any, mod.app))

    resp = client.get("/agents")
    assert resp.status_code == 200
    agents = resp.json()
    expected = {
        "PlanningAgent",
        "ResearchAgent",
        "StrategyAgent",
        "MarketAnalysisAgent",
        "CodeGenAgent",
        "SafetyAgent",
    }
    assert expected.issubset(set(agents))
