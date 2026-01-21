import asyncio
import types
import pytest

from alpha_factory_v1.backend.agents import biotech_agent


class StubClient:
    def __init__(self):
        self.calls = 0
        self.node_id = "X"

    async def register(self, *_, **__):
        self.calls += 1
        if self.calls < 3:
            raise biotech_agent.AdkClientError("boom")


async def no_sleep(_: float) -> None:
    return None


def test_register_mesh_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    client = StubClient()
    fake_adk = types.SimpleNamespace(Client=lambda: client)
    monkeypatch.setattr(biotech_agent, "adk", fake_adk)
    monkeypatch.setattr(asyncio, "sleep", no_sleep)

    agent = biotech_agent.BiotechAgent()
    asyncio.run(agent._register_mesh())
    assert client.calls == 3


def test_register_mesh_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailClient(StubClient):
        async def register(self, *_, **__):
            self.calls += 1
            raise biotech_agent.AdkClientError("boom")

    client = FailClient()
    fake_adk = types.SimpleNamespace(Client=lambda: client)
    monkeypatch.setattr(biotech_agent, "adk", fake_adk)
    monkeypatch.setattr(asyncio, "sleep", no_sleep)

    agent = biotech_agent.BiotechAgent()
    with pytest.raises(biotech_agent.AdkClientError):
        asyncio.run(agent._register_mesh())
    assert client.calls == 3
