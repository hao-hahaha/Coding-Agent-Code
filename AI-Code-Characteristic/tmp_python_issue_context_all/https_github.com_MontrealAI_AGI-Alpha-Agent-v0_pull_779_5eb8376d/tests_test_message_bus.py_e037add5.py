import asyncio
import types
from unittest import TestCase, mock

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging


class TestMessageBus(TestCase):
    def test_start_without_optional_dependencies(self) -> None:
        cfg = config.Settings(bus_port=0)
        with mock.patch.object(messaging, "AIOKafkaProducer", None), \
             mock.patch.object(messaging, "grpc", None):
            bus = messaging.A2ABus(cfg)
            asyncio.run(bus.start())
            asyncio.run(bus.stop())

    def test_kafka_publish(self) -> None:
        events: list[object] = []

        class Prod:
            def __init__(self, bootstrap_servers: str) -> None:
                events.append(bootstrap_servers)

            async def start(self) -> None:
                events.append("start")

            async def send_and_wait(self, topic: str, data: bytes) -> None:
                events.append((topic, data))

            async def stop(self) -> None:
                events.append("stop")

        cfg = config.Settings(bus_port=0, broker_url="k:1")
        with mock.patch.object(messaging, "AIOKafkaProducer", Prod):
            bus = messaging.A2ABus(cfg)
            asyncio.run(bus.start())
            env = types.SimpleNamespace(sender="a", recipient="b", payload={}, ts=0.0)

            async def _send() -> None:
                bus.publish("b", env)
                await asyncio.sleep(0)

            asyncio.run(_send())
            asyncio.run(bus.stop())

        self.assertEqual(events[0:2], ["k:1", "start"])
        self.assertIn("stop", events)
        sent = [e for e in events if isinstance(e, tuple)][0]
        self.assertEqual(sent[0], "b")
