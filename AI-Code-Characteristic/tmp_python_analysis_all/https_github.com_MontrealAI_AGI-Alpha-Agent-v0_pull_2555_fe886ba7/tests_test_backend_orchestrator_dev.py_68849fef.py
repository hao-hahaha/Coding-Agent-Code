# SPDX-License-Identifier: Apache-2.0
"""Integration test for backend orchestrator dev mode."""

from __future__ import annotations

import asyncio
import contextlib
import time

import pytest

try:
    from fastapi.testclient import TestClient  # noqa: E402
except ModuleNotFoundError:  # pragma: no cover - optional dep
    pytest.skip("fastapi required for REST API", allow_module_level=True)

from alpha_factory_v1.backend import orchestrator as orch_mod
from alpha_factory_v1.backend.api_server import build_rest
from alpha_factory_v1.backend.agents import (
    AGENT_REGISTRY,
    StubAgent,
    start_background_tasks,
    stop_background_tasks,
)
from alpha_factory_v1.backend.agents.base import AgentBase


class DummyAgent(AgentBase):  # type: ignore[misc]
    NAME = "dummy"
    CYCLE_SECONDS = 0.0

    async def step(self) -> None:  # pragma: no cover - simple agent
        return None


class FailingAgent(AgentBase):  # type: ignore[misc]
    NAME = "fail"
    CYCLE_SECONDS = 0.0

    async def step(self) -> None:  # pragma: no cover - test failure
        raise RuntimeError("boom")


@pytest.fixture()  # type: ignore[misc]
async def dev_orchestrator(monkeypatch: pytest.MonkeyPatch) -> orch_mod.Orchestrator:
    monkeypatch.setenv("DEV_MODE", "true")
    monkeypatch.setenv("API_TOKEN", "test-token")
    monkeypatch.setenv("AGENT_ERR_THRESHOLD", "1")

    from alpha_factory_v1.backend.agents import _HEALTH_Q
    import inspect
    import time

    def list_agents(_detail: bool = False) -> list[str]:  # noqa: D401
        return ["dummy", "fail"]

    def get_agent(name: str) -> object:  # noqa: D401
        agent = DummyAgent() if name == "dummy" else FailingAgent()

        if hasattr(agent, "step") and inspect.iscoroutinefunction(agent.step):
            orig = agent.step

            async def _wrapped(*a: object, **kw: object) -> object:
                t0 = time.perf_counter()
                ok = True
                try:
                    return await orig(*a, **kw)
                except Exception:
                    ok = False
                    raise
                finally:
                    _HEALTH_Q.put((name, (time.perf_counter() - t0) * 1000, ok))

            agent.step = _wrapped
        return agent

    monkeypatch.setattr("alpha_factory_v1.backend.agents.list_agents", list_agents)
    monkeypatch.setattr("alpha_factory_v1.backend.agents.get_agent", get_agent)
    monkeypatch.setattr("alpha_factory_v1.backend.agent_runner.get_agent", get_agent)
    await start_background_tasks()

    orch = orch_mod.Orchestrator()
    yield orch
    await stop_background_tasks()


def _mem_stub() -> object:
    vec = type("Vec", (), {"recent": lambda *a, **k: [], "search": lambda *a, **k: []})()
    return type("Mem", (), {"vector": vec})()


@pytest.mark.asyncio  # type: ignore[misc]
async def test_rest_and_quarantine(dev_orchestrator: orch_mod.Orchestrator) -> None:
    app = build_rest(dev_orchestrator.manager.runners, 1024 * 1024, _mem_stub())
    assert app is not None
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-token"}

    resp = client.get("/agents", headers=headers)
    assert resp.status_code == 200
    assert set(resp.json()) == {"dummy", "fail"}

    runner = dev_orchestrator.manager.runners["fail"]
    await runner.maybe_step()
    if runner.task:
        with contextlib.suppress(Exception):
            await runner.task
    await asyncio.sleep(0.05)
    time.sleep(0.05)  # allow health thread to process

    assert AGENT_REGISTRY["fail"].cls is StubAgent
