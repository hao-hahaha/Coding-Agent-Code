import asyncio
import json
import os
import tempfile
import unittest

from alpha_factory_v1.demos.alpha_agi_insight_v1.src import orchestrator
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging


class TestInsightOrchestrator(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = config.Settings(bus_port=0, ledger_path=os.path.join(self.tmp.name, "ledger.db"))
        self.orch = orchestrator.Orchestrator(self.settings)

    def tearDown(self) -> None:
        asyncio.run(self.orch.bus.stop())
        asyncio.run(self.orch.ledger.stop_merkle_task())
        self.orch.ledger.close()
        self.tmp.cleanup()

    def test_registration_records(self) -> None:
        count = self.orch.ledger.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        self.assertEqual(count, len(self.orch.runners))


class TestMessaging(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = config.Settings(bus_port=0)
        self.bus = messaging.A2ABus(self.settings)

    def tearDown(self) -> None:
        asyncio.run(self.bus.stop())

    def test_publish_subscribe(self) -> None:
        received = []

        async def handler(env: messaging.Envelope) -> None:
            received.append(env)

        self.bus.subscribe("x", handler)
        env = messaging.Envelope("a", "x", {"v": 1}, 0.0)
        self.bus.publish("x", env)
        asyncio.run(asyncio.sleep(0.01))
        self.assertEqual(received[0].payload["v"], 1)

    def test_rpc_auth(self) -> None:
        self.settings.bus_token = "s3cr3t"
        bus = messaging.A2ABus(self.settings)

        class Ctx:
            def abort(self, *_a, **_kw):
                raise RuntimeError("denied")

        payload = {
            "sender": "a",
            "recipient": "b",
            "payload": {},
            "ts": 0.0,
            "token": "s3cr3t",
        }
        asyncio.run(bus._handle_rpc(json.dumps(payload).encode(), Ctx()))


class TestLedger(unittest.TestCase):
    def test_merkle_task(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        led = orchestrator.Ledger(os.path.join(tmp.name, "l.db"))
        env = messaging.Envelope("a", "b", {}, 0.0)
        led.log(env)
        asyncio.run(led.broadcast_merkle_root())
        led.start_merkle_task(0.1)
        asyncio.run(asyncio.sleep(0.2))
        asyncio.run(led.stop_merkle_task())
        tmp.cleanup()


if __name__ == "__main__":  # pragma: no cover - manual
    unittest.main()
