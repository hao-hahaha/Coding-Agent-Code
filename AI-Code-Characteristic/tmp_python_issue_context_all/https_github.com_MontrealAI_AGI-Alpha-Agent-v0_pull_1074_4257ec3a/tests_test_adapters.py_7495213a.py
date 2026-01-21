# SPDX-License-Identifier: Apache-2.0

import sys
import types
import asyncio
import pytest

# Stub generated proto dependency if missing
_stub_path = "alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.a2a_pb2"
if _stub_path not in sys.modules:
    stub = types.ModuleType("a2a_pb2")
    class Envelope:
        def __init__(self, sender: str = "", recipient: str = "", payload: dict | None = None, ts: float = 0.0) -> None:
            self.sender = sender
            self.recipient = recipient
            self.payload = payload or {}
            self.ts = ts
    stub.Envelope = Envelope
    sys.modules[_stub_path] = stub

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents.adk_adapter import ADKAdapter  # noqa: E402
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents.mcp_adapter import MCPAdapter  # noqa: E402


@pytest.mark.skipif(not ADKAdapter.is_available(), reason="ADK not installed")
def test_adk_list_packages():
    adapter = ADKAdapter()
    pkgs = adapter.list_packages()
    assert isinstance(pkgs, list)

@pytest.mark.skipif(not MCPAdapter.is_available(), reason="MCP not installed")
def test_mcp_invoke_tool_missing():
    async def _run() -> None:
        adapter = MCPAdapter()
        with pytest.raises(KeyError):
            await adapter.invoke_tool("missing_tool", {})

    asyncio.run(_run())


def _make_agent(monkeypatch):
    """Return a ResearchAgent wired with dummy bus/ledger."""
    from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import research_agent
    from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging

    class DummyBus:
        def __init__(self, settings: config.Settings) -> None:
            self.settings = settings
            self.published: list[tuple[str, messaging.Envelope]] = []

        def publish(self, topic: str, env: messaging.Envelope) -> None:
            self.published.append((topic, env))

        def subscribe(self, _t: str, _h):
            pass

    class DummyLedger:
        def __init__(self) -> None:
            self.logged: list[messaging.Envelope] = []

        def log(self, env: messaging.Envelope) -> None:  # type: ignore[override]
            self.logged.append(env)

        def start_merkle_task(self, *_a, **_kw):
            pass

        async def stop_merkle_task(self) -> None:  # pragma: no cover - interface
            pass

        def close(self) -> None:
            pass

    settings = config.Settings(bus_port=0)
    bus = DummyBus(settings)
    agent = research_agent.ResearchAgent(bus, DummyLedger())
    return agent, bus


def test_adk_generate_text_flow(monkeypatch) -> None:
    agent, bus = _make_agent(monkeypatch)

    class StubADK:
        def __init__(self) -> None:
            self.called: list[str] = []

        def generate_text(self, prompt: str) -> str:
            self.called.append(prompt)
            return "reply"

    adk = StubADK()
    monkeypatch.setattr(agent, "adk", adk, raising=False)

    async def patched_handle(self, env):
        text = self.adk.generate_text(env.payload.get("plan", ""))
        await self.emit("strategy", {"research": text})

    monkeypatch.setattr(type(agent), "handle", patched_handle)
    from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import messaging

    env = messaging.Envelope("planning", "research", {"plan": "p"}, 0.0)
    asyncio.run(agent.handle(env))

    assert adk.called == ["p"]
    assert bus.published and bus.published[-1][1].payload["research"] == "reply"


def test_mcp_invoke_tool_flow(monkeypatch) -> None:
    agent, bus = _make_agent(monkeypatch)

    class StubMCP:
        def __init__(self) -> None:
            self.called: list[tuple[str, dict[str, object]]] = []

        async def invoke_tool(self, name: str, args: dict[str, object] | None = None) -> object:
            args = args or {}
            self.called.append((name, args))
            return {"ok": True}

    mcp = StubMCP()
    monkeypatch.setattr(agent, "mcp", mcp, raising=False)

    async def patched_run_cycle(self) -> None:
        res = await self.mcp.invoke_tool("echo", {"t": 1})
        await self.emit("strategy", res)

    monkeypatch.setattr(type(agent), "run_cycle", patched_run_cycle)

    asyncio.run(agent.run_cycle())

    assert mcp.called == [("echo", {"t": 1})]
    assert bus.published and bus.published[-1][1].payload == {"ok": True}

