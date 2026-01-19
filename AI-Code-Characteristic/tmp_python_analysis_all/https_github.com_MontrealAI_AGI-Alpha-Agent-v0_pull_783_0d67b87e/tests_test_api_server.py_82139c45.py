import asyncio
import importlib
import sys
import types
import pytest
from httpx import AsyncClient, ASGITransport

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

class DummyOrch:
    async def run_forever(self) -> None:
        await asyncio.Event().wait()

async def make_client(monkeypatch: pytest.MonkeyPatch):
    from src.interface import api_server

    dummy_mod = types.ModuleType(
        "alpha_factory_v1.demos.alpha_agi_insight_v1.src.orchestrator"
    )
    dummy_mod.Orchestrator = lambda: DummyOrch()
    monkeypatch.setitem(sys.modules, dummy_mod.__name__, dummy_mod)
    await api_server.app.router.startup()
    client = AsyncClient(base_url="http://test", transport=ASGITransport(app=api_server.app))
    return client, api_server

def test_simulate_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    async def run() -> None:
        client, api_server = await make_client(monkeypatch)
        async with client:
            r = await client.post("/simulate", json={"horizon": 1, "pop_size": 2, "generations": 1})
            assert r.status_code == 200
            sim_id = r.json()["id"]
            for _ in range(50):
                if sim_id in api_server._simulations:
                    break
                await asyncio.sleep(0.05)
            r = await client.get(f"/results/{sim_id}")
            assert r.status_code == 200
            data = r.json()
            assert "forecast" in data
        await api_server.app.router.shutdown()

    asyncio.run(run())
