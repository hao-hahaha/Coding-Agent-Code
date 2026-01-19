import asyncio
from types import SimpleNamespace

import pytest

from alpha_factory_v1.backend.services.api_server_service import APIServer


@pytest.mark.asyncio
async def test_api_server_start_stop(monkeypatch):
    events = []

    async def fake_start_servers(*a, **k):
        events.append("start")

        async def sleeper():
            await asyncio.sleep(0)
        task = asyncio.create_task(sleeper())
        server = SimpleNamespace(stop=lambda code=0: events.append("stop"))
        return task, server

    monkeypatch.setattr(
        "alpha_factory_v1.backend.services.api_server_service.start_servers",
        fake_start_servers,
    )

    srv = APIServer({}, 1, object(), 0, 0, "INFO", True)
    await srv.start()
    assert events == ["start"]
    await srv.stop()
    assert events[-1] == "stop"
