from __future__ import annotations

import asyncio
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import chaos_agent, safety_agent
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging
from google.protobuf import struct_pb2

if not hasattr(struct_pb2.Struct, "get"):
    def _get(self: struct_pb2.Struct, key: str, default=None):
        try:
            return self[key]
        except Exception:
            return default

    struct_pb2.Struct.get = _get  # type: ignore[attr-defined]


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


def test_safety_blocks_chaos() -> None:
    cfg = config.Settings(bus_port=0)
    bus = DummyBus(cfg)
    led = DummyLedger()
    chaos = chaos_agent.ChaosAgent(bus, led, burst=20)
    guardian = safety_agent.SafetyGuardianAgent(bus, led)

    asyncio.run(chaos.run_cycle())
    chaos_msgs = [env for topic, env in bus.published if topic == "safety"]

    blocked = 0
    for env in chaos_msgs:
        asyncio.run(guardian.handle(env))
        if bus.published[-1][1].payload["status"] == "blocked":
            blocked += 1

    assert chaos_msgs
    assert blocked / len(chaos_msgs) >= 0.95


def test_cycle_emits_blocked_to_memory() -> None:
    cfg = config.Settings(bus_port=0)
    bus = DummyBus(cfg)
    led = DummyLedger()
    chaos = chaos_agent.ChaosAgent(bus, led, burst=1)
    guardian = safety_agent.SafetyGuardianAgent(bus, led)

    asyncio.run(chaos.run_cycle())
    topic, env = bus.published[0]
    assert topic == "safety"

    asyncio.run(guardian.handle(env))
    assert bus.published[-1][0] == "memory"
    assert bus.published[-1][1].payload["status"] == "blocked"
