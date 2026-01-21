# SPDX-License-Identifier: Apache-2.0
"""Basic pub/sub behavior for :class:`A2ABus`."""

from __future__ import annotations

import asyncio

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging


def test_publish_to_async_subscriber() -> None:
    """Envelopes published to a subscribed coroutine should be delivered."""
    bus = messaging.A2ABus(config.Settings(bus_port=0))
    received: list[messaging.Envelope] = []

    async def handler(env: messaging.Envelope) -> None:
        received.append(env)

    bus.subscribe("x", handler)
    env = messaging.Envelope("a", "x", {"v": 42}, 0.0)

    async def run() -> None:
        bus.publish("x", env)
        await asyncio.sleep(0)  # allow handler task to run

    asyncio.run(run())
    assert len(received) == 1
    assert received[0].payload["v"] == 42
