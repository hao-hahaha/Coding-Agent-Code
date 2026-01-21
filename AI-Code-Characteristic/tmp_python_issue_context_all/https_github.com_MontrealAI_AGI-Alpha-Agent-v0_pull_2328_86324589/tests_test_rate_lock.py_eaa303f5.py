# SPDX-License-Identifier: Apache-2.0
import asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from typing import Any

import sys
import types

stub = types.ModuleType("stub_agents")


class DummyRuntime:
    def __init__(self, *a, **k):
        pass

    def register(self, *a, **k):
        pass


class DummyOA:
    def __init__(self, *a, **k):
        pass

    async def __call__(self, _t):
        return "ok"


stub.Agent = object
stub.AgentRuntime = DummyRuntime
stub.OpenAIAgent = DummyOA
stub.Tool = lambda *a, **k: (lambda f: f)

sys.modules.setdefault("openai_agents", stub)
sys.modules.setdefault("agents", stub)
a2a_mod = sys.modules.setdefault("a2a", types.ModuleType("a2a"))
a2a_mod.A2ASocket = lambda *a, **k: None
gr_mod = sys.modules.setdefault("gradio", types.ModuleType("gradio"))
gr_mod.Blocks = lambda *a, **k: types.SimpleNamespace(__enter__=lambda s: s, __exit__=lambda *e: None)

from alpha_factory_v1.demos.aiga_meta_evolution import agent_aiga_entrypoint as mod


async def _make_client() -> tuple[AsyncClient, Any]:
    app = FastAPI()
    app.middleware("http")(mod._count_requests)

    @app.get("/")
    async def root():
        return {"ok": True}

    transport = ASGITransport(app=app)
    client = AsyncClient(base_url="http://test", transport=transport)
    return client, app


async def _run_concurrent() -> None:
    client, _ = await _make_client()
    async with client:
        await asyncio.gather(*[client.get("/") for _ in range(5)])


def test_concurrent_requests(monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "1000")
    mod._REQUEST_LOG.clear()
    asyncio.run(_run_concurrent())
    assert len(mod._REQUEST_LOG.get("127.0.0.1", [])) == 5
