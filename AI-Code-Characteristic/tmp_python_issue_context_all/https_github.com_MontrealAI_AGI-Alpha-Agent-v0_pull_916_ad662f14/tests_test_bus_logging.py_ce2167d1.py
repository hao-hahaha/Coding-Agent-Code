import asyncio
import logging
from unittest import mock

import pytest

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging


def test_bus_logs_start_stop(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    cfg = config.Settings(bus_port=1234, broker_url="kafka:9092")
    bus = messaging.A2ABus(cfg)
    with mock.patch.object(messaging, "AIOKafkaProducer", None), \
         mock.patch.object(messaging, "grpc", None):
        asyncio.run(bus.start())
        asyncio.run(bus.stop())
    messages = [r.message for r in caplog.records]
    assert any("Starting A2ABus" in m and "1234" in m and "kafka:9092" in m for m in messages)
    assert any("Stopping A2ABus" in m for m in messages)
