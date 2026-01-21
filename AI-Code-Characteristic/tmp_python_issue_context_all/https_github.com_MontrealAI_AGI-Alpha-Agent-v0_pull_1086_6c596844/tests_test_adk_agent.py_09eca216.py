import sys
import types
import asyncio

# Stub generated proto dependency if missing
_stub_path = "src.utils.a2a_pb2"
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

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import (
    adk_summariser_agent,
    base_agent,
)
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


def test_adk_summariser_runs(monkeypatch) -> None:
    calls: list[str] = []

    class StubADK:
        def __init__(self) -> None:
            pass

        @classmethod
        def is_available(cls) -> bool:
            return True

        def generate_text(self, prompt: str) -> str:
            calls.append(prompt)
            return "sum"

    monkeypatch.setattr(base_agent, "ADKAdapter", StubADK)

    settings = config.Settings(bus_port=0)
    bus = DummyBus(settings)
    agent = adk_summariser_agent.ADKSummariserAgent(bus, DummyLedger())

    env = messaging.Envelope("research", "summariser", {"research": "r"}, 0.0)
    asyncio.run(agent.handle(env))
    asyncio.run(agent.run_cycle())

    assert calls == ["r"]
    assert bus.published
    topic, sent = bus.published[-1]
    assert topic == "strategy"
    assert sent.payload["summary"] == "sum"
