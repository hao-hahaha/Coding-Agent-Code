import asyncio
import types
from unittest import TestCase, mock

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging
import json
import socket
import grpc
import pytest


class TestMessageBus(TestCase):
    def test_start_without_optional_dependencies(self) -> None:
        cfg = config.Settings(bus_port=0)
        with mock.patch.object(messaging, "AIOKafkaProducer", None), mock.patch.object(messaging, "grpc", None):

            async def run() -> None:
                async with messaging.A2ABus(cfg):
                    pass

            asyncio.run(run())

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

            async def run() -> None:
                async with messaging.A2ABus(cfg) as bus:
                    env = types.SimpleNamespace(sender="a", recipient="b", payload={}, ts=0.0)

                    async def _send() -> None:
                        bus.publish("b", env)
                        await asyncio.sleep(0)

                    await _send()

            asyncio.run(run())

        self.assertEqual(events[0:2], ["k:1", "start"])
        self.assertIn("stop", events)
        sent = [e for e in events if isinstance(e, tuple)][0]
        self.assertEqual(sent[0], "b")


def _free_port() -> int:
    s = socket.socket()
    s.bind(("localhost", 0))
    port = int(s.getsockname()[1])
    s.close()
    return port


def test_publish_grpc() -> None:
    port = _free_port()
    cfg = config.Settings(bus_port=port, allow_insecure=True)
    bus = messaging.A2ABus(cfg)
    received: list[messaging.Envelope] = []

    def handler(env: messaging.Envelope) -> None:
        received.append(env)

    bus.subscribe("x", handler)

    async def run() -> None:
        async with bus:
            async with grpc.aio.insecure_channel(f"localhost:{port}") as ch:
                stub = ch.unary_unary("/bus.Bus/Send")
                await stub(b"proto_schema=1")
                payload = {
                    "sender": "a",
                    "recipient": "x",
                    "payload": {"v": 1},
                    "ts": 0.0,
                }
                await stub(json.dumps(payload).encode())
                await asyncio.sleep(0)

    asyncio.run(run())

    assert len(received) == 1
    assert received[0].payload["v"] == 1


def test_publish_kafka_disabled() -> None:
    events: list[messaging.Envelope] = []

    async def handler(env: messaging.Envelope) -> None:
        events.append(env)

    cfg = config.Settings(bus_port=0)
    with mock.patch.object(messaging, "AIOKafkaProducer", None):
        bus = messaging.A2ABus(cfg)
        bus.subscribe("x", handler)

        async def run() -> None:
            async with bus:
                env = messaging.Envelope(sender="a", recipient="x", payload={"ok": True}, ts=0.0)
                bus.publish("x", env)
                await asyncio.sleep(0)

        asyncio.run(run())

    assert len(events) == 1
    assert events[0].payload["ok"] is True


def test_new_connection_requires_handshake() -> None:
    port = _free_port()
    cfg = config.Settings(bus_port=port, allow_insecure=True)
    bus = messaging.A2ABus(cfg)
    received: list[messaging.Envelope] = []

    def handler(env: messaging.Envelope) -> None:
        received.append(env)

    bus.subscribe("x", handler)

    async def run() -> None:
        async with bus:
            # first client performs handshake and sends message
            async with grpc.aio.insecure_channel(f"localhost:{port}") as ch1:
                stub1 = ch1.unary_unary("/bus.Bus/Send")
                await stub1(b"proto_schema=1")
                payload = {
                    "sender": "a",
                    "recipient": "x",
                    "payload": {"v": 1},
                    "ts": 0.0,
                }
                await stub1(json.dumps(payload).encode())

            # second client should fail without handshake
            async with grpc.aio.insecure_channel(f"localhost:{port}") as ch2:
                stub2 = ch2.unary_unary("/bus.Bus/Send")
                payload = {
                    "sender": "b",
                    "recipient": "x",
                    "payload": {"v": 2},
                    "ts": 0.0,
                }
                with pytest.raises(grpc.aio.AioRpcError):
                    await stub2(json.dumps(payload).encode())

    asyncio.run(run())

    assert len(received) == 1
    assert received[0].payload["v"] == 1
