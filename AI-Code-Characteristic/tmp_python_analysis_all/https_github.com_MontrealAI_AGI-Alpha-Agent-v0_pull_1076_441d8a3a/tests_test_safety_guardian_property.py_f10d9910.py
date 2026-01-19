# SPDX-License-Identifier: Apache-2.0
"""Property-based tests for SafetyGuardianAgent."""

from __future__ import annotations

import asyncio
import sys
import types

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import assume, given, settings, strategies as st

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import safety_agent
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging

_STUB = "alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.a2a_pb2"
if _STUB not in sys.modules:
    stub = types.ModuleType("a2a_pb2")

    from dataclasses import dataclass

    @dataclass
    class Envelope:
        sender: str = ""
        recipient: str = ""
        payload: dict[str, object] | None = None
        ts: float = 0.0

    stub.Envelope = Envelope
    sys.modules[_STUB] = stub


class DummyBus:
    def __init__(self, settings: config.Settings) -> None:
        self.settings = settings
        self.published: list[tuple[str, messaging.Envelope]] = []

    def publish(self, topic: str, env: messaging.Envelope) -> None:
        self.published.append((topic, env))

    def subscribe(self, topic: str, handler) -> None:  # pragma: no cover - dummy
        pass


class DummyLedger:
    def __init__(self) -> None:
        self.logged: list[messaging.Envelope] = []

    def log(self, env: messaging.Envelope) -> None:  # type: ignore[override]
        self.logged.append(env)

    def start_merkle_task(self, *a, **kw) -> None:  # pragma: no cover - dummy
        pass

    async def stop_merkle_task(self) -> None:  # pragma: no cover - interface
        pass

    def close(self) -> None:  # pragma: no cover - dummy
        pass


@settings(max_examples=30)
@given(code=st.text(min_size=0, max_size=100))
def test_blocks_import_os(code: str) -> None:
    assume("import os" in code)
    bus = DummyBus(config.Settings(bus_port=0))
    led = DummyLedger()
    agent = safety_agent.SafetyGuardianAgent(bus, led)
    env = messaging.Envelope("codegen", "safety", {"code": code}, 0.0)
    asyncio.run(agent.handle(env))
    assert bus.published[-1][1].payload["status"] == "blocked"


@settings(max_examples=30)
@given(code=st.text(min_size=0, max_size=100))
def test_allows_safe_code(code: str) -> None:
    assume("import os" not in code)
    bus = DummyBus(config.Settings(bus_port=0))
    led = DummyLedger()
    agent = safety_agent.SafetyGuardianAgent(bus, led)
    env = messaging.Envelope("codegen", "safety", {"code": code}, 0.0)
    asyncio.run(agent.handle(env))
    assert bus.published[-1][1].payload["status"] == "ok"
