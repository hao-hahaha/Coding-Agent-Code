# SPDX-License-Identifier: Apache-2.0
"""Kafka event bus wrapper."""

from __future__ import annotations

from typing import Any, Dict

from ..agent_runner import EventBus


class KafkaService:
    """Provide a Kafka-backed event bus if available."""

    def __init__(self, broker: str | None, dev_mode: bool) -> None:
        self._bus = EventBus(broker, dev_mode)

    async def start(self) -> None:  # pragma: no cover - no async setup
        return None

    async def stop(self) -> None:  # pragma: no cover - close handled by EventBus
        return None

    def publish(self, topic: str, msg: Dict[str, Any]) -> None:
        self._bus.publish(topic, msg)

    @property
    def bus(self) -> EventBus:
        return self._bus
