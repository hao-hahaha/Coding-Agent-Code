import asyncio
import sys
import types
import unittest
from unittest.mock import patch

# Provide a dummy google_adk module so adk_bridge imports succeed
_dummy = types.ModuleType("google_adk")
_dummy.Agent = object
class _Router:
    def __init__(self):
        self.app = types.SimpleNamespace(middleware=lambda *_a, **_k: lambda f: f)
    def register_agent(self, _agent):
        pass
_dummy.Router = _Router
_dummy.AgentException = Exception
sys.modules.setdefault("google_adk", _dummy)

from alpha_factory_v1.demos.alpha_agi_business_v1 import openai_agents_bridge as bridge


class DummyResponse:
    def __init__(self, payload=None, text="ok", status_code=200):
        self._payload = payload
        self.text = text
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http error")


class TestBusinessAgentIntegration(unittest.TestCase):
    def test_list_agents(self):
        agent = bridge.BusinessAgent()
        with patch.object(bridge, "requests") as req:
            req.get.return_value = DummyResponse(["a"])
            result = asyncio.run(bridge.list_agents())
        req.get.assert_called_once_with(f"{bridge.HOST}/agents", timeout=5)
        self.assertEqual(result, ["a"])

    def test_trigger_discovery(self):
        agent = bridge.BusinessAgent()
        with patch.object(bridge, "requests") as req:
            req.post.return_value = DummyResponse()
            result = asyncio.run(bridge.trigger_discovery())
        req.post.assert_called_once_with(
            f"{bridge.HOST}/agent/alpha_discovery/trigger", timeout=5
        )
        self.assertEqual(result, "alpha_discovery queued")

    def test_submit_job(self):
        agent = bridge.BusinessAgent()
        job = {"agent": "alpha_discovery", "foo": 1}
        with patch.object(bridge, "requests") as req:
            req.post.return_value = DummyResponse()
            result = asyncio.run(bridge.submit_job(job))
        req.post.assert_called_once_with(
            f"{bridge.HOST}/agent/alpha_discovery/trigger", json=job, timeout=5
        )
        self.assertEqual(result, "job for alpha_discovery queued")

    def test_check_health(self):
        agent = bridge.BusinessAgent()
        with patch.object(bridge, "requests") as req:
            req.get.return_value = DummyResponse(text="healthy")
            result = asyncio.run(bridge.check_health())
        req.get.assert_called_once_with(f"{bridge.HOST}/healthz", timeout=5)
        self.assertEqual(result, "healthy")


if __name__ == "__main__":  # pragma: no cover - manual run
    unittest.main()
