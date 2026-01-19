# SPDX-License-Identifier: Apache-2.0
"""Integration test ensuring blocked messages are not stored."""

from __future__ import annotations

import asyncio

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import (
    chaos_agent,
    memory_agent,
    safety_agent,
)
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import (
    config,
    logging,
    messaging,
)


class CaptureBus(messaging.A2ABus):
    """A2ABus that records published envelopes."""

    def __init__(self, settings: config.Settings) -> None:
        super().__init__(settings)
        self.published: list[tuple[str, messaging.Envelope]] = []

    def publish(self, topic: str, env: messaging.Envelope) -> None:  # type: ignore[override]
        self.published.append((topic, env))
        super().publish(topic, env)


class FilteringMemoryAgent(memory_agent.MemoryAgent):
    """MemoryAgent variant that ignores blocked payloads."""

    async def handle(self, env: messaging.Envelope) -> None:  # type: ignore[override]
        if env.payload.get("status") == "blocked":
            return
        await super().handle(env)


def test_blocked_payload_not_stored(tmp_path) -> None:
    """ChaosAgent payloads should be blocked and skipped by the memory."""

    cfg = config.Settings(bus_port=0)
    bus = CaptureBus(cfg)
    ledger = logging.Ledger(str(tmp_path / "ledger.db"), broadcast=False)

    mem = FilteringMemoryAgent(bus, ledger, str(tmp_path / "mem.log"))
    guardian = safety_agent.SafetyGuardianAgent(bus, ledger)  # noqa: F841  # needed to register handler
    chaos = chaos_agent.ChaosAgent(bus, ledger, burst=1)

    async def run() -> None:
        async with bus, ledger:
            await chaos.run_cycle()
            await asyncio.sleep(0)

    asyncio.run(run())

    memory_events = [env for topic, env in bus.published if topic == "memory"]
    assert memory_events
    assert memory_events[-1].payload["status"] == "blocked"
    assert mem.records == []
