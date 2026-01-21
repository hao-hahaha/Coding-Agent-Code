import unittest
import time
from types import SimpleNamespace

from alpha_factory_v1.backend.orchestrator import _build_rest

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - allow unittest fallback
    TestClient = None  # type: ignore


class DummyRunner:
    def __init__(self):
        self.next_ts = 0
        self.period = 1
        self.last_beat = time.time()
        self.inst = SimpleNamespace()
        self.spec = None


@unittest.skipIf(TestClient is None, "fastapi not installed")
class BuildRestTest(unittest.TestCase):
    def test_basic_routes(self):
        runners = {"foo": DummyRunner()}
        app = _build_rest(runners)
        self.assertIsNotNone(app)
        client = TestClient(app)
        resp = client.get("/agents")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), ["foo"])

        resp = client.post("/agent/foo/trigger")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("queued"))
